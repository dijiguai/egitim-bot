"""
Otomatik zamanlayıcı
- 08:00 → eğitim başlat (gruba + kişilere mesaj)
- 17:00 → eğitimi kapat (gruba kapanış mesajı)
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
    def simdi_tr():
        return datetime.now(TURKIYE_TZ).replace(tzinfo=None)
except ImportError:
    def simdi_tr():
        return datetime.utcnow() + timedelta(hours=3)


async def egitim_baslat(app):
    """08:00 — eğitimi başlat."""
    from config import GRUP_ID
    from calisanlar import tum_calisanlar
    from durum import siradaki_egitim_al, izinli_mi, aktif_egitim_set
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    simdi = simdi_tr()
    gun = simdi.weekday()
    if gun == 6:  # Pazar
        logger.info("Pazar — eğitim yok.")
        return

    egitim_id, egitim = siradaki_egitim_al()
    if not egitim:
        logger.error("Eğitim bulunamadı.")
        return

    # Aktif eğitimi kaydet
    aktif_egitim_set(egitim_id)

    bugun = simdi.strftime("%d.%m.%Y")
    gunler = ["Pazartesi","Salı","Çarşamba","Perşembe","Cuma","Cumartesi","Pazar"]

    keyboard = [[InlineKeyboardButton("▶️ Eğitime Başla", callback_data=f"egitim_baslat:{egitim_id}")]]
    markup = InlineKeyboardMarkup(keyboard)

    grup_metin = (
        f"🔔 *{gunler[gun]} {bugun} — Günün Eğitimi*\n\n"
        f"📋 *{egitim['baslik']}*\n"
        f"🏷 Tür: {egitim['tur']} · ⏱ {egitim['sure']}\n"
        f"✅ Geçme notu: 70/100\n\n"
        f"⏰ Eğitim *saat 17:00*'ye kadar açık.\n"
        f"İşe başlamadan önce tamamlayın 👇"
    )

    if GRUP_ID and GRUP_ID != 0:
        try:
            msg = await app.bot.send_message(
                chat_id=GRUP_ID, text=grup_metin,
                parse_mode="Markdown", reply_markup=markup
            )
            # Mesaj ID'sini kaydet (akşam güncellemek için)
            aktif_egitim_set(egitim_id, grup_mesaj_id=msg.message_id)
            logger.info(f"Grup mesajı gönderildi: {egitim['baslik']}")
        except Exception as e:
            logger.error(f"Grup mesajı hatası: {e}")

    # Kişisel bildirimler
    calisanlar = tum_calisanlar()
    for user_id, calisan in calisanlar.items():
        if izinli_mi(user_id, bugun):
            logger.info(f"{calisan['ad_soyad']} izinli — atlandı.")
            continue
        if not user_id or user_id <= 0:
            logger.warning(f"{calisan['ad_soyad']} icin gecerli Telegram ID yok, atlandi")
            continue
        try:
            ad = calisan['ad_soyad'].split()[0]
            await app.bot.send_message(
                chat_id=user_id,
                text=(
                    f"Gunaydin *{ad}*!\n\n"
                    f"Bugunun egitimi: *{egitim['baslik']}*\n"
                    f"Saat 17:00'ye kadar tamamlayin."
                ),
                parse_mode="Markdown", reply_markup=markup
            )
            logger.info(f"Bildirim gonderildi: {calisan['ad_soyad']}")
            await asyncio.sleep(0.3)
        except Exception as e:
            logger.warning(f"{calisan['ad_soyad']} bildirimi gonderilemedi: {e}")


async def egitim_kapat(app):
    """17:00 — eğitimi kapat, tamamlamayanları bildir."""
    from config import GRUP_ID
    from calisanlar import tum_calisanlar
    from durum import aktif_egitim_al, aktif_egitim_temizle, bugun_tamamlayanlar
    from sheets import kayitlari_getir
    from datetime import date

    durum = aktif_egitim_al()
    if not durum:
        return

    egitim_id = durum.get("egitim_id")
    bugun = date.today().strftime("%d.%m.%Y")

    # Bugün tamamlayanları bul
    tamamlayanlar = bugun_tamamlayanlar(bugun)
    calisanlar = tum_calisanlar()

    tamamlamayan = [
        c["ad_soyad"]
        for uid, c in calisanlar.items()
        if str(uid) not in tamamlayanlar
    ]

    # Gruba kapanış mesajı
    if GRUP_ID and GRUP_ID != 0:
        try:
            metin = f"🔒 *Bugünkü eğitim sona erdi.*\n\n"
            if tamamlamayan:
                metin += f"⚠️ Eğitimi tamamlamamış çalışanlar:\n"
                metin += "\n".join([f"• {ad}" for ad in tamamlamayan])
                metin += f"\n\nYönetici gerekli görürse tekrar açabilir."
            else:
                metin += "✅ Tüm çalışanlar eğitimi tamamladı, tebrikler!"

            await app.bot.send_message(
                chat_id=GRUP_ID, text=metin, parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Kapanış mesajı hatası: {e}")

    aktif_egitim_temizle()
    logger.info("Günlük eğitim kapatıldı.")


def zamanlayici_baslat(app):
    def dongu():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        while True:
            try:
                simdi = simdi_tr()
                bugun_08 = simdi.replace(hour=8, minute=0, second=0, microsecond=0)
                bugun_17 = simdi.replace(hour=17, minute=0, second=0, microsecond=0)

                # Sıradaki tetikleyiciyi bul
                tetikleyiciler = []
                if simdi < bugun_08:
                    tetikleyiciler.append((bugun_08, "ac"))
                if simdi < bugun_17:
                    tetikleyiciler.append((bugun_17, "kapat"))

                if not tetikleyiciler:
                    # Yarın 08:00
                    yarin_08 = bugun_08 + timedelta(days=1)
                    tetikleyiciler.append((yarin_08, "ac"))

                hedef_zaman, hedef_is = min(tetikleyiciler, key=lambda x: x[0])
                bekle = (hedef_zaman - simdi).total_seconds()

                logger.info(f"Sonraki: {hedef_is} @ {hedef_zaman.strftime('%d.%m.%Y %H:%M')} ({int(bekle/60)} dk sonra)")
                time.sleep(max(bekle, 1))

                if hedef_is == "ac":
                    loop.run_until_complete(egitim_baslat(app))
                else:
                    loop.run_until_complete(egitim_kapat(app))

            except Exception as e:
                logger.error(f"Zamanlayıcı hatası: {e}")
                time.sleep(60)

    threading.Thread(target=dongu, daemon=True).start()
    logger.info("Zamanlayıcı başlatıldı (08:00 aç / 17:00 kapat).")
