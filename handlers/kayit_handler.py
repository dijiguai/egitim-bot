"""
Kimlik dogrulama + otomatik kayit akisi
"""

import logging, datetime, re
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
    args = context.args

    # Egitim baslat
    if args and args[0].startswith("egitim_"):
        egitim_id = args[0].replace("egitim_", "", 1)
        from handlers.egitim_handler import egitim_baslat
        await egitim_baslat(update, context, user_id, egitim_id)
        return

    # Kayit akisi
    if args and args[0] == "kayit":
        await _kayit_baslat(update, context, user_id)
        return

    # Admin
    if user_id in ADMIN_IDS:
        from handlers.admin_handler import start as admin_start
        await admin_start(update, context)
        return

    # Kayitli mi?
    try:
        from calisanlar import calisan_bul
        calisan = calisan_bul(user_id)
    except:
        calisan = None

    if calisan:
        await update.message.reply_text(
            f"Merhaba *{calisan['ad_soyad'].split()[0]}*!\n\n"
            f"Sisteme kayitlisiniz. Sabah 08:00'de egitim bildirimi alacaksiniz.",
            parse_mode="Markdown"
        )
    else:
        await _kayit_baslat(update, context, user_id)


async def _kayit_baslat(update, context, user_id):
    """Kendi kendine kayit akisini baslat - sadece ad sor."""
    kullanici_durum[user_id] = {
        "kayit_akisi": True,
        "adim": "ad_soyad",
        "ad_soyad": "",
        "dogum_tarihi": "00.00.0000",
        "gorev": "Belirsiz",
    }
    await context.bot.send_message(
        chat_id=user_id,
        text=(
            "Hos geldiniz! 👋\n\n"
            "Ad ve soyadinizi girin:\n"
            "(Ornek: Ahmet Yilmaz)"
        )
    )


async def metin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or user.is_bot:
        return

    user_id = user.id
    durum = kullanici_durum.get(user_id, {})

    # Kendi kendine kayit akisi
    if durum.get("kayit_akisi"):
        await _kayit_adim_isle(update, context, user_id, durum)
        return

    if durum.get("dogum_dogrulama"):
        await dogum_ile_dogrula(update, context, user_id, durum)
        return

    if durum.get("kimlik_bekleniyor"):
        await kimlik_dogrula(update, context, user_id, durum)
        return

    # Grup mesajlari ayri handler'da islenir
    chat = update.effective_chat
    if chat and hasattr(chat, 'type') and chat.type in ("group", "supergroup"):
        return


async def _kayit_adim_isle(update, context, user_id, durum):
    """Kayit akisinin her adimini isle."""
    from calisanlar import calisan_ekle
    metin = update.message.text.strip()
    adim = durum.get("adim")

    if adim == "ad_soyad":
        if len(metin) < 3:
            await update.message.reply_text("Lutfen gercek ad soyadinizi girin (en az 3 karakter):")
            return
        durum["ad_soyad"] = metin
        durum["adim"] = "onay"
        kullanici_durum[user_id] = durum

        keyboard = [[
            InlineKeyboardButton("Kaydet", callback_data=f"kayit_onayla:{user_id}"),
            InlineKeyboardButton("Iptal", callback_data=f"kayit_iptal:{user_id}")
        ]]
        await update.message.reply_text(
            f"Adiniz: *{metin}*\n\n"
            f"Kaydedelim mi? Yoneticiniz gorevi ve dogum tarihinizi tamamlayacak.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def kayit_onayla_callback(update, context):
    """Kayit onay butonu."""
    query = update.callback_query
    await query.answer()
    user_id = int(query.data.split(":")[1])

    if query.from_user.id != user_id:
        return

    durum = kullanici_durum.get(user_id, {})
    if not durum.get("kayit_akisi"):
        return

    from calisanlar import calisan_ekle, calisan_bul

    # Zaten kayitli mi?
    if calisan_bul(user_id):
        await query.edit_message_text("Zaten sisteme kayitlisiniz.")
        kullanici_durum.pop(user_id, None)
        return

    try:
        calisan_ekle(user_id, durum["ad_soyad"], durum["dogum_tarihi"], durum["gorev"])
        kullanici_durum.pop(user_id, None)

        await query.edit_message_text(
            f"Kaydiniz tamamlandi!\n\n"
            f"Ad: {durum['ad_soyad']}\n"
            f"Gorev: {durum['gorev']}\n\n"
            f"Artik sabah 08:00'de gunluk egitim bildirimi alacaksiniz."
        )

        # Admin'e bildir
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=(
                        f"Yeni calisan kaydoldu!\n\n"
                        f"Ad: {durum['ad_soyad']}\n"
                        f"Dogum: {durum['dogum_tarihi']}\n"
                        f"Gorev: {durum['gorev']}\n"
                        f"Telegram ID: {user_id}"
                    )
                )
            except:
                pass

    except Exception as e:
        logger.error(f"Kayit hatasi: {e}")
        await query.edit_message_text(f"Kayit sirasinda hata olustu: {e}\n\nLutfen yoneticinizle iletisime gecin.")


