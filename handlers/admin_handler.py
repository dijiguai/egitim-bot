"""
Admin komutları — /egitim_gonder, /rapor, /kalanlar
"""

import logging
from datetime import date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import EGITIMLER, ADMIN_IDS, GECME_NOTU
from handlers.egitim_handler import kullanici_durum
from sheets import kayitlari_getir

logger = logging.getLogger(__name__)


def admin_mi(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bota ilk kez başlayanlar için karşılama mesajı."""
    metin = (
        "👷 *İş Başı Eğitim Sistemi*\n\n"
        "Sabah eğitiminiz geldiğinde butona tıklayarak başlayabilirsiniz.\n\n"
        "📌 *Nasıl çalışır?*\n"
        "1. Eğitim metnini okuyun\n"
        "2. 5 soruyu yanıtlayın\n"
        "3. Doğum tarihinizle onaylayın\n"
        "4. 70 puan ve üzeri → iş başına geçin ✅\n\n"
        "_Sorun yaşarsanız yöneticinize bildirin._"
    )
    await update.message.reply_text(metin, parse_mode="Markdown")


async def egitim_gonder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Admin komutu: /egitim_gonder forklift_guvenligi
    Grupta eğitimi başlatır.
    """
    if not admin_mi(update.effective_user.id):
        await update.message.reply_text("⛔ Bu komutu kullanma yetkiniz yok.")
        return

    args = context.args
    if not args:
        # Eğitim listesini göster
        egitim_listesi = "\n".join(
            [f"• `{k}` — {v['baslik']}" for k, v in EGITIMLER.items()]
        )
        await update.message.reply_text(
            f"📚 *Mevcut Eğitimler:*\n\n{egitim_listesi}\n\n"
            f"Kullanım: `/egitim_gonder forklift_guvenligi`",
            parse_mode="Markdown"
        )
        return

    egitim_id = args[0]
    egitim = EGITIMLER.get(egitim_id)

    if not egitim:
        await update.message.reply_text(
            f"❌ `{egitim_id}` bulunamadı. `/egitim_gonder` ile listeye bakın.",
            parse_mode="Markdown"
        )
        return

    bugun = date.today().strftime("%d.%m.%Y")
    keyboard = [[
        InlineKeyboardButton("▶️ Eğitime Başla", callback_data=f"egitim_baslat:{egitim_id}")
    ]]

    metin = (
        f"🔔 *Günün Eğitimi — {bugun}*\n\n"
        f"📋 *Konu:* {egitim['baslik']}\n"
        f"🏷 *Tür:* {egitim['tur']}\n"
        f"⏱ *Tahmini Süre:* {egitim['sure']}\n"
        f"✅ *Geçme Notu:* {GECME_NOTU}/100\n\n"
        f"Aşağıdaki butona tıklayarak eğitiminizi başlatın. "
        f"İş başına geçmeden önce tamamlanması zorunludur."
    )

    await update.message.reply_text(
        metin,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def rapor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin komutu: /rapor — bugünkü özet."""
    if not admin_mi(update.effective_user.id):
        await update.message.reply_text("⛔ Bu komutu kullanma yetkiniz yok.")
        return

    bugun = date.today().strftime("%d.%m.%Y")

    try:
        kayitlar = kayitlari_getir(bugun)
    except Exception as e:
        logger.error(f"Sheets hatası: {e}")
        kayitlar = []

    if not kayitlar:
        await update.message.reply_text(
            f"📊 *{bugun} Raporu*\n\nHenüz tamamlanan eğitim yok.",
            parse_mode="Markdown"
        )
        return

    gecenler = [k for k in kayitlar if k.get("durum") == "GEÇTİ"]
    kalanlar = [k for k in kayitlar if k.get("durum") == "KALDI"]
    toplam = len(kayitlar)
    oran = round((len(gecenler) / toplam) * 100) if toplam > 0 else 0

    gecen_liste = "\n".join([f"  ✅ {k['ad_soyad']}" for k in gecenler]) or "  —"
    kalan_liste = "\n".join([f"  ❌ {k['ad_soyad']} ({k['puan']}p)" for k in kalanlar]) or "  —"

    metin = (
        f"📊 *{bugun} Eğitim Raporu*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👥 Toplam: {toplam} kişi\n"
        f"✅ Geçti: {len(gecenler)} kişi (%{oran})\n"
        f"❌ Kaldı: {len(kalanlar)} kişi\n\n"
        f"*Geçenler:*\n{gecen_liste}\n\n"
        f"*Kalanlar:*\n{kalan_liste}"
    )

    await update.message.reply_text(metin, parse_mode="Markdown")


async def kalanlar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin komutu: /kalanlar — henüz tamamlamayanlar."""
    if not admin_mi(update.effective_user.id):
        await update.message.reply_text("⛔ Bu komutu kullanma yetkiniz yok.")
        return

    bugun = date.today().strftime("%d.%m.%Y")

    try:
        kayitlar = kayitlari_getir(bugun)
    except Exception:
        kayitlar = []

    kalan_listesi = [k for k in kayitlar if k.get("durum") == "KALDI"]

    if not kalan_listesi:
        await update.message.reply_text("✅ Bugün kalan çalışan yok!")
        return

    liste = "\n".join([
        f"❌ {k['ad_soyad']} — {k['puan']} puan"
        for k in kalan_listesi
    ])

    await update.message.reply_text(
        f"⚠️ *Bugün Kalan Çalışanlar ({bugun}):*\n\n{liste}\n\n"
        f"_Bu çalışanları yüz yüze eğitime alın._",
        parse_mode="Markdown"
    )


async def yardim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Komut listesi."""
    if admin_mi(update.effective_user.id):
        metin = (
            "🛠 *Admin Komutları:*\n\n"
            "/egitim_gonder `[egitim_id]` — Eğitimi gruba gönder\n"
            "/rapor — Bugünkü özet rapor\n"
            "/kalanlar — Kalan çalışanlar listesi\n"
            "/yardim — Bu mesaj\n\n"
            "📚 Eğitim listesi için: `/egitim_gonder`"
        )
    else:
        metin = (
            "👷 *Eğitim Botu Yardım*\n\n"
            "Sabah gelen eğitim mesajındaki butona tıklayın.\n"
            "Sorun için yöneticinize başvurun."
        )
    await update.message.reply_text(metin, parse_mode="Markdown")
