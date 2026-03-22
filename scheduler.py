"""
Otomatik zamanlayici
- 08:00 -> egitim baslat
- 17:00 -> egitimi kapat
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
    """08:00 - egitimi baslat."""
    from config import GRUP_ID
    from calisanlar import tum_calisanlar
    from durum import siradaki_egitim_al, izinli_mi, aktif_egitim_set
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    simdi = simdi_tr()
    gun = simdi.weekday()  # 0=Pzt, 6=Paz

    # Firma bazli egitim gunlerini kontrol et
    def egitim_gunu_mu(firma_id, gun_no):
        try:
            import os
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build
            creds = Credentials.from_service_account_file(
                os.environ.get("GOOGLE_CREDENTIALS_PATH","credentials.json"),
                scopes=["https://www.googleapis.com/auth/spreadsheets"])
            s = build("sheets","v4",credentials=creds).spreadsheets()
            sid = os.environ.get("SPREADSHEET_ID")
            r = s.values().get(spreadsheetId=sid, range="Ayarlar!A1:B30").execute()
            for satir in r.get("values",[]):
                if satir and satir[0].strip() == f"egitim_gunleri_{firma_id}":
                    gunler = [int(g.strip()) for g in satir[1].split(",") if g.strip().isdigit()]
                    return gun_no in gunler
        except Exception as e:
            logger.warning(f"Egitim gun kontrolu hatasi: {e}")
        # Varsayilan: Pazar haric her gun
        return gun_no != 6

    # Varsayilan firma icin gun kontrolu
    from config import GRUP_ID as DEFAULT_GRUP_ID
    if not egitim_gunu_mu("varsayilan", gun):
        logger.info(f"Bugun ({gun}) egitim gunu degil (varsayilan firma).")
        return

    egitim_id, egitim = siradaki_egitim_al()
    if not egitim:
        logger.error("Egitim bulunamadi.")
        return

    aktif_egitim_set(egitim_id)

    bugun = simdi.strftime("%d.%m.%Y")
    gunler = ["Pazartesi","Sali","Carsamba","Persembe","Cuma","Cumartesi","Pazar"]

    keyboard = [[InlineKeyboardButton("Egitime Basla", callback_data=f"egitim_baslat:{egitim_id}")]]
    markup = InlineKeyboardMarkup(keyboard)

    grup_metin = (
        f"Bugunun Egitimi — {gunler[gun]} {bugun}\n\n"
        f"{egitim['baslik']}\n"
        f"Tur: {egitim['tur']} | Sure: {egitim['sure']}\n"
        f"Gecme notu: 70/100\n\n"
        f"Egitim saat 17:00'ye kadar acik.\n"
        f"Ise baslamadan once tamamlayin"
    )

    if GRUP_ID and GRUP_ID != 0:
        try:
            msg = await app.bot.send_message(
                chat_id=GRUP_ID, text=grup_metin,
                parse_mode="Markdown", reply_markup=markup
            )
            aktif_egitim_set(egitim_id, grup_mesaj_id=msg.message_id)
            logger.info(f"Grup mesaji gonderildi: {egitim['baslik']}")
        except Exception as e:
            logger.error(f"Grup mesaji hatasi: {e}")

    calisanlar = tum_calisanlar()
    for user_id, calisan in calisanlar.items():
        if izinli_mi(user_id, bugun):
            continue
        if not user_id or user_id <= 0:
            logger.warning(f"{calisan['ad_soyad']} icin gecerli ID yok, atlandi")
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
    """17:00 - egitimi kapat, tamamlayanlar ve tamamlamayanlar Sheets'ten okunur."""
    from config import GRUP_ID
    from calisanlar import tum_calisanlar
    from durum import aktif_egitim_al, aktif_egitim_temizle
    from sheets import tum_kayitlar_getir
    from datetime import date

    bugun = date.today().strftime("%d.%m.%Y")

    # Aktif egitimin basligini al
    aktif = aktif_egitim_al()
    aktif_egitim_id = aktif.get("egitim_id") if aktif else None

    # Sheets'ten bugunun kayitlarini cek
    try:
        from config import EGITIMLER
        tum_kayitlar = tum_kayitlar_getir()
        # Sadece bugunun kayitlari VE aktif egitimin kayitlari
        if aktif_egitim_id and aktif_egitim_id in EGITIMLER:
            aktif_baslik = EGITIMLER[aktif_egitim_id].get("baslik", "")
            bugun_kayitlar = [k for k in tum_kayitlar
                if k.get("tarih") == bugun
                and k.get("egitim_konusu","") == aktif_baslik
                and k.get("kimlik_dogrulandi","") != "TOPLU"]
        else:
            bugun_kayitlar = [k for k in tum_kayitlar
                if k.get("tarih") == bugun
                and k.get("kimlik_dogrulandi","") != "TOPLU"]
    except Exception as e:
        logger.error(f"Kayit okuma hatasi: {e}")
        bugun_kayitlar = []

    calisanlar = tum_calisanlar()

    # Calisan bazi kayit haritasi
    calisan_kayit_map = {}
    for k in bugun_kayitlar:
        tid = str(k.get("telegram_id", ""))
        if tid:
            calisan_kayit_map.setdefault(tid, []).append(k)

    gecenler = []
    tamamlamayan = []

    for uid, c in calisanlar.items():
        tid_str = str(uid)
        kayitlar = calisan_kayit_map.get(tid_str, [])
        if kayitlar:
            gecti = any(k.get("durum","") in ("GECTI","GECTİ") for k in kayitlar)
            en_iyi = max((int(k.get("puan","0") or 0) for k in kayitlar), default=0)
            if gecti:
                gecenler.append(f"• {c['ad_soyad']} — {en_iyi} puan")
            else:
                tamamlamayan.append(c["ad_soyad"])
        else:
            tamamlamayan.append(c["ad_soyad"])

    if GRUP_ID and GRUP_ID != 0:
        try:
            satirlar = ["Bugunki egitim sona erdi.", ""]
            if gecenler:
                satirlar.append(f"Tamamlayanlar ({len(gecenler)}):")
                satirlar.extend(gecenler)
                satirlar.append("")
            if tamamlamayan:
                satirlar.append(f"Tamamlamayanlar ({len(tamamlamayan)}):")
                satirlar.extend([f"• {ad}" for ad in tamamlamayan])
                satirlar.append("")
                satirlar.append("Yonetici gerekli gorurse tekrar acabilir.")
            if not gecenler and not tamamlamayan:
                satirlar.append("Bugun hic katilim olmadi.")

            metin = "\n".join(satirlar)
            await app.bot.send_message(
                chat_id=GRUP_ID, text=metin
            )
            logger.info(f"Kapanis: {len(gecenler)} gecti, {len(tamamlamayan)} tamamlamadi")
        except Exception as e:
            logger.error(f"Kapanis mesaji hatasi: {e}")

    aktif_egitim_temizle()
    logger.info("Gunluk egitim kapatildi.")


def zamanlayici_baslat(app):
    def dongu():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        while True:
            try:
                simdi = simdi_tr()
                bugun_08 = simdi.replace(hour=8, minute=0, second=0, microsecond=0)
                bugun_17 = simdi.replace(hour=17, minute=0, second=0, microsecond=0)

                tetikleyiciler = []
                if simdi < bugun_08:
                    tetikleyiciler.append((bugun_08, "ac"))
                if simdi < bugun_17:
                    tetikleyiciler.append((bugun_17, "kapat"))

                if not tetikleyiciler:
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
                logger.error(f"Zamanlayici hatasi: {e}")
                time.sleep(60)

    threading.Thread(target=dongu, daemon=True).start()
    logger.info("Zamanlayici baslatildi (08:00 ac / 17:00 kapat).")
