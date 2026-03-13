"""
Egitim buton ve sinav akisi
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import EGITIMLER, GECME_NOTU, BOT_USERNAME
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
            chat = update.effective_chat

            # Grup'tan basildi — bota yonlendir
            if chat and chat.type in ("group", "supergroup"):
                bot_link = f"https://t.me/{BOT_USERNAME}?start=egitim_{egitim_id}"
                keyboard = [[InlineKeyboardButton(
                    "Egitimi Baslat", url=bot_link
                )]]
                await query.edit_message_reply_markup(
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                await context.bot.send_message(
                    chat_id=user_id,
                    text=(
                        "Egitimi baslatmak icin asagidaki butona basin:\n"
                        "Bot size ozel mesaj gonderecektir."
                    ),
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("Egitimi Baslat", url=bot_link)
                    ]])
                )
                return

            # Ozel mesajdan basildi
            await egitim_baslat(update, context, user_id, egitim_id)
            return

        if data.startswith("cevap:"):
            p = data.split(":")
            await cevap_isle(update, context, user_id, int(p[1]), int(p[2]))
            return

    except Exception as e:
        logger.error(f"Buton hatasi: {e}", exc_info=True)
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="Bir hata olustu, tekrar deneyin."
            )
        except:
            pass


async def egitim_baslat(update, context, user_id, egitim_id):
    egitim = EGITIMLER.get(egitim_id)
    if not egitim:
        await context.bot.send_message(chat_id=user_id, text="Egitim bulunamadi.")
        return

    # Calisani bul
    try:
        from calisanlar import calisan_bul
        calisan = calisan_bul(user_id)
    except Exception as e:
        logger.error(f"calisan_bul hatasi: {e}")
        calisan = None

    if calisan:
        # Kayitli — direkt sinavi baslat
        kullanici_durum[user_id] = {
            "egitim_id": egitim_id,
            "sorular": egitim["sorular"],
            "soru_idx": 0,
            "dogru_sayisi": 0,
            "kimlik_bekleniyor": False,
            "dogum_dogrulama": False,
            "kimlik_dogrulandi": True,
            "kimlik_deneme": 0
        }
        await context.bot.send_message(
            chat_id=user_id,
            text=egitim["metin"],
            parse_mode="Markdown"
        )
        await soru_gonder(context, user_id, 0, egitim["sorular"])
    else:
        # Kayitli degil — dogum tarihi sor
        kullanici_durum[user_id] = {
            "egitim_id": egitim_id,
            "sorular": egitim["sorular"],
            "soru_idx": 0,
            "dogru_sayisi": 0,
            "kimlik_bekleniyor": False,
            "dogum_dogrulama": True,
            "kimlik_dogrulandi": False,
            "kimlik_deneme": 0
        }
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                f"*{egitim['baslik']}* egitimine hosgeldiniz!\n\n"
                f"Baslamak icin dogum tarihinizi girin (GG.AA.YYYY):"
            ),
            parse_mode="Markdown"
        )


async def soru_gonder(context, user_id, idx, sorular):
    """Soruyu butonlarla tek mesajda goster."""
    soru_obj = sorular[idx]
    toplam = len(sorular)

    # Soru metni + secenekler tek mesajda
    secenekler_metni = "\n".join([
        f"{['A','B','C','D'][i]}) {s}"
        for i, s in enumerate(soru_obj["secenekler"])
    ])

    keyboard = [
        [InlineKeyboardButton(
            f"{['A','B','C','D'][i]}) {s[:40]}",
            callback_data=f"cevap:{idx}:{i}"
        )]
        for i, s in enumerate(soru_obj["secenekler"])
    ]

    await context.bot.send_message(
        chat_id=user_id,
        text=f"Soru {idx+1}/{toplam}\n\n{soru_obj['soru']}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def cevap_isle(update, context, user_id, soru_idx, secim):
    durum = kullanici_durum.get(user_id)
    if not durum or soru_idx != durum["soru_idx"]:
        return

    sorular = durum["sorular"]
    dogru_idx = sorular[soru_idx]["dogru"]
    harf = ["A", "B", "C", "D"]
    secenekler = sorular[soru_idx]["secenekler"]

    if secim == dogru_idx:
        durum["dogru_sayisi"] += 1
        sonuc = "Dogru!"
    else:
        sonuc = f"Yanlis. Dogru: {harf[dogru_idx]}) {secenekler[dogru_idx]}"

    # Mevcut soruyu guncelle — butonlari kaldir, sonucu goster
    toplam = len(sorular)
    try:
        await update.callback_query.edit_message_text(
            text=(
                f"Soru {soru_idx+1}/{toplam}\n\n"
                f"{sorular[soru_idx]['soru']}\n\n"
                f"{sonuc}"
            )
        )
    except Exception as e:
        logger.warning(f"Mesaj guncelleme hatasi: {e}")

    sonraki = soru_idx + 1
    durum["soru_idx"] = sonraki
    kullanici_durum[user_id] = durum

    if sonraki < toplam:
        # Bir sonraki soruyu gonder
        await soru_gonder(context, user_id, sonraki, sorular)
    else:
        # Sinav bitti
        if durum.get("kimlik_dogrulandi"):
            from handlers.kayit_handler import sinav_tamamla_direkt
            await sinav_tamamla_direkt(context, user_id, durum)
        else:
            durum["kimlik_bekleniyor"] = True
            kullanici_durum[user_id] = durum
            await context.bot.send_message(
                chat_id=user_id,
                text="Tum sorular tamamlandi!\n\nSonucunuzu kaydetmek icin dogum tarihinizi girin (GG.AA.YYYY):"
            )
