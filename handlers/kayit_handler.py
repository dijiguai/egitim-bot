"""
Kimlik dogrulama + otomatik uye tanima
"""

import logging, datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import ADMIN_IDS, GECME_NOTU
from sheets import kayit_ekle

logger = logging.getLogger(__name__)

kullanici_durum = {}
onay_bekleyenler = {}


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return
    user_id = user.id

    # Grup butonundan gelen start parametresi: /start egitim_forklift_guvenligi
    args = context.args
    if args and args[0].startswith("egitim_"):
        egitim_id = args[0].replace("egitim_", "", 1)
        from handlers.egitim_handler import egitim_baslat
        await egitim_baslat(update, context, user_id, egitim_id)
        return

    # Normal /start
    if user_id in ADMIN_IDS:
        from handlers.admin_handler import start as admin_start
        await admin_start(update, context)
        return

    try:
        from calisanlar import calisan_bul
        calisan = calisan_bul(user_id)
    except:
        calisan = None

    if calisan:
        await update.message.reply_text(
            f"Merhaba *{calisan['ad_soyad'].split()[0]}*!\n\n"
            f"Sabah 08:00'de gunun egitimi otomatik gelir.",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "Merhaba!\n\n"
            "Gruptan gelen egitim butonuna basarak egitime katilabilirsiniz.\n"
            "Ilk katilimda dogum tarihiniz sorulacak."
        )
        await _admin_bildir(context, user)


async def metin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or user.is_bot:
        return

    user_id = user.id
    durum = kullanici_durum.get(user_id, {})

    if durum.get("dogum_dogrulama"):
        await dogum_ile_dogrula(update, context, user_id, durum)
        return

    if durum.get("kimlik_bekleniyor"):
        await kimlik_dogrula(update, context, user_id, durum)
        return

    # Grup mesaji — yeni uye tespiti
    chat = update.effective_chat
    if chat and hasattr(chat, 'type') and chat.type != "private":
        try:
            from calisanlar import calisan_bul
            if not calisan_bul(user_id) and user_id not in ADMIN_IDS:
                await _admin_bildir(context, user)
        except:
            pass


async def dogum_ile_dogrula(update, context, user_id, durum):
    from calisanlar import calisan_bul_dogum, telegram_id_guncelle
    girilen = update.message.text.strip()
    tid, calisan = calisan_bul_dogum(girilen)

    if calisan:
        telegram_id_guncelle(girilen, user_id)
        durum["dogum_dogrulama"] = False
        durum["kimlik_dogrulandi"] = True
        kullanici_durum[user_id] = durum

        from config import EGITIMLER
        from handlers.egitim_handler import soru_gonder
        egitim = EGITIMLER.get(durum["egitim_id"], {})

        await update.message.reply_text(
            f"Kimliginiz dogrulandi, *{calisan['ad_soyad'].split()[0]}*! Egitim basliyor...",
            parse_mode="Markdown"
        )
        await update.message.reply_text(egitim.get("metin", ""), parse_mode="Markdown")
        await soru_gonder(context, user_id, 0, durum["sorular"])
    else:
        durum["kimlik_deneme"] = durum.get("kimlik_deneme", 0) + 1
        if durum["kimlik_deneme"] >= 3:
            kullanici_durum.pop(user_id, None)
            await update.message.reply_text("3 yanlis deneme. Yoneticinizle iletisime gecin.")
        else:
            kalan = 3 - durum["kimlik_deneme"]
            await update.message.reply_text(
                f"Eslesme bulunamadi. {kalan} hakkiniz kaldi.\n"
                f"Dogum tarihinizi GG.AA.YYYY formatinda girin:"
            )


async def kimlik_dogrula(update, context, user_id, durum):
    from calisanlar import calisan_bul, calisan_bul_dogum
    girilen = update.message.text.strip()

    calisan = calisan_bul(user_id)
    if calisan:
        dogru = calisan.get("dogum_tarihi", "")
        eslesti = (girilen == dogru or girilen == dogru.split(".")[-1])
    else:
        _, calisan = calisan_bul_dogum(girilen)
        eslesti = calisan is not None

    if eslesti and calisan:
        durum["kimlik_bekleniyor"] = False
        durum["kimlik_dogrulandi"] = True
        kullanici_durum[user_id] = durum
        await sinav_tamamla_direkt(context, user_id, durum, calisan=calisan, guncelle=update)
    else:
        durum["kimlik_deneme"] = durum.get("kimlik_deneme", 0) + 1
        if durum["kimlik_deneme"] >= 3:
            kullanici_durum.pop(user_id, None)
            await update.message.reply_text("3 yanlis deneme. Yoneticinizle iletisime gecin.")
        else:
            await update.message.reply_text(
                f"Eslesme bulunamadi. {3 - durum['kimlik_deneme']} hakkiniz kaldi.\n"
                f"Dogum tarihinizi girin (GG.AA.YYYY):"
            )


