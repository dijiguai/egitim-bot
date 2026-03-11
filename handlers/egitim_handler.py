"""
Eğitim akışı — Buton tıklamaları ve sınav yönetimi
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import EGITIMLER, GECME_NOTU, SORU_SAYISI

logger = logging.getLogger(__name__)

# Her kullanıcının anlık sınav durumu bellekte tutulur
# { user_id: { egitim_id, soru_index, dogru_sayisi, cevaplar } }
kullanici_durum = {}


async def buton_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tüm inline buton tıklamalarını yönetir."""
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    # ── Eğitim başlat ──────────────────────────────────────
    if data.startswith("egitim_baslat:"):
        egitim_id = data.split(":")[1]
        egitim = EGITIMLER.get(egitim_id)
        if not egitim:
            await query.edit_message_text("Eğitim bulunamadı.")
            return

        kullanici_durum[user_id] = {
            "egitim_id": egitim_id,
            "soru_index": 0,
            "dogru_sayisi": 0,
            "cevaplar": [],
            "baslangic": update.effective_message.date
        }

        keyboard = [[InlineKeyboardButton("📝 Sınava Geç ➜", callback_data="sinava_gec")]]
        await query.edit_message_text(
            egitim["metin"],
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # ── Sınava geç ─────────────────────────────────────────
    elif data == "sinava_gec":
        if user_id not in kullanici_durum:
            await query.edit_message_text("Oturum bulunamadı. Lütfen tekrar /start yapın.")
            return
        await _soru_gonder(query, user_id, context)

    # ── Cevap seçildi ──────────────────────────────────────
    elif data.startswith("cevap:"):
        if user_id not in kullanici_durum:
            await query.edit_message_text("Oturum süresi dolmuş.")
            return

        secilen = int(data.split(":")[1])
        durum = kullanici_durum[user_id]
        egitim = EGITIMLER[durum["egitim_id"]]
        soru_obj = egitim["sorular"][durum["soru_index"]]

        dogru_mu = (secilen == soru_obj["dogru"])
        durum["cevaplar"].append({
            "soru": soru_obj["soru"],
            "secilen": secilen,
            "dogru": soru_obj["dogru"],
            "dogru_mu": dogru_mu
        })

        if dogru_mu:
            durum["dogru_sayisi"] += 1

        durum["soru_index"] += 1

        # Sonraki soru veya bitiş
        if durum["soru_index"] < len(egitim["sorular"]):
            await _soru_gonder(query, user_id, context)
        else:
            await sinav_bitti_mesaj(query, user_id, context)


async def _soru_gonder(query, user_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Sıradaki soruyu gönderir."""
    durum = kullanici_durum[user_id]
    egitim = EGITIMLER[durum["egitim_id"]]
    idx = durum["soru_index"]
    soru_obj = egitim["sorular"][idx]
    toplam = len(egitim["sorular"])

    harfler = ["A", "B", "C", "D"]
    keyboard = [
        [InlineKeyboardButton(f"{harfler[i]}) {opt}", callback_data=f"cevap:{i}")]
        for i, opt in enumerate(soru_obj["secenekler"])
    ]

    metin = (
        f"❓ *Soru {idx + 1} / {toplam}*\n\n"
        f"{soru_obj['soru']}"
    )

    await query.edit_message_text(
        metin,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def sinav_bitti_mesaj(query, user_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Sınav bitti — kimlik doğrulama adımına yönlendir."""
    durum = kullanici_durum[user_id]
    egitim = EGITIMLER[durum["egitim_id"]]
    toplam_soru = len(egitim["sorular"])
    puan = round((durum["dogru_sayisi"] / toplam_soru) * 100)

    durum["puan"] = puan

    # Sonuç önizlemesi
    sonuc_ikonu = "✅" if puan >= GECME_NOTU else "❌"
    metin = (
        f"{sonuc_ikonu} *Sınav Tamamlandı*\n\n"
        f"📊 Puanınız: *{puan}/100*\n"
        f"✔️ Doğru: {durum['dogru_sayisi']}/{toplam_soru}\n\n"
        f"🔐 *Kimlik Doğrulama*\n"
        f"Eğitimi gerçekten siz aldığınızı onaylamak için "
        f"sisteme kayıtlı *doğum tarihinizi* yazınız.\n\n"
        f"_Örnek: 15.06.1990_"
    )

    await query.edit_message_text(metin, parse_mode="Markdown")

    # Konuşma handler'ına geçiş için context'e işaretle
    context.user_data["kimlik_bekleniyor"] = True


async def sinav_bitti(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ConversationHandler entry point — kimlik doğrulama başlar."""
    from handlers.kayit_handler import KIMLIK_DOGRULAMA
    context.user_data["kimlik_bekleniyor"] = True
    return KIMLIK_DOGRULAMA
