"""
Egitim buton ve sinav akisi — gunluk 1 hak sistemi
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

            # Gruptan basildi — bota yonlendir
            if chat and chat.type in ("group", "supergroup"):
                bot_link = f"https://t.me/{BOT_USERNAME}?start=egitim_{egitim_id}"
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text="Egitime baslamak icin asagidaki butona basin:",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("Egitime Basla", url=bot_link)
                        ]])
                    )
                except Exception as e:
                    logger.warning(f"Ozel mesaj gonderilemedi: {e}")
                    await query.answer(
                        text=f"Once @{BOT_USERNAME} ile ozel sohbet acin.",
                        show_alert=True
                    )
                return

            await egitim_baslat(update, context, user_id, egitim_id)
            return

        if data.startswith("sinav_baslat:"):
            # Drive'dan materyali okudu, şimdi sınav başlasın
            egitim_id = data.split(":", 1)[1]
            await sinav_baslat(update, context, user_id, egitim_id)
            return

        if data.startswith("cevap:"):
            p = data.split(":")
            await cevap_isle(update, context, user_id, int(p[1]), int(p[2]))
            return

    except Exception as e:
        logger.error(f"Buton hatasi: {e}", exc_info=True)
        try:
            await context.bot.send_message(chat_id=user_id, text="Bir hata olustu, tekrar deneyin.")
        except:
            pass


async def egitim_baslat(update, context, user_id, egitim_id):
    from durum import hak_var_mi, deneme_kullan, kacinci_deneme

    egitim = EGITIMLER.get(egitim_id)
    if not egitim:
        await context.bot.send_message(chat_id=user_id, text="Egitim bulunamadi.")
        return

    # Hak kontrolu
    if not hak_var_mi(user_id):
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "Bugunluk egitim hakkinizi kullandınız.\n\n"
                "Yoneticiniz ek hak tanimlarsaa tekrar girebilirsiniz."
            )
        )
        return

    # Kacinci deneme
    deneme_no = kacinci_deneme(user_id)

    # Hakki kullan
    deneme_kullan(user_id)

    # Calisani bul
    try:
        from calisanlar import calisan_bul
        calisan = calisan_bul(user_id)
    except Exception as e:
        logger.error(f"calisan_bul hatasi: {e}")
        calisan = None

    if calisan:
        drive_link = egitim.get("drive_link", "")
        deneme_txt = f" ({deneme_no}. deneme)" if deneme_no > 1 else ""

        kullanici_durum[user_id] = {
            "egitim_id": egitim_id,
            "sorular": egitim.get("sorular", []),
            "soru_idx": 0,
            "dogru_sayisi": 0,
            "kimlik_bekleniyor": False,
            "dogum_dogrulama": False,
            "kimlik_dogrulandi": True,
            "kimlik_deneme": 0,
            "deneme_no": deneme_no,
            "drive_link": drive_link,
            "egitim_baslik": egitim.get("baslik", egitim_id),
        }

        if drive_link:
            # Drive linkli eğitim: önce materyali göster, sonra sınav butonu
            metin = egitim.get("metin", "") or ""
            metin_kisim = f"\n\n{metin}" if metin else ""
            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    f"📚 *{egitim.get('baslik', 'Eğitim')}{deneme_txt}*\n\n"
                    f"Aşağıdaki butona tıklayarak eğitim materyalini inceleyin, "
                    f"ardından *Okudum, Sınava Geç* butonuna basın.{metin_kisim}"
                ),
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📖 Eğitim Materyalini Aç", url=drive_link)],
                    [InlineKeyboardButton("✅ Okudum, Sınava Geç", callback_data=f"sinav_baslat:{egitim_id}")]
                ])
            )
        else:
            # Eski akış: metin göster, soru-cevap başlat
            await context.bot.send_message(
                chat_id=user_id,
                text=egitim.get("metin", "") + f"\n\n_{egitim.get('sure','')}{deneme_txt}_",
                parse_mode="Markdown"
            )
        await soru_gonder(context, user_id, 0, egitim["sorular"])
    else:
        kullanici_durum[user_id] = {
            "egitim_id": egitim_id,
            "sorular": egitim["sorular"],
            "soru_idx": 0,
            "dogru_sayisi": 0,
            "kimlik_bekleniyor": False,
            "dogum_dogrulama": True,
            "kimlik_dogrulandi": False,
            "kimlik_deneme": 0,
            "deneme_no": deneme_no
        }
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                f"*{egitim['baslik']}* egitimine hosgeldiniz!\n\n"
                f"Baslamak icin dogum tarihinizi girin (GG.AA.YYYY):"
            ),
            parse_mode="Markdown"
        )


async def sinav_baslat(update, context, user_id, egitim_id):
    """Drive materyali okunduktan sonra sınav soruları gönder."""
    from handlers.kayit_handler import kullanici_durum
    durum = kullanici_durum.get(user_id, {})
    if durum.get("egitim_id") != egitim_id:
        # Durum yoksa yeni başlat
        await egitim_baslat(update, context, user_id, egitim_id)
        return

    sorular = durum.get("sorular", [])
    if not sorular:
        await context.bot.send_message(
            chat_id=user_id,
            text="⚠️ Bu eğitim için sınav sorusu tanımlanmamış. Eğitim tamamlandı sayıldı."
        )
        return

    # İlk soruyu gönder
    durum["soru_idx"] = 0
    durum["dogru_sayisi"] = 0
    kullanici_durum[user_id] = durum

    await context.bot.send_message(
        chat_id=user_id,
        text=f"📝 *Sınav Başlıyor* — {len(sorular)} soru, geçme notu: %{GECME_NOTU}",
        parse_mode="Markdown"
    )
    await soru_gonder(update, context, user_id)


async def soru_gonder(context, user_id, idx, sorular):
    soru_obj = sorular[idx]
    toplam = len(sorular)
    keyboard = [
        [InlineKeyboardButton(
            f"{['A','B','C','D'][i]}) {s[:50]}",
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

    if secim == dogru_idx:
        durum["dogru_sayisi"] += 1
        sonuc = "Dogru!"
    else:
        sonuc = f"Yanlis. Dogru: {harf[dogru_idx]}) {sorular[soru_idx]['secenekler'][dogru_idx]}"

    try:
        await update.callback_query.edit_message_text(
            text=(
                f"Soru {soru_idx+1}/{len(sorular)}\n\n"
                f"{sorular[soru_idx]['soru']}\n\n"
                f"{sonuc}"
            )
        )
    except Exception as e:
        logger.warning(f"Mesaj guncelleme: {e}")

    sonraki = soru_idx + 1
    durum["soru_idx"] = sonraki
    kullanici_durum[user_id] = durum

    if sonraki < len(sorular):
        await soru_gonder(context, user_id, sonraki, sorular)
    else:
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
