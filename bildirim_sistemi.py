"""
bildirim_sistemi.py
===================
Otomatik hatırlatma ve bildirim sistemi.

Zamanlamalar (scheduler.py üzerinden çağrılır):
  08:00 → egitim_baslat (mevcut)
  14:00 → tamamlamayan_hatirlat  (YENİ)
  17:00 → egitim_kapat (mevcut)
  Her Pazartesi 08:30 → haftalik_isg_ozet (YENİ)
  Her Pazartesi 09:00 → uzman_sozlesme_uyari (YENİ)
  Her Pazartesi 09:15 → zorunlu_egitim_yaklasan_uyari (YENİ)
"""

import logging
import os
from datetime import datetime, date, timedelta

logger = logging.getLogger(__name__)

ADMIN_TID = os.environ.get("ADMIN_TELEGRAM_ID", "")  # Panel admin TG ID


def _token():
    return os.environ.get("TELEGRAM_BOT_TOKEN", "")


def _gonder(chat_id: int, metin: str, parse_mode="Markdown") -> bool:
    """Telegram mesajı gönder (sync — requests üzerinden)."""
    try:
        import requests
        r = requests.post(
            f"https://api.telegram.org/bot{_token()}/sendMessage",
            json={"chat_id": chat_id, "text": metin, "parse_mode": parse_mode},
            timeout=10
        )
        return r.json().get("ok", False)
    except Exception as e:
        logger.warning(f"Mesaj gönderilemedi ({chat_id}): {e}")
        return False


# ── 1. Tamamlamayan Çalışan Hatırlatması (14:00) ───────────────
async def tamamlamayan_hatirlat(app=None):
    """
    Bugün eğitimi henüz tamamlamamış çalışanlara Telegram'dan hatırlatma gönderir.
    14:00'da çalışır, 17:00 kapanışından önce son hatırlatma.
    """
    from datetime import date as d_date
    from calisanlar import tum_calisanlar
    from sheets import tum_kayitlar_getir
    from durum import egitim_acik_mi, aktif_egitim_al, izinli_mi
    from egitimler_sheets import tum_egitimler

    if not egitim_acik_mi():
        logger.info("Hatırlatma: Aktif eğitim yok, atlandı.")
        return

    bugun_str = d_date.today().strftime("%d.%m.%Y")
    aktif = aktif_egitim_al()
    if not aktif:
        return

    egitim_id = aktif.get("egitim_id", "")
    egitimler = tum_egitimler()
    egitim = egitimler.get(egitim_id, {})
    baslik = egitim.get("baslik", "bugünün eğitimi")

    # Bugün kaydı olan çalışanlar
    try:
        kayitlar = tum_kayitlar_getir()
        bugun_kayit_tidler = {
            str(k.get("telegram_id", ""))
            for k in kayitlar
            if k.get("tarih") == bugun_str and k.get("telegram_id")
        }
    except Exception as e:
        logger.error(f"Kayıt okuma hatası: {e}")
        return

    calisanlar = tum_calisanlar()
    gonderilen = 0

    for uid, c in calisanlar.items():
        if str(uid) in bugun_kayit_tidler:
            continue  # Zaten katıldı
        if izinli_mi(uid, bugun_str):
            continue
        if not uid or uid <= 0:
            continue
        try:
            ad = c["ad_soyad"].split()[0]
            metin = (
                f"⏰ *Hatırlatma, {ad}!*\n\n"
                f"Bugünün eğitimini henüz tamamlamadın.\n"
                f"📚 *{baslik}*\n\n"
                f"Saat 17:00'ye kadar vaktın var. "
                f"Hemen başlamak için botla konuş!"
            )
            if app:
                await app.bot.send_message(
                    chat_id=uid, text=metin, parse_mode="Markdown"
                )
            else:
                _gonder(uid, metin)
            gonderilen += 1
            if app:
                import asyncio
                await asyncio.sleep(0.2)
        except Exception as e:
            logger.warning(f"Hatırlatma gönderilemedi ({c['ad_soyad']}): {e}")

    logger.info(f"Hatırlatma tamamlandı: {gonderilen} kişiye gönderildi.")


