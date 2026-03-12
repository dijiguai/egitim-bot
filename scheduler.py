"""
Otomatik eğitim zamanlayıcı — Her hafta içi ve Cumartesi 08:00
"""

import logging
import asyncio
import time
import threading
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

try:
    import pytz
    TURKIYE_TZ = pytz.timezone("Europe/Istanbul")
except ImportError:
    TURKIYE_TZ = None
    logger.warning("pytz yüklü değil, UTC+3 manuel hesaplanacak")


def simdi_tr():
    if TURKIYE_TZ:
        return datetime.now(TURKIYE_TZ).replace(tzinfo=None)
    return datetime.utcnow() + timedelta(hours=3)


async def gunluk_egitim_gonder(app):
    from config import EGITIMLER, GRUP_ID, CALISANLAR
    from durum import siradaki_egitim_al, izinli_mi
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    simdi = simdi_tr()
    gun = simdi.weekday()  # 0=Pzt, 6=Pzr

    if gun == 6:
        logger.info("Pazar — eğitim gönderilmedi.")
        return

    egitim_id, egitim = siradaki_egitim_al()
    if not egitim:
        logger.error("Eğitim bulunamadı.")
        return

    bugun = simdi.strftime("%d.%m.%Y")
    gunler = ["Pazartesi","Salı","Çarşamba","Perşembe","Cuma","Cumartesi","Pazar"]

    keyboard = [[InlineKeyboardButton("▶️ Eğitime Başla", callback_data=f"egitim_baslat:{egitim_id}")]]
    markup = InlineKeyboardMarkup(keyboard)

    grup_metin = (
        f"🔔 *{gunler[gun]} {bugun} — Günün Eğitimi*\n\n"
        f"📋 *Konu:* {egitim['baslik']}\n"
        f"🏷 *Tür:* {egitim['tur']}\n"
        f"⏱ *Süre:* {egitim['sure']}\n"
        f"✅ *Geçme Notu:* 70/100\n\n"
        f"İşe başlamadan önce eğitiminizi tamamlayın 👇"
    )

    if GRUP_ID and GRUP_ID != 0:
        try:
            await app.bot.send_message(chat_id=GRUP_ID, text=grup_metin,
                                        parse_mode="Markdown", reply_markup=markup)
            logger.info(f"Grup mesajı gönderildi: {egitim['baslik']}")
        except Exception as e:
            logger.error(f"Grup mesajı hatası: {e}")

    for user_id, calisan in CALISANLAR.items():
        if izinli_mi(user_id, bugun):
            logger.info(f"{calisan['ad_soyad']} izinli — atlandı.")
            continue
        try:
            ad = calisan['ad_soyad'].split()[0]
            kisi_metin = (
                f"👷 Günaydın *{ad}*!\n\n"
                f"Bugünkü eğitiminiz hazır:\n"
                f"📋 *{egitim['baslik']}*\n\n"
                f"İşe başlamadan önce tamamlamanız gerekiyor 👇"
            )
            await app.bot.send_message(chat_id=user_id, text=kisi_metin,
                                        parse_mode="Markdown", reply_markup=markup)
            await asyncio.sleep(0.1)
        except Exception as e:
            logger.warning(f"{calisan['ad_soyad']} bildirimi gönderilemedi: {e}")

    logger.info("Günlük eğitim tamamlandı.")


def zamanlayici_baslat(app):
    def dongu():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        while True:
            try:
                simdi = simdi_tr()
                hedef = simdi.replace(hour=8, minute=0, second=0, microsecond=0)
                if simdi >= hedef:
                    hedef += timedelta(days=1)
                bekle = (hedef - simdi).total_seconds()
                logger.info(f"Sonraki eğitim: {hedef.strftime('%d.%m.%Y %H:%M')} ({int(bekle/3600)}s {int((bekle%3600)/60)}dk sonra)")
                time.sleep(bekle)
                loop.run_until_complete(gunluk_egitim_gonder(app))
            except Exception as e:
                logger.error(f"Zamanlayıcı hatası: {e}")
                time.sleep(60)

    threading.Thread(target=dongu, daemon=True).start()
    logger.info("Otomatik zamanlayıcı başlatıldı.")
