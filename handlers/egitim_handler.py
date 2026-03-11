"""
E�itim akışı — Buton tıklamaları ve sınav yönetimi
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import EGITIMLER, GECME_NOTU

logger = logging.getLogger(__name__)

# { user_id: { egitim_id, soru_index, dogru_sayisi, puan, kimlik_bekleniyor } }
kullanici_durum = {}


async def buton_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    # Eğitim başlat
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
            "puan": 0,
            "kimlik_bekleniyor": False,
        }

        keyboard = [[InlineKeyboardButton("📝 Sınava Geç ➜", callback_data="sinava_gec")]]
        await query.edit_message_text(
            egitim["metin"],
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # Sınava geç
    elif data == "sinava_gec":
        if user_id not in kullanici_durum:
            await query.edit_message_text("Oturum bulunamadı. /start yazın.")
            return
        await _soru_gonder(query, user_id)

    # Cevap seçildi
    elif data.startswith("cevap:"):
        if user_id not in kullanici_durum:
            await query.edit_message_text("Oturum süresi dolmuş.")
            return

        secilen = int(data.split(":")[1])
        durum = kullanici_durum[user_id]
        egitim = EGITIMLER[durum["egitim_id"]]
        soru_obj = egitim["sorular"][durum["soru_index"]]

        if secilen == soru_obj["dogru"]:
            durum["dogru_sayisi"] += 1

        durum["soru_index"] += 1

        if durum["soru_index"] < len(egitim["sorular"]):
            await _soru_gonder(query, user_id)
        else:
            await _sinav_bitti(query, user_id)


async def _soru_gonder(query, user_id: int):
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

    await query.edit_message_text(
        f"❓ *Soru {idx + 1} / {toplam}*\n\n{soru_obj['soru']}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def _sinav_bitti(query, user_id: int):
    durum = kullanici_durum[user_id]
    egitim = EGITIMLER[durum["egitim_id"]]
    toplam = len(egitim["sorular"])
    puan = round((durum["dogru_sayisi"] / toplam) * 100)
    durum["puan"] = puan
    durum["kimlik_bekleniyor"] = True  # metin_handler devreye girecek

    sonuc = "✅" if puan >= GECME_NOTU else "❌"
    await query.edit_message_text(
        f"{sonuc} *Sınav Tamamlandı*\n\n"
        f"📊 Puanınız: *{puan}/100*\n"
        f"✔️ Doğru: {durum['dogru_sayisi']}/{toplam}\n\n"
        f"🔐 *Kimlik Doğrulama*\n"
        f"Doğum tarihinizi yazın:\n"
        f"_Örnek: 15.06.1990_",
        parse_mode="Markdown"
    )
