"""
E�itim buton ve sınav akışı
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import EGITIMLER, GECME_NOTU
from handlers.kayit_handler import kullanici_durum

logger = logging.getLogger(__name__)


async def buton_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    try:
        if data.startswith("uye_ekle:"):
            from handlers.kayit_handler import uye_ekle_callback
            await uye_ekle_callback(update, context, int(data.split(":")[1]))
            return

        if data.startswith("uye_yoksay:"):
            from handlers.kayit_handler import uye_yoksay_callback
            await uye_yoksay_callback(update, context, int(data.split(":")[1]))
            return

        if data.startswith("egitim_baslat:"):
            egitim_id = data.split(":")[1]
            await egitim_baslat(update, context, user_id, egitim_id)
            return

        if data.startswith("cevap:"):
            parcalar = data.split(":")
            await cevap_isle(update, context, user_id, int(parcalar[1]), int(parcalar[2]))
            return

    except Exception as e:
        logger.error(f"Buton handler hatası: {e}", exc_info=True)
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="⚠️ Bir hata oluştu, lütfen tekrar deneyin."
            )
        except:
            pass


async def egitim_baslat(update, context, user_id, egitim_id):
    egitim = EGITIMLER.get(egitim_id)
    if not egitim:
        await context.bot.send_message(chat_id=user_id, text="❌ Eğitim bulunamadı.")
        return

    # Çalışanı bul — hata olursa yine de devam et
    try:
        from calisanlar import calisan_bul
        calisan = calisan_bul(user_id)
    except Exception as e:
        logger.error(f"calisan_bul hatası: {e}")
        calisan = None

    if not calisan:
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "⛔ Sisteme kayıtlı değilsiniz.\n\n"
                "Yöneticinizden sizi panelden eklemesini isteyin."
            )
        )
        return

    # Zaten aktif sınavı var mı?
    mevcut = kullanici_durum.get(user_id, {})
    if mevcut.get("egitim_id") and not mevcut.get("kimlik_bekleniyor"):
        await context.bot.send_message(
            chat_id=user_id,
            text="⚠️ Devam eden bir sınavınız var. Lütfen tamamlayın."
        )
        return

    # Sınavı başlat
    kullanici_durum[user_id] = {
        "egitim_id": egitim_id,
        "sorular": egitim["sorular"],
        "soru_idx": 0,
        "dogru_sayisi": 0,
        "kimlik_bekleniyor": False,
        "kimlik_dogrulandi": False,
        "kimlik_deneme": 0
    }

    await context.bot.send_message(
        chat_id=user_id,
        text=egitim["metin"],
        parse_mode="Markdown"
    )

    await soru_gonder(context, user_id, 0, egitim["sorular"])


async def soru_gonder(context, user_id, idx, sorular):
    soru_obj = sorular[idx]
    keyboard = [
        [InlineKeyboardButton(
            f"{['A','B','C','D'][i]}) {s}",
            callback_data=f"cevap:{idx}:{i}"
        )]
        for i, s in enumerate(soru_obj["secenekler"])
    ]
    await context.bot.send_message(
        chat_id=user_id,
        text=f"❓ *Soru {idx+1}/{len(sorular)}*\n\n{soru_obj['soru']}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def cevap_isle(update, context, user_id, soru_idx, secim):
    durum = kullanici_durum.get(user_id)
    if not durum:
        await context.bot.send_message(chat_id=user_id, text="❌ Oturum sona erdi. Tekrar başlayın.")
        return

    if soru_idx != durum["soru_idx"]:
        return

    sorular = durum["sorular"]
    dogru = sorular[soru_idx]["dogru"]
    harf = ["A", "B", "C", "D"]

    if secim == dogru:
        durum["dogru_sayisi"] += 1
        geri = "✅ *Doğru!*"
    else:
        geri = f"❌ *Yanlış.* Doğru cevap: {harf[dogru]}) {sorular[soru_idx]['secenekler'][dogru]}"

    try:
        await update.callback_query.edit_message_text(
            f"{geri}\n\n_{update.callback_query.message.text}_",
            parse_mode="Markdown"
        )
    except:
        pass

    sonraki = soru_idx + 1
    durum["soru_idx"] = sonraki
    kullanici_durum[user_id] = durum

    if sonraki < len(sorular):
        await soru_gonder(context, user_id, sonraki, sorular)
    else:
        durum["kimlik_bekleniyor"] = True
        kullanici_durum[user_id] = durum
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "✅ *Tüm sorular tamamlandı!*\n\n"
                "Sonucunuzu kaydetmek için kimlik doğrulaması gerekiyor.\n\n"
                "📅 Doğum tarihinizi girin *(GG.AA.YYYY)*:"
            ),
            parse_mode="Markdown"
        )
