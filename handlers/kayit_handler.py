"""
Kimlik doğrulama ve sonuç kayıt işlemleri
"""

import logging
import re
from datetime import datetime, date
from telegram import Update
from telegram.ext import ContextTypes
from handlers.egitim_handler import kullanici_durum
from config import EGITIMLER, GECME_NOTU
from sheets import sonuc_kaydet

logger = logging.getLogger(__name__)

# Kimlik doğrulama bekleyen kullanıcılar
kimlik_bekleyenler = set()

# Çalışan veritabanı
# { telegram_user_id: { "ad_soyad": ..., "dogum_tarihi": "15.06.1990", "gorev": ... } }
CALISANLAR = {
    # Örnek — kendi ID ve bilgilerini ekle:
    # 1424268115: {
    #     "ad_soyad": "Ad Soyad",
    #     "dogum_tarihi": "GG.AA.YYYY",
    #     "gorev": "Görev"
    # },
}


def dogum_tarihi_gecerli_mi(metin: str) -> bool:
    pattern = r"^\d{2}\.\d{2}\.\d{4}$"
    if not re.match(pattern, metin.strip()):
        return False
    try:
        datetime.strptime(metin.strip(), "%d.%m.%Y")
        return True
    except ValueError:
        return False


async def metin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tüm metin mesajlarını yakalar — kimlik doğrulama bekliyorsa işler."""
    user_id = update.effective_user.id

    # Bu kullanıcı sınav tamamladı ve kimlik doğrulama bekleniyor mu?
    if user_id not in kullanici_durum:
        return  # Eğitimde değil, yoksay

    durum = kullanici_durum[user_id]
    if not durum.get("kimlik_bekleniyor"):
        return  # Henüz sınav bitmedi, yoksay

    girilen = update.message.text.strip()

    # Format kontrolü
    if not dogum_tarihi_gecerli_mi(girilen):
        await update.message.reply_text(
            "⚠️ Geçersiz format. Lütfen GG.AA.YYYY şeklinde yazın.\n"
            "_Örnek: 15.06.1990_",
            parse_mode="Markdown"
        )
        return

    # Çalışan kaydı kontrolü
    calisan = CALISANLAR.get(user_id)
    if calisan and calisan["dogum_tarihi"] != girilen:
        await update.message.reply_text(
            "❌ Doğum tarihi eşleşmedi. Tekrar deneyin.\n"
            "_Örnek format: 15.06.1990_",
            parse_mode="Markdown"
        )
        return

    # Sonucu kaydet
    egitim = EGITIMLER[durum["egitim_id"]]
    puan = durum.get("puan", 0)
    gecti = puan >= GECME_NOTU
    bugun = date.today().strftime("%d.%m.%Y")
    saat = datetime.now().strftime("%H:%M")

    ad_soyad = calisan["ad_soyad"] if calisan else update.effective_user.full_name
    gorev = calisan["gorev"] if calisan else "—"

    kayit = {
        "tarih": bugun,
        "saat": saat,
        "ad_soyad": ad_soyad,
        "telegram_id": str(user_id),
        "gorev": gorev,
        "egitim_konusu": egitim["baslik"],
        "egitim_turu": egitim["tur"],
        "puan": puan,
        "durum": "GEÇTİ" if gecti else "KALDI",
        "kimlik_dogrulandi": "EVET",
        "dogum_tarihi_son4": girilen[-4:],
    }

    try:
        sonuc_kaydet(kayit)
        logger.info(f"Kayıt OK: {ad_soyad} — {puan}p — {'GEÇTİ' if gecti else 'KALDI'}")
    except Exception as e:
        logger.error(f"Sheets hatası: {e}")

    # Sonuç mesajı
    if gecti:
        mesaj = (
            f"🎉 *TEBRİKLER — GEÇTİNİZ!*\n\n"
            f"👤 {ad_soyad}\n"
            f"📋 {egitim['baslik']}\n"
            f"📊 Puanınız: *{puan}/100*\n"
            f"🔐 Kimlik: ✅ Doğrulandı\n"
            f"📅 {bugun} · {saat}\n\n"
            f"✅ *İş başına geçebilirsiniz.*"
        )
    else:
        mesaj = (
            f"❌ *SINAVI GEÇEMEDİNİZ*\n\n"
            f"👤 {ad_soyad}\n"
            f"📋 {egitim['baslik']}\n"
            f"📊 Puanınız: *{puan}/100* (Geçme: {GECME_NOTU})\n"
            f"🔐 Kimlik: ✅ Doğrulandı\n"
            f"📅 {bugun} · {saat}\n\n"
            f"⚠️ *Eğitmeninize başvurun.*"
        )

    await update.message.reply_text(mesaj, parse_mode="Markdown")

    # Temizle
    kullanici_durum.pop(user_id, None)


async def iptal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kullanici_durum.pop(update.effective_user.id, None)
    await update.message.reply_text("İşlem iptal edildi.")
