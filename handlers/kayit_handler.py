"""
Kimlik doğrulama + otomatik üye tanıma
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
            f"👷 Merhaba *{calisan['ad_soyad'].split()[0]}*!\n\n"
            f"Sabah 08:00'de eğitim bildirimi alacaksınız.",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "👋 Merhaba!\n\n"
            "Yöneticiniz sizi sisteme ekledikten sonra eğitimlere katılabilirsiniz.\n"
            "Sabah gruba gelen eğitim mesajındaki butona basarak eğitime başlayabilirsiniz."
        )
        await _admin_bildir(context, user)


async def metin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or user.is_bot:
        return

    user_id = user.id
    durum = kullanici_durum.get(user_id, {})

    # Doğum tarihi ile ilk doğrulama (kayıtsız kullanıcı eğitime başladı)
    if durum.get("dogum_dogrulama"):
        await dogum_ile_dogrula(update, context, user_id, durum)
        return

    # Sınav sonrası kimlik doğrulama (kayıtlı ama doğum sorusu)
    if durum.get("kimlik_bekleniyor"):
        await kimlik_dogrula(update, context, user_id, durum)
        return

    # Grup mesajı — yeni üye tespiti
    chat = update.effective_chat
    if chat and hasattr(chat, 'type') and chat.type != "private":
        try:
            from calisanlar import calisan_bul
            if not calisan_bul(user_id) and user_id not in ADMIN_IDS:
                await _admin_bildir(context, user)
        except:
            pass


async def dogum_ile_dogrula(update, context, user_id, durum):
    """Kayıtsız kullanıcı doğum tarihi girerek eşleşme yapıyor."""
    from calisanlar import calisan_bul_dogum, telegram_id_guncelle
    girilen = update.message.text.strip()

    tid, calisan = calisan_bul_dogum(girilen)

    if calisan:
        # Eşleşti — Telegram ID'yi güncelle
        telegram_id_guncelle(girilen, user_id)

        durum["dogum_dogrulama"] = False
        durum["kimlik_dogrulandi"] = True
        kullanici_durum[user_id] = durum

        await update.message.reply_text(
            f"✅ Kimliğiniz doğrulandı, *{calisan['ad_soyad'].split()[0]}*!\n\nEğitim başlıyor...",
            parse_mode="Markdown"
        )
        from handlers.egitim_handler import soru_gonder
        from config import EGITIMLER
        egitim = EGITIMLER.get(durum["egitim_id"], {})
        await context.bot.send_message(
            chat_id=user_id, text=egitim.get("metin",""), parse_mode="Markdown"
        )
        await soru_gonder(context, user_id, 0, durum["sorular"])
    else:
        durum["kimlik_deneme"] = durum.get("kimlik_deneme", 0) + 1
        if durum["kimlik_deneme"] >= 3:
            kullanici_durum.pop(user_id, None)
            await update.message.reply_text(
                "❌ 3 yanlış deneme. Yöneticinizle iletişime geçin."
            )
        else:
            kalan = 3 - durum["kimlik_deneme"]
            await update.message.reply_text(
                f"❌ Eşleşme bulunamadı. {kalan} hakkınız kaldı.\n"
                f"Doğum tarihinizi GG.AA.YYYY formatında girin:"
            )


async def kimlik_dogrula(update, context, user_id, durum):
    """Sınav sonrası doğum tarihi doğrulama."""
    from calisanlar import calisan_bul, calisan_bul_dogum
    girilen = update.message.text.strip()

    # Önce Telegram ID ile bak
    calisan = calisan_bul(user_id)

    if calisan:
        dogru = calisan.get("dogum_tarihi", "")
        eslesti = (girilen == dogru or girilen == dogru.split(".")[-1])
    else:
        # Doğum tarihiyle eşleş
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
            await update.message.reply_text("❌ 3 yanlış deneme. Yöneticinizle iletişime geçin.")
        else:
            await update.message.reply_text(
                f"❌ Eşleşmedi. {3 - durum['kimlik_deneme']} hakkınız kaldı.\n"
                f"Doğum tarihinizi girin (GG.AA.YYYY):"
            )


async def sinav_tamamla_direkt(context, user_id, durum, calisan=None, guncelle=None):
    """Sonucu hesapla ve kaydet."""
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
            "egitim_turu": egitim.get("tur", "—"),
            "puan": str(puan),
            "durum": "GEÇTİ" if gecti else "KALDI",
            "kimlik_dogrulandi": "EVET",
            "dogum_yili": calisan.get("dogum_tarihi","").split(".")[-1]
        })
        from durum import tamamlandi_kaydet
        if gecti:
            tamamlandi_kaydet(user_id, egitim_id)
    except Exception as e:
        logger.error(f"Kayıt hatası: {e}")

    kullanici_durum.pop(user_id, None)

    mesaj = (
        f"🎉 *Tebrikler {calisan['ad_soyad'].split()[0]}!*\n\n"
        f"✅ Eğitimi geçtiniz!\n📊 Puanınız: *{puan}/100*\n\nİyi çalışmalar! 👷"
        if gecti else
        f"📋 *Eğitim Sonucu*\n\n❌ Geçemediniz.\n📊 Puanınız: *{puan}/100* (Geçme: {GECME_NOTU})\n\nYöneticiniz sizi bilgilendirecektir."
    )

    if guncelle:
        await guncelle.message.reply_text(mesaj, parse_mode="Markdown")
    else:
        await context.bot.send_message(chat_id=user_id, text=mesaj, parse_mode="Markdown")


async def _admin_bildir(context, user):
    """Admin'e yeni üye bildirimi."""
    user_id = user.id
    if user_id in onay_bekleyenler:
        return
    ad = f"{user.first_name or ''} {user.last_name or ''}".strip() or f"Kullanıcı {user_id}"
    username = f"@{user.username}" if user.username else "—"
    onay_bekleyenler[user_id] = {"ad": ad, "username": username}

    keyboard = [[
        InlineKeyboardButton("✅ Sisteme Ekle", callback_data=f"uye_ekle:{user_id}"),
        InlineKeyboardButton("❌ Yoksay", callback_data=f"uye_yoksay:{user_id}")
    ]]

    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=(
                    f"👤 *Yeni üye grupta!*\n\n"
                    f"*Ad:* {ad}\n*Kullanıcı adı:* {username}\n"
                    f"*Telegram ID:* `{user_id}`\n\n"
                    f"Panelden ekleyin (ID girmek zorunda değilsiniz, "
                    f"doğum tarihi girerseniz sistem otomatik eşleştirir)."
                ),
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            logger.warning(f"Admin bildirimi: {e}")


async def uye_ekle_callback(update, context, user_id):
    bilgi = onay_bekleyenler.get(user_id, {})
    await update.callback_query.edit_message_text(
        f"✅ Panelden ekleyin:\n*Ad:* {bilgi.get('ad','?')}\n`{user_id}`\n\n"
        f"ID girmek zorunda değilsiniz — doğum tarihi girerseniz sistem otomatik eşleştirir.",
        parse_mode="Markdown"
    )


async def uye_yoksay_callback(update, context, user_id):
    bilgi = onay_bekleyenler.pop(user_id, {})
    await update.callback_query.edit_message_text(
        f"❌ {bilgi.get('ad','?')} yoksayıldı.", parse_mode="Markdown"
    )
