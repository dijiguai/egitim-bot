"""
E�itim buton ve sınav akışı
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import EGITIMLER, GECME_NOTU
from calisanlar import calisan_bul
from handlers.kayit_handler import kullanici_durum

logger = logging.getLogger(__name__)


async def buton_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    # Üye ekleme butonları
    if data.startswith("uye_ekle:"):
        tid = int(data.split(":")[1])
        from handlers.kayit_handler import uye_ekle_callback
        await uye_ekle_callback(update, context, tid)
        return

    if data.startswith("uye_yoksay:"):
        tid = int(data.split(":")[1])
        from handlers.kayit_handler import uye_yoksay_callback
        await uye_yoksay_callback(update, context, tid)
        return

    # Eğitim başlat
    if data.startswith("egitim_baslat:"):
        egitim_id = data.split(":")[1]
        await egitim_baslat(update, context, user_id, egitim_id)
        return

    # Soru cevabı
    if data.startswith("cevap:"):
        _, soru_idx, secim = data.split(":")
        await cevap_isle(update, context, user_id, int(soru_idx), int(secim))
        return


async def egitim_baslat(update, context, user_id, egitim_id):
    egitim = EGITIMLER.get(egitim_id)
    if not egitim:
        await update.callback_query.edit_message_text("❌ Eğitim bulunamadı.")
        return

    calisan = calisan_bul(user_id)
    if not calisan:
        await update.callback_query.edit_message_text(
            "⛔ Sisteme kayıtlı değilsiniz.\n\n"
            "Yöneticinizden sizi sisteme eklemesini isteyin."
        )
        return

    # Durumu başlat
    kullanici_durum[user_id] = {
        "egitim_id": egitim_id,
        "sorular": egitim["sorular"],
        "soru_idx": 0,
        "dogru_sayisi": 0,
        "kimlik_bekleniyor": False,
        "kimlik_dogrulandi": False,
        "kimlik_deneme": 0
    }

    # Eğitim metnini gönder
    await context.bot.send_message(
        chat_id=user_id,
        text=egitim["metin"],
        parse_mode="Markdown"
    )

    # İlk soruyu sor
    await soru_gonder(context, user_id, 0, egitim["sorular"])


async def soru_gonder(context, user_id, idx, sorular):
    soru_obj = sorular[idx]
    soru = soru_obj["soru"]
    secenekler = soru_obj["secenekler"]

    keyboard = [
        [InlineKeyboardButton(f"{['A','B','C','D'][i]}) {s}", callback_data=f"cevap:{idx}:{i}")]
        for i, s in enumerate(secenekler)
    ]

    await context.bot.send_message(
        chat_id=user_id,
        text=f"❓ *Soru {idx+1}/{len(sorular)}*\n\n{soru}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def cevap_isle(update, context, user_id, soru_idx, secim):
    durum = kullanici_durum.get(user_id)
    if not durum:
        await update.callback_query.edit_message_text("❌ Oturum sona erdi. Tekrar başlayın.")
        return

    sorular = durum["sorular"]
    if soru_idx != durum["soru_idx"]:
        return  # Eski soruya cevap geldi, yoksay

    dogru = sorular[soru_idx]["dogru"]
    harf = ["A", "B", "C", "D"]

    if secim == dogru:
        durum["dogru_sayisi"] += 1
        await update.callback_query.edit_message_text(
            f"✅ *Doğru!*\n\n{update.callback_query.message.text}",
            parse_mode="Markdown"
        )
    else:
        await update.callback_query.edit_message_text(
            f"❌ *Yanlış.* Doğru cevap: {harf[dogru]}) {sorular[soru_idx]['secenekler'][dogru]}\n\n{update.callback_query.message.text}",
            parse_mode="Markdown"
        )

    sonraki = soru_idx + 1
    durum["soru_idx"] = sonraki
    kullanici_durum[user_id] = durum

    if sonraki < len(sorular):
        await soru_gonder(context, user_id, sonraki, sorular)
    else:
        # Sınav bitti — kimlik doğrulama
        durum["kimlik_bekleniyor"] = True
        kullanici_durum[user_id] = durum
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "✅ *Tüm sorular tamamlandı!*\n\n"
                "Sonucunuzu kaydetmek için kimlik doğrulaması gerekiyor.\n\n"
                "📅 Doğum tarihinizi girin (GG.AA.YYYY):"
            ),
            parse_mode="Markdown"
        )
