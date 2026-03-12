"""
Kimlik doğrulama + otomatik üye tanıma
"""

import logging
from datetime import date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import ADMIN_IDS, GECME_NOTU, GRUP_ID
from calisanlar import tum_calisanlar, calisan_bul
from sheets import kayit_ekle

logger = logging.getLogger(__name__)

# Aktif sınav durumları { user_id: { egitim_id, sorular, soru_idx, dogru_sayisi, kimlik_bekleniyor } }
kullanici_durum = {}

# Onay bekleyen yeni üyeler { user_id: { ad, username } }
onay_bekleyenler = {}


def _bugun(): return date.today().strftime("%d.%m.%Y")


async def metin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gelen tüm metin mesajlarını işle."""
    user = update.effective_user
    if not user:
        return

    user_id = user.id
    durum = kullanici_durum.get(user_id, {})

    # Kimlik doğrulama bekleniyor mu?
    if durum.get("kimlik_bekleniyor"):
        await kimlik_dogrula(update, context, user_id, durum)
        return

    # Grup mesajı — yeni üye tespiti
    chat = update.effective_chat
    if chat and chat.id == GRUP_ID:
        await yeni_uye_tespit(update, context, user)
        return


async def yeni_uye_tespit(update: Update, context: ContextTypes.DEFAULT_TYPE, user):
    """Grupta mesaj yazan bilinmeyen kişiyi admin'e bildir."""
    user_id = user.id

    # Zaten kayıtlı mı?
    if calisan_bul(user_id):
        return

    # Zaten bildirim gönderildi mi?
    if user_id in onay_bekleyenler:
        return

    # Bot mu?
    if user.is_bot:
        return

    ad = f"{user.first_name or ''} {user.last_name or ''}".strip() or f"Kullanıcı {user_id}"
    username = f"@{user.username}" if user.username else "—"

    onay_bekleyenler[user_id] = {"ad": ad, "username": username}

    # Adminlere bildir
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
                    f"👤 *Yeni üye grupta mesaj yazdı!*\n\n"
                    f"*Ad:* {ad}\n"
                    f"*Kullanıcı adı:* {username}\n"
                    f"*Telegram ID:* `{user_id}`\n\n"
                    f"Bu kişiyi eğitim sistemine eklemek ister misiniz?"
                ),
                parse_mode="Markdown",
                reply_markup=markup
            )
        except Exception as e:
            logger.warning(f"Admin bildirimi gönderilemedi: {e}")


async def uye_ekle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Admin 'Sisteme Ekle' butonuna bastı — panele yönlendir."""
    bilgi = onay_bekleyenler.get(user_id, {})
    ad = bilgi.get("ad", "?")
    username = bilgi.get("username", "—")

    await update.callback_query.edit_message_text(
        f"✅ *{ad}* sisteme eklenmek üzere işaretlendi.\n\n"
        f"*Telegram ID:* `{user_id}`\n"
        f"*Kullanıcı adı:* {username}\n\n"
        f"Panelden bu ID ile çalışanı ekleyin:\n"
        f"👉 Çalışanlar → Çalışan Ekle → ID: `{user_id}`\n\n"
        f"Veya hızlı eklemek için doğum tarihini ve görevi gönderin:\n"
        f"`/hizli_ekle {user_id} GOREV GG.AA.YYYY`",
        parse_mode="Markdown"
    )


async def uye_yoksay_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Admin yoksay dedi."""
    bilgi = onay_bekleyenler.pop(user_id, {})
    ad = bilgi.get("ad", "?")
    await update.callback_query.edit_message_text(f"❌ *{ad}* yoksayıldı.", parse_mode="Markdown")


async def kimlik_dogrula(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, durum: dict):
    """Doğum tarihi doğrulama."""
    from calisanlar import calisan_bul
    girilen = update.message.text.strip()
    calisan = calisan_bul(user_id)

    if not calisan:
        await update.message.reply_text("❌ Sisteme kayıtlı değilsiniz. Yöneticinizle iletişime geçin.")
        kullanici_durum.pop(user_id, None)
        return

    dogru_dogum = calisan.get("dogum_tarihi", "")

    # GG.AA.YYYY veya sadece yıl kabul et
    if girilen == dogru_dogum or girilen == dogru_dogum.split(".")[-1]:
        durum["kimlik_bekleniyor"] = False
        durum["kimlik_dogrulandi"] = True
        kullanici_durum[user_id] = durum
        await sinav_tamamla(update, context, user_id, durum)
    else:
        durum["kimlik_deneme"] = durum.get("kimlik_deneme", 0) + 1
        if durum["kimlik_deneme"] >= 3:
            kullanici_durum.pop(user_id, None)
            await update.message.reply_text(
                "❌ Kimlik doğrulama başarısız. 3 yanlış deneme. Yöneticinizle iletişime geçin."
            )
        else:
            kalan = 3 - durum["kimlik_deneme"]
            await update.message.reply_text(
                f"❌ Doğum tarihiniz eşleşmedi. {kalan} deneme hakkınız kaldı.\n"
                f"GG.AA.YYYY formatında girin (örn: 15.06.1990)"
            )


async def sinav_tamamla(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, durum: dict):
    """Kimlik doğrulandı — sonucu kaydet."""
    from calisanlar import calisan_bul
    from config import EGITIMLER, GECME_NOTU

    calisan = calisan_bul(user_id)
    egitim_id = durum.get("egitim_id")
    egitim = EGITIMLER.get(egitim_id, {})
    dogru = durum.get("dogru_sayisi", 0)
    toplam = len(durum.get("sorular", []))
    puan = round(dogru / toplam * 100) if toplam else 0
    gecti = puan >= GECME_NOTU

    simdi = __import__("datetime").datetime.now()
    tarih = simdi.strftime("%d.%m.%Y")
    saat = simdi.strftime("%H:%M")

    try:
        kayit_ekle({
            "tarih": tarih,
            "saat": saat,
            "ad_soyad": calisan["ad_soyad"],
            "telegram_id": str(user_id),
            "gorev": calisan["gorev"],
            "egitim_konusu": egitim.get("baslik", egitim_id),
            "egitim_turu": egitim.get("tur", "—"),
            "puan": str(puan),
            "durum": "GEÇTİ" if gecti else "KALDI",
            "kimlik_dogrulandi": "EVET",
            "dogum_yili": calisan["dogum_tarihi"].split(".")[-1]
        })
        # Tamamlandı kaydet
        from durum import tamamlandi_kaydet
        if gecti:
            tamamlandi_kaydet(user_id, egitim_id)
    except Exception as e:
        logger.error(f"Kayıt hatası: {e}")

    kullanici_durum.pop(user_id, None)

    if gecti:
        mesaj = (
            f"🎉 *Tebrikler {calisan['ad_soyad'].split()[0]}!*\n\n"
            f"✅ Eğitimi başarıyla tamamladınız.\n"
            f"📊 Puanınız: *{puan}/100*\n"
            f"📋 Eğitim: {egitim.get('baslik','')}\n\n"
            f"İyi çalışmalar! 👷"
        )
    else:
        mesaj = (
            f"📋 *Eğitim Sonucu*\n\n"
            f"❌ Maalesef geçemediniz.\n"
            f"📊 Puanınız: *{puan}/100* (Geçme: {GECME_NOTU})\n\n"
            f"Yöneticiniz sizi bilgilendirecektir."
        )

    await update.message.reply_text(mesaj, parse_mode="Markdown")