# ── 2. Haftalık ISG Özeti (Pazartesi 08:30) ────────────────────
def haftalik_isg_ozet():
    """
    Her Pazartesi adminlere / uzman Telegram ID'lerine firma bazlı haftalık özet gönderir.
    """
    if not ADMIN_TID:
        logger.info("Haftalık özet: ADMIN_TELEGRAM_ID tanımlı değil, atlandı.")
        return

    try:
        admin_id = int(ADMIN_TID)
    except:
        logger.warning("ADMIN_TELEGRAM_ID geçersiz format.")
        return

    try:
        from firma_manager import tum_firmalar
        from sheets import tum_kayitlar_getir
        from calisanlar import tum_calisanlar

        firmalar = tum_firmalar()
        bugun = date.today()
        hafta_basi = (bugun - timedelta(days=7)).strftime("%d.%m.%Y")
        hafta_sonu = bugun.strftime("%d.%m.%Y")

        satirlar = [
            f"📊 *Haftalık Eğitim Özeti*",
            f"_{hafta_basi} — {hafta_sonu}_\n",
        ]

        for firma_id, f in firmalar.items():
            try:
                kayitlar = tum_kayitlar_getir(firma_id=firma_id)
                calisanlar = tum_calisanlar(firma_id=firma_id)

                # Geçen haftanın kayıtları
                haftanin = [
                    k for k in kayitlar
                    if _tarih_araliginda(k.get("tarih",""), hafta_basi, hafta_sonu)
                ]
                gecti = [k for k in haftanin if k.get("durum","").upper() in ("GECTI","GECTİ")]
                benzersiz = len({str(k.get("telegram_id","")) for k in gecti})
                toplam_c = len(calisanlar)

                satirlar.append(
                    f"🏭 *{f.get('ad', firma_id)}*\n"
                    f"   Katılım: {len(haftanin)} · Geçti: {len(gecti)} · "
                    f"Aktif çalışan: {toplam_c}\n"
                    f"   Katılan kişi: {benzersiz}/{toplam_c}"
                )
            except Exception as e:
                satirlar.append(f"🏭 *{f.get('ad', firma_id)}* — veri alınamadı")

        _gonder(admin_id, "\n".join(satirlar))
        logger.info("Haftalık ISG özeti gönderildi.")
    except Exception as e:
        logger.error(f"Haftalık özet hatası: {e}")


# ── 3. Uzman Sözleşme Bitiş Uyarısı (Pazartesi 09:00) ─────────
def uzman_sozlesme_uyari():
    """
    Sözleşmesi 30 gün içinde bitecek uzman atamalarını kontrol eder.
    Admin'e Telegram mesajı gönderir.
    """
    if not ADMIN_TID:
        return

    try:
        admin_id = int(ADMIN_TID)
    except:
        return

    try:
        from isg.atama_gecmisi import tum_satirlar, SEKME, BASLIKLAR
        from isg.sheets_base import tum_satirlar as sheets_tum
        from firma_manager import tum_firmalar
        from isg.uzmanlar import uzman_getir

        firmalar = tum_firmalar()
        satirlar = sheets_tum(SEKME)
        bugun = date.today()
        limit = bugun + timedelta(days=30)

        yaklasanlar = []
        for s in satirlar:
            while len(s) < len(BASLIKLAR):
                s.append("")
            a = dict(zip(BASLIKLAR, s))
            if a.get("aktif") != "1":
                continue
            bitis_str = a.get("bitis_tarihi", "")
            if not bitis_str:
                continue  # Süresiz — sorun değil
            try:
                bitis = datetime.strptime(bitis_str.strip(), "%d.%m.%Y").date()
                if bugun <= bitis <= limit:
                    firma_ad = firmalar.get(a.get("firma_id",""), {}).get("ad", a.get("firma_id",""))
                    uzman = uzman_getir(a.get("uzman_id",""))
                    uzman_ad = uzman.get("ad_soyad","?") if uzman else "?"
                    kalan = (bitis - bugun).days
                    yaklasanlar.append(
                        f"• {uzman_ad} — {firma_ad} ({kalan} gün kaldı, {bitis_str})"
                    )
            except:
                pass

        if not yaklasanlar:
            logger.info("Uzman sözleşme uyarısı: Yaklaşan bitiş yok.")
            return

        metin = (
            f"⚠️ *Uzman Sözleşme Bitiş Uyarısı*\n\n"
            f"Aşağıdaki atamalar 30 gün içinde sona eriyor:\n\n"
            + "\n".join(yaklasanlar) +
            "\n\nLütfen yenileme yapın veya yeni atama oluşturun."
        )
        _gonder(admin_id, metin)
        logger.info(f"Sözleşme uyarısı gönderildi: {len(yaklasanlar)} atama.")
    except Exception as e:
        logger.error(f"Uzman sözleşme uyarı hatası: {e}")


