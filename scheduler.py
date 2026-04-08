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
    from durum import siradaki_egitim_al, izinli_mi, aktif_egitim_set, egitim_acik_mi
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    # Deploy sonrasi tekrar gonderimi onle: bugun zaten gonderildiyse cik
    if egitim_acik_mi():
        logger.info("Bugun zaten egitim gonderilmis, tekrar gonderilmiyor.")
        return

    simdi = simdi_tr()
    gun = simdi.weekday()  # 0=Pzt, 6=Paz

    # Firma bazli egitim gunlerini kontrol et
    def egitim_gunu_mu(firma_id, gun_no):
        try:
            from sheets import _servis
            s, sid = _servis()
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

        # Haftalık bildirimlerin bugün gönderilip gönderilmediğini takip et
        son_haftalik_gun = None

        while True:
            try:
                simdi = simdi_tr()
                bugun_08 = simdi.replace(hour=8,  minute=0,  second=0, microsecond=0)
                bugun_14 = simdi.replace(hour=14, minute=0,  second=0, microsecond=0)
                bugun_17 = simdi.replace(hour=17, minute=0,  second=0, microsecond=0)
                # Haftalık: Pazartesi 08:30, 09:00, 09:15
                bugun_0830 = simdi.replace(hour=8,  minute=30, second=0, microsecond=0)
                bugun_0900 = simdi.replace(hour=9,  minute=0,  second=0, microsecond=0)
                bugun_0915 = simdi.replace(hour=9,  minute=15, second=0, microsecond=0)

                tetikleyiciler = []
                if simdi < bugun_08:
                    tetikleyiciler.append((bugun_08, "ac"))
                if simdi < bugun_14:
                    tetikleyiciler.append((bugun_14, "hatirlat"))
                if simdi < bugun_17:
                    tetikleyiciler.append((bugun_17, "kapat"))
                # Pazartesi bildirimleri
                if simdi.weekday() == 0 and son_haftalik_gun != simdi.date():
                    if simdi < bugun_0830:
                        tetikleyiciler.append((bugun_0830, "haftalik_ozet"))
                    if simdi < bugun_0900:
                        tetikleyiciler.append((bugun_0900, "sozlesme_uyari"))
                    if simdi < bugun_0915:
                        tetikleyiciler.append((bugun_0915, "zorunlu_uyari"))

                if not tetikleyiciler:
                    yarin_08 = bugun_08 + timedelta(days=1)
                    tetikleyiciler.append((yarin_08, "ac"))

                hedef_zaman, hedef_is = min(tetikleyiciler, key=lambda x: x[0])
                bekle = (hedef_zaman - simdi).total_seconds()

                logger.info(f"Sonraki: {hedef_is} @ {hedef_zaman.strftime('%d.%m.%Y %H:%M')} ({int(bekle/60)} dk sonra)")
                time.sleep(max(bekle, 1))

                if hedef_is == "ac":
                    loop.run_until_complete(egitim_baslat(app))
                elif hedef_is == "kapat":
                    loop.run_until_complete(egitim_kapat(app))
                elif hedef_is == "hatirlat":
                    try:
                        from bildirim_sistemi import tamamlamayan_hatirlat
                        n = loop.run_until_complete(tamamlamayan_hatirlat(app))
                        logger.info(f"14:00 hatırlatma: {n} kişiye gönderildi")
                    except Exception as e:
                        logger.error(f"Hatirlatma hatasi: {e}")
                elif hedef_is == "haftalik_ozet":
                    try:
                        from isg.hatirlatmalar import haftalik_egitim_ozeti
                        n = loop.run_until_complete(haftalik_egitim_ozeti(app))
                        logger.info(f"Haftalik ozet: {n} mesaj gonderildi")
                        son_haftalik_gun = simdi.date()
                    except Exception as e:
                        logger.error(f"Haftalik ozet hatasi: {e}")
                elif hedef_is == "sozlesme_uyari":
                    try:
                        from isg.hatirlatmalar import uzman_sozlesme_uyarisi
                        n = loop.run_until_complete(uzman_sozlesme_uyarisi(app))
                        logger.info(f"Sozlesme uyarisi: {n} mesaj gonderildi")
                    except Exception as e:
                        logger.error(f"Sozlesme uyari hatasi: {e}")
                elif hedef_is == "zorunlu_uyari":
                    try:
                        from isg.hatirlatmalar import aylik_zorunlu_kontrol
                        n = loop.run_until_complete(aylik_zorunlu_kontrol(app))
                        logger.info(f"Zorunlu egitim uyarisi: {n} mesaj gonderildi")
                    except Exception as e:
                        logger.error(f"Zorunlu egitim uyari hatasi: {e}")

            except Exception as e:
                logger.error(f"Zamanlayici hatasi: {e}")
                time.sleep(60)

    threading.Thread(target=dongu, daemon=True).start()
    logger.info("Zamanlayici baslatildi (08:00 ac / 14:00 hatirlat / 17:00 kapat / Pzt haftalik).")
