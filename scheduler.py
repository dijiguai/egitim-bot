"""
Otomatik eğitim zamanlayıcı
Her hafta içi ve Cumartesi sabah 08:00'de çalışır.
"""

import logging
import asyncio
from datetime import datetime, date
import pytz

logger = logging.getLogger(__name__)

TURKIYE_TZ = pytz.timezone("Europe/Istanbul")


async def gunluk_egitim_gonder(app):
    """
    Her sabah 08:00'de çalışır:
    1. Gruba eğitim mesajı gönderir
    2. Her aktif çalışana kişisel bildirim gönderir
    """
    from config import EGITIMLER, GRUP_ID, CALISANLAR
    from durum import siradaki_egitim_al, izinli_mi

    simdi = datetime.now(TURKIYE_TZ)
    gun = simdi.weekday()  # 0=Pzt, 5=Cmt, 6=Pzr

    # Pazar günü gönderme
    if gun == 6:
        logger.info("Pazar — eğitim gönderilmedi.")
        return

    egitim_id, egitim = siradaki_egitim_al()
    if not egitim:
        logger.error("Sıradaki eğitim bulunamadı.")
        return

    bugun = simdi.strftime("%d.%m.%Y")
    gun_adi = ["Pazartesi","Salı","Çarşamba","Perşembe","Cuma","Cumartesi","Pazar"][gun]

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = [[InlineKeyboardButton("▶️ Eğitime Başla", callback_data=f"egitim_baslat:{egitim_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    grup_metin = (
        f"🔔 *{gun_adi} {bugun} — Günün Eğitimi*\n\n"
        f"📋 *Konu:* {egitim['baslik']}\n"
        f"🏷 *Tür:* {egitim['tur']}\n"
        f"⏱ *Süre:* {egitim['sure']}\n"
        f"✅ *Geçme Notu:* 70/100\n\n"
        f"İşe başlamadan önce eğitiminizi tamamlayın. 👇"
    )

    # Gruba gönder
    try:
        await app.bot.send_message(
            chat_id=GRUP_ID,
            text=grup_metin,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        logger.info(f"Grup mesajı gönderildi: {egitim['baslik']}")
    except Exception as e:
        logger.error(f"Grup mesajı hatası: {e}")

    # Her çalışana kişisel bildirim
    for user_id, calisan in CALISANLAR.items():
        if izinli_mi(user_id, bugun):
            logger.info(f"{calisan['ad_soyad']} izinli — atlandı.")
            continue
        try:
            kisi_metin = (
                f"👷 Günaydın *{calisan['ad_soyad'].split()[0]}*!\n\n"
                f"Bugünkü eğitiminiz hazır.\n"
                f"📋 *{egitim['baslik']}*\n\n"
                f"İşe başlamadan önce tamamlamanız gerekiyor. 👇"
            )
            await app.bot.send_message(
                chat_id=user_id,
                text=kisi_metin,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
            await asyncio.sleep(0.1)  # Rate limit önlemi
        except Exception as e:
            logger.warning(f"{calisan['ad_soyad']} bildirimi gönderilemedi: {e}")

    logger.info(f"Günlük eğitim tamamlandı: {egitim['baslik']}")


def zamanlayici_baslat(app):
    """
    Arka planda çalışan zamanlayıcı thread'i başlatır.
    Her gün 08:00'i bekler, eğitimi gönderir.
    """
    import threading

    def dongu():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        while True:
            try:
                simdi = datetime.now(TURKIYE_TZ)
                # Bugün 08:00
                hedef = simdi.replace(hour=8, minute=0, second=0, microsecond=0)

                # Eğer 08:00 geçtiyse yarın 08:00'i hedefle
                if simdi >= hedef:
                    from datetime import timedelta
                    hedef = hedef + timedelta(days=1)

                bekle_sn = (hedef - simdi).total_seconds()
                logger.info(f"Sonraki eğitim: {hedef.strftime('%d.%m.%Y %H:%M')} ({int(bekle_sn/3600)}s {int((bekle_sn%3600)/60)}dk sonra)")

                import time
                time.sleep(bekle_sn)

                # 08:00 oldu — gönder
                loop.run_until_complete(gunluk_egitim_gonder(app))

            except Exception as e:
                logger.error(f"Zamanlayıcı hatası: {e}")
                import time
                time.sleep(60)  # Hata durumunda 1 dk bekle

    t = threading.Thread(target=dongu, daemon=True)
    t.start()
    logger.info("Otomatik eğitim zamanlayıcısı başlatıldı.")