async def sinav_tamamla_direkt(context, user_id, durum, calisan=None, guncelle=None):
    from calisanlar import calisan_bul
    from config import EGITIMLER

    if not calisan:
        calisan = calisan_bul(user_id)
    if not calisan:
        return

    egitim_id = durum.get("egitim_id")
    egitim = EGITIMLER.get(egitim_id, {})
    dogru = durum.get("dogru_sayisi", 0)
    toplam = len(durum.get("sorular", []))
    puan = round(dogru / toplam * 100) if toplam else 0
    gecti = puan >= GECME_NOTU
    simdi = datetime.datetime.now()

    try:
        kayit_ekle({
            "tarih": simdi.strftime("%d.%m.%Y"),
            "saat": simdi.strftime("%H:%M"),
            "ad_soyad": calisan["ad_soyad"],
            "telegram_id": str(user_id),
            "gorev": calisan["gorev"],
            "egitim_konusu": egitim.get("baslik", egitim_id),
            "egitim_turu": egitim.get("tur", ""),
            "puan": str(puan),
            "durum": "GECTI" if gecti else "KALDI",
            "kimlik_dogrulandi": "EVET",
            "dogum_yili": calisan.get("dogum_tarihi", "").split(".")[-1]
        })
        from durum import tamamlandi_kaydet
        if gecti:
            tamamlandi_kaydet(user_id, egitim_id)
    except Exception as e:
        logger.error(f"Kayit hatasi: {e}")

    kullanici_durum.pop(user_id, None)

    ad = calisan['ad_soyad'].split()[0]
    if gecti:
        mesaj = f"Tebrikler {ad}!\n\nEgitimi gecdiniz!\nPuaniniz: {puan}/100\n\nIyi calismalar!"
    else:
        mesaj = f"Egitim Sonucu\n\nGecemediniz.\nPuaniniz: {puan}/100 (Gecme: {GECME_NOTU})\n\nYoneticiniz sizi bilgilendirecektir."

    if guncelle:
        await guncelle.message.reply_text(mesaj)
    else:
        await context.bot.send_message(chat_id=user_id, text=mesaj)


async def _admin_bildir(context, user):
    user_id = user.id
    if user_id in onay_bekleyenler:
        return
    ad = f"{user.first_name or ''} {user.last_name or ''}".strip() or f"Kullanici {user_id}"
    username = f"@{user.username}" if user.username else ""
    onay_bekleyenler[user_id] = {"ad": ad, "username": username}

    keyboard = [[
        InlineKeyboardButton("Sisteme Ekle", callback_data=f"uye_ekle:{user_id}"),
        InlineKeyboardButton("Yoksay", callback_data=f"uye_yoksay:{user_id}")
    ]]

    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=(
                    f"Yeni uye!\n\n"
                    f"Ad: {ad}\n"
                    f"Kullanici adi: {username}\n"
                    f"Telegram ID: {user_id}\n\n"
                    f"Panelden ekleyin (ID girmek zorunda degilsiniz)."
                ),
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            logger.warning(f"Admin bildirimi: {e}")


async def uye_ekle_callback(update, context, user_id):
    bilgi = onay_bekleyenler.get(user_id, {})
    await update.callback_query.edit_message_text(
        f"Panelden ekleyin:\nAd: {bilgi.get('ad','?')}\nID: {user_id}\n\n"
        f"ID girmek zorunda degilsiniz, dogum tarihi ile eslesir."
    )


async def uye_yoksay_callback(update, context, user_id):
    bilgi = onay_bekleyenler.pop(user_id, {})
    await update.callback_query.edit_message_text(f"{bilgi.get('ad','?')} yoksayildi.")
