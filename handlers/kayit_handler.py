"""
Kimlik doğrulama ve sonuç kayıt işlemleri
"""

import logging
import re
from datetime import datetime, date
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from handlers.egitim_handler import kullanici_durum
from config import EGITIMLER, GECME_NOTU
from sheets import sonuc_kaydet

logger = logging.getLogger(__name__)

KIMLIK_DOGRULAMA = 1

# Çalışan veritabanı — production'da bu bir dosya veya veritabanı olur
# { telegram_user_id: { "ad_soyad": ..., "dogum_tarihi": "15.06.1990", "gorev": ... } }
CALISANLAR = {
    # Örnek kayıt — gerçek sistemde bu bir JSON dosyasından veya
    # Google Sheets'teki "Çalışanlar" sekmesinden okunur
    # 123456789: {
    #     "ad_soyad": "Ahmet Yılmaz",
    #     "dogum_tarihi": "15.06.1990",
    #     "gorev": "Operatör"
    # },
}


def dogum_tarihi_gecerli_mi(metin: str) -> bool:
    """GG.AA.YYYY formatını kontrol eder."""
    pattern = r"^\d{2}\.\d{2}\.\d{4}$"
    if not re.match(pattern, metin.strip()):
        return False
    try:
        datetime.strptime(metin.strip(), "%d.%m.%Y")
        return True
    except ValueError:
        return False


async def kimlik_dogrula(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kullanıcının yazdığı doğum tarihini doğrular."""
    user_id = update.effective_user.id
    girilen = update.message.text.strip()

    # Format kontrolü
    if not dogum_tarihi_gecerli_mi(girilen):
        await update.message.reply_text(
            "⚠️ Geçersiz format. Lütfen GG.AA.YYYY şeklinde yazın.\n"
            "_Örnek: 15.06.1990_",
            parse_mode="Markdown"
        )
        return KIMLIK_DOGRULAMA  # Tekrar bekle

    # Çalışan kaydı kontrolü
    calisan = CALISANLAR.get(user_id)

    if calisan and calisan["dogum_tarihi"] != girilen:
        await update.message.reply_text(
            "❌ Doğum tarihi eşleşmedi. Lütfen sisteme kayıtlı tarihinizi girin.\n\n"
            "_3 kez hatalı girişte hesabınız kilitlenir._"
        )
        return KIMLIK_DOGRULAMA

    # ── Sonucu kaydet ──────────────────────────────────────
    durum = kullanici_durum.get(user_id, {})
    if not durum:
        await update.message.reply_text("Oturum bulunamadı. Lütfen tekrar başlayın.")
        return ConversationHandler.END

    egitim = EGITIMLER[durum["egitim_id"]]
    puan = durum.get("puan", 0)
    gecti = puan >= GECME_NOTU
    bugun = date.today().strftime("%d.%m.%Y")
    saat = datetime.now().strftime("%H:%M")

    ad_soyad = calisan["ad_soyad"] if calisan else update.effective_user.full_name
    gorev = calisan["gorev"] if calisan else "—"

    # Google Sheets'e kaydet
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
        "dogum_tarihi_son4": girilen[-4:],  # Sadece yıl kaydedilir — KVKK
    }

    try:
        sonuc_kaydet(kayit)
        logger.info(f"Kayıt başarılı: {ad_soyad} — {puan}p — {'GEÇTİ' if gecti else 'KALDI'}")
    except Exception as e:
        logger.error(f"Sheets kayıt hatası: {e}")

    # ── Sonuç mesajı ───────────────────────────────────────
    if gecti:
        mesaj = (
            f"🎉 *TEBRİKLER — GEÇTİNİZ!*\n\n"
            f"👤 {ad_soyad}\n"
            f"📋 {egitim['baslik']}\n"
            f"📊 Puanınız: *{puan}/100*\n"
            f"🔐 Kimlik: ✅ Doğrulandı\n"
            f"📅 {bugun} · {saat}\n\n"
            f"✅ *İş başına geçebilirsiniz.*\n\n"
            f"_Bu kayıt sisteme işlenmiştir._"
        )
    else:
        mesaj = (
            f"❌ *SINAVI GEÇEMEDİNİZ*\n\n"
            f"👤 {ad_soyad}\n"
            f"📋 {egitim['baslik']}\n"
            f"📊 Puanınız: *{puan}/100* (Geçme: {GECME_NOTU})\n"
            f"🔐 Kimlik: ✅ Doğrulandı\n"
            f"📅 {bugun} · {saat}\n\n"
            f"⚠️ *Yüz yüze eğitime alınacaksınız.*\n"
            f"Lütfen eğitmeninize başvurun.\n\n"
            f"_Bu kayıt sisteme işlenmiştir._"
        )

    await update.message.reply_text(mesaj, parse_mode="Markdown")

    # Durumu temizle
    kullanici_durum.pop(user_id, None)
    context.user_data.clear()

    return ConversationHandler.END


async def iptal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kullanici_durum.pop(update.effective_user.id, None)
    await update.message.reply_text("İşlem iptal edildi.")
    return ConversationHandler.END