# ── 4. Zorunlu Eğitim Yaklaşan Uyarısı (Pazartesi 09:15) ───────
def zorunlu_egitim_yaklasan_uyari():
    """
    Her Pazartesi: periyodik yenileme tarihi yaklaşan zorunlu eğitimleri tespit eder.
    Admin'e Telegram mesajı gönderir.
    """
    if not ADMIN_TID:
        return

    try:
        admin_id = int(ADMIN_TID)
    except:
        return

    try:
        from firma_manager import tum_firmalar
        from isg.firma_detay import firma_detay_getir
        from isg.zorunlu_egitim import calisan_eksik_egitimler
        from isg.personel_rapor import firma_personel_listesi

        firmalar = tum_firmalar()
        satirlar = []

        for firma_id, f in firmalar.items():
            detay = firma_detay_getir(firma_id)
            tehlike = detay.get("tehlike_sinifi", "")
            if not tehlike:
                continue

            calisanlar = firma_personel_listesi(firma_id)
            kritik_calisanlar = []

            for c in calisanlar:
                tid = c.get("telegram_id", "")
                if not tid:
                    continue
                eksikler = calisan_eksik_egitimler(tid, firma_id, tehlike)
                yaklasan = [
                    e for e in eksikler
                    if e.get("durum") == "suresi_yaklashyor"
                    and e.get("kalan_gun", 999) <= 14
                ]
                if yaklasan:
                    kritik_calisanlar.append(
                        f"  • {c['ad_soyad']}: " +
                        ", ".join(e["baslik"][:30] for e in yaklasan)
                    )

            if kritik_calisanlar:
                satirlar.append(f"🏭 *{f.get('ad', firma_id)}*")
                satirlar.extend(kritik_calisanlar)

        if not satirlar:
            logger.info("Zorunlu eğitim uyarısı: Kritik yaklaşan yok.")
            return

        metin = (
            f"📋 *Zorunlu Eğitim Yaklaşıyor (14 gün)*\n\n"
            + "\n".join(satirlar) +
            "\n\nİSG panelinden ilgili eğitimleri gönderin."
        )
        _gonder(admin_id, metin)
        logger.info(f"Zorunlu eğitim uyarısı gönderildi.")
    except Exception as e:
        logger.error(f"Zorunlu eğitim uyarı hatası: {e}")


# ── Yardımcı ────────────────────────────────────────────────────
def _tarih_araliginda(tarih_str: str, bas: str, bitis: str) -> bool:
    try:
        t = datetime.strptime(tarih_str.strip(), "%d.%m.%Y").date()
        b = datetime.strptime(bas.strip(), "%d.%m.%Y").date()
        e = datetime.strptime(bitis.strip(), "%d.%m.%Y").date()
        return b <= t <= e
    except:
        return False