async def kayit_iptal_callback(update, context):
    query = update.callback_query
    await query.answer()
    user_id = int(query.data.split(":")[1])
    kullanici_durum.pop(user_id, None)
    await query.edit_message_text("Kayit iptal edildi. Tekrar baslamak icin /start yazin.")


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
    deneme_no = durum.get("deneme_no", 1)

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
            "dogum_yili": calisan.get("dogum_tarihi", "").split(".")[-1],
            "deneme_no": str(deneme_no)
        })
        from durum import tamamlandi_kaydet
        if gecti:
            tamamlandi_kaydet(user_id, egitim_id)
    except Exception as e:
        logger.error(f"Kayit hatasi: {e}")

    kullanici_durum.pop(user_id, None)

    deneme_txt = f" ({deneme_no}. denemede)" if deneme_no > 1 else ""

    # ISG uzman bilgisini al (modül yoksa sessizce atla)
    uzman_satiri = ""
    try:
        from isg.atama_gecmisi import uzman_bilgisi_bul
        from isg.uzmanlar import uzman_unvan_str
        from isg.firma_detay import firma_detay_getir, tehlike_sinifi_str
        from firma_manager import tum_firmalar, grup_id_den_firma
        import datetime as _dt

        egitim_tarihi = simdi.strftime("%d.%m.%Y")

        # Çalışanın hangi firmada olduğunu bul (grup_id üzerinden)
        firma_id = None
        try:
            from config import GRUP_ID
            if GRUP_ID:
                fid, _ = grup_id_den_firma(GRUP_ID)
                firma_id = fid
        except Exception:
            firma_id = "varsayilan"

        if firma_id:
            bilgi = uzman_bilgisi_bul(firma_id, egitim_tarihi)
            uzman = bilgi.get("is_guvenligi_uzmani", {})
            if uzman:
                detay = firma_detay_getir(firma_id)
                firma_ad = tum_firmalar().get(firma_id, {}).get("ad", "")
                tehlike = tehlike_sinifi_str(detay.get("tehlike_sinifi", ""))
                uzman_satiri = (
                    f"\n\n─────────────────────\n"
                    f"🛡️ *{uzman_unvan_str(uzman)}*"
                )
                if firma_ad:
                    uzman_satiri += f"\n🏭 {firma_ad}"
                if tehlike:
                    uzman_satiri += f" · {tehlike}"
                uzman_satiri += "\n─────────────────────"
    except Exception as _isg_e:
        logger.debug(f"ISG uzman bilgisi alınamadı (normal): {_isg_e}")

    if gecti:
        mesaj = (
            f"✅ *Tebrikler {calisan['ad_soyad'].split()[0]}!*\n\n"
            f"🏆 *{egitim.get('baslik', '')}* eğitimini geçtiniz{deneme_txt}!\n"
            f"📊 Puanınız: *{puan}/100*"
            f"{uzman_satiri}"
        )
    else:
        mesaj = (
            f"📋 *Eğitim Sonucu*\n\n"
            f"Geçemediniz. Puanınız: *{puan}/100* (Geçme: {GECME_NOTU})\n\n"
            f"Yöneticiniz ek hak tanımlarsa tekrar girebilirsiniz."
        )

    if guncelle:
        await guncelle.message.reply_text(mesaj, parse_mode="Markdown")
    else:
        await context.bot.send_message(chat_id=user_id, text=mesaj, parse_mode="Markdown")


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
                    f"Yeni uye!\n\nAd: {ad}\nKullanici adi: {username}\nID: {user_id}\n\n"
                    f"Panelden ekleyin."
                ),
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            logger.warning(f"Admin bildirimi: {e}")


async def uye_ekle_callback(update, context, user_id):
    bilgi = onay_bekleyenler.get(user_id, {})
    await update.callback_query.edit_message_text(
        f"Panelden ekleyin:\nAd: {bilgi.get('ad','?')}\nID: {user_id}\n\n"
        f"ID girmek zorunda degilsiniz."
    )


async def uye_yoksay_callback(update, context, user_id):
    bilgi = onay_bekleyenler.pop(user_id, {})
    await update.callback_query.edit_message_text(f"{bilgi.get('ad','?')} yoksayildi.")
