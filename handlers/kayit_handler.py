"""
Kimlik doğrulama + otomatik üye tanıma
"""

import logging
from datetime import date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import ADMIN_IDS, GECME_NOTU, GRUP_ID
from sheets import kayit_ekle

logger = logging.getLogger(__name__)

kullanici_durum = {}
onay_bekleyenler = {}  # { user_id: { ad, username } }


def _bugun():
    return date.today().strftime("%d.%m.%Y")


async def metin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or user.is_bot:
        return

    user_id = user.id
    durum = kullanici_durum.get(user_id, {})

    # Kimlik doğrulama bekleniyor mu?
    if durum.get("kimlik_bekleniyor"):
        await kimlik_dogrula(update, context, user_id, durum)
        return

    # Özel mesaj — kayıtlı değilse otomatik tanı
    chat = update.effective_chat
    if chat and chat.type == "private":
        try:
            from calisanlar import calisan_bul
            calisan = calisan_bul(user_id)
        except:
            calisan = None

        if not calisan and user_id not in ADMIN_IDS:
            await yeni_uye_bildir(update, context, user)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Çalışan bota /start yazınca çalışır.
    Kayıtlı değilse admin'e bildirim gönderilir.
    """
    user = update.effective_user
    if not user:
        return

    user_id = user.id

    # Admin ise admin menüsü
    if user_id in ADMIN_IDS:
        from handlers.admin_handler import start as admin_start
        await admin_start(update, context)
        return

    # Kayıtlı mı kontrol et
    try:
        from calisanlar import calisan_bul
        calisan = calisan_bul(user_id)
    except:
        calisan = None

    if calisan:
        # Kayıtlı — hoş geldin
        await update.message.reply_text(
            f"👷 Merhaba *{calisan['ad_soyad'].split()[0]}*!\n\n"
            f"Bugünkü eğitim hazır olduğunda bildirim alacaksınız.\n"
            f"Sabah 08:00'de otomatik bildirim gönderilir.",
            parse_mode="Markdown"
        )
    else:
        # Kayıtlı değil — admin'e bildir
        await update.message.reply_text(
            f"👋 Merhaba!\n\n"
            f"Sisteme kaydınız yapılıyor, yöneticiniz sizi onaylayacak.\n"
            f"Onaylandıktan sonra eğitimlere katılabilirsiniz."
        )
        await yeni_uye_bildir(update, context, user)


async def yeni_uye_bildir(update: Update, context: ContextTypes.DEFAULT_TYPE, user):
    """Admin'e yeni üye bildirimi gönder."""
    user_id = user.id

    if user_id in onay_bekleyenler:
        return  # Zaten bildirim gönderildi

    ad = f"{user.first_name or ''} {user.last_name or ''}".strip() or f"Kullanıcı {user_id}"
    username = f"@{user.username}" if user.username else "—"

    onay_bekleyenler[user_id] = {"ad": ad, "username": username}

    keyboard = [[
        InlineKeyboardButton("✅ Sisteme Ekle", callback_data=f"uye_ekle:{user_id}"),
        InlineKeyboardButton("❌ Yoksay", callback_data=f"uye_yoksay:{user_id}")
    ]]
    markup = InlineKeyboardMarkup(keyboard)

    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=(
                    f"👤 *Yeni çalışan sisteme katılmak istiyor!*\n\n"
                    f"*Ad:* {ad}\n"
                    f"*Kullanıcı adı:* {username}\n"
                    f"*Telegram ID:* `{user_id}`\n\n"
                    f"Panelden eklemek için ID'yi kullanın ya da hızlı eklemek için:\n"
                    f"`/hizli_ekle {user_id} Görev 01.01.1990`"
                ),
                parse_mode="Markdown",
                reply_markup=markup
            )
        except Exception as e:
            logger.warning(f"Admin bildirimi gönderilemedi: {e}")


async def uye_ekle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    bilgi = onay_bekleyenler.get(user_id, {})
    ad = bilgi.get("ad", "?")
    await update.callback_query.edit_message_text(
        f"✅ *{ad}* için panele gidin ve ekleyin.\n\n"
        f"*Telegram ID:* `{user_id}`\n\n"
        f"Ya da hızlı eklemek için:\n"
        f"`/hizli_ekle {user_id} Görev GG.AA.YYYY`",
        parse_mode="Markdown"
    )


async def uye_yoksay_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    bilgi = onay_bekleyenler.pop(user_id, {})
    await update.callback_query.edit_message_text(
        f"❌ *{bilgi.get('ad','?')}* yoksayıldı.", parse_mode="Markdown"
    )


async def kimlik_dogrula(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, durum: dict):
    from calisanlar import calisan_bul
    girilen = update.message.text.strip()
    calisan = calisan_bul(user_id)

    if not calisan:
        await update.message.reply_text("❌ Sisteme kayıtlı değilsiniz.")
        kullanici_durum.pop(user_id, None)
        return

    dogru = calisan.get("dogum_tarihi", "")

    # GG.AA.YYYY veya sadece yıl kabul
    if girilen == dogru or girilen == dogru.split(".")[-1]:
        durum["kimlik_bekleniyor"] = False
        durum["kimlik_dogrulandi"] = True
        kullanici_durum[user_id] = durum
        await sinav_tamamla(update, context, user_id, durum)
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
                f"❌ Doğum tarihi eşleşmedi. {kalan} hakkınız kaldı.\n"
                f"Format: GG.AA.YYYY (örn: 15.06.1990)"
            )


async def sinav_tamamla(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, durum: dict):
    from calisanlar import calisan_bul
    from config import EGITIMLER

    calisan = calisan_bul(user_id)
    egitim_id = durum.get("egitim_id")
    egitim = EGITIMLER.get(egitim_id, {})
    dogru = durum.get("dogru_sayisi", 0)
    toplam = len(durum.get("sorular", []))
    puan = round(dogru / toplam * 100) if toplam else 0
    gecti = puan >= GECME_NOTU

    import datetime
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
            "dogum_yili": calisan["dogum_tarihi"].split(".")[-1] if calisan.get("dogum_tarihi") else ""
        })
        from durum import tamamlandi_kaydet
        if gecti:
            tamamlandi_kaydet(user_id, egitim_id)
    except Exception as e:
        logger.error(f"Kayıt hatası: {e}")

    kullanici_durum.pop(user_id, None)

    if gecti:
        mesaj = (
            f"🎉 *Tebrikler {calisan['ad_soyad'].split()[0]}!*\n\n"
            f"✅ Eğitimi geçtiniz!\n"
            f"📊 Puanınız: *{puan}/100*\n"
            f"📋 {egitim.get('baslik','')}\n\n"
            f"İyi çalışmalar! 👷"
        )
    else:
        mesaj = (
            f"📋 *Eğitim Sonucu*\n\n"
            f"❌ Geçemediniz.\n"
            f"📊 Puanınız: *{puan}/100* (Geçme: {GECME_NOTU})\n\n"
            f"Yöneticiniz sizi bilgilendirecektir."
        )

    await update.message.reply_text(mesaj, parse_mode="Markdown")
