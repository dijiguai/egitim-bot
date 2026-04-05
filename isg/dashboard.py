"""
isg/dashboard.py
================
Firma bazlı ISG uyum skoru ve özet dashboard verisi.

Uyum skoru (0-100):
  - Uzman ataması           : 25 puan
  - Uzman sınıfı uyumu      : 10 puan
  - Hekim ataması           : 15 puan
  - Eğitim süresi yeterliliği: 20 puan
  - Zorunlu eğitim uyumu    : 25 puan
  - Belgeler / SGK/NACE     :  5 puan
"""

import logging
from datetime import date, datetime

logger = logging.getLogger(__name__)


def firma_uyum_skoru(firma_id: str) -> dict:
    """
    Tek firma için tam ISG uyum analizi.
    Döner: {
        skor: int (0-100),
        seviye: str,
        renk: str,
        maddeler: [{baslik, puan, max_puan, durum, aciklama}],
        uyarilar: [str],
        oneriler: [str],
    }
    """
    maddeler = []
    uyarilar = []
    oneriler = []
    toplam_puan = 0

    # ── Firma detayını al ───────────────────────────────────────
    try:
        from isg.firma_detay import firma_detay_getir
        detay = firma_detay_getir(firma_id)
        tehlike = detay.get("tehlike_sinifi", "")
        calisan_str = detay.get("calisan_sayisi", "0")
        try:
            calisan = int(calisan_str) if calisan_str else 0
        except:
            calisan = 0
        sgk_no = detay.get("sgk_sicil_no", "")
        nace   = detay.get("nace_kodu", "")
    except Exception as e:
        logger.warning(f"Firma detay alınamadı: {e}")
        tehlike = ""
        calisan = 0
        sgk_no = nace = ""

    # ── 1. Uzman ataması (25 puan) ─────────────────────────────
    try:
        from isg.atama_gecmisi import aktif_atama_getir
        from isg.uzmanlar import uzman_getir
        from isg.sure_hesap import uzman_sinifi_kontrol

        uzman_atama = aktif_atama_getir(firma_id, "is_guvenligi_uzmani")
        if uzman_atama:
            uzman = uzman_getir(uzman_atama.get("uzman_id", ""))
            uzman_sinif = uzman.get("sinif", "") if uzman else ""
            uzman_ad    = uzman.get("ad_soyad", "?") if uzman else "?"

            # Sınıf uyumu
            if tehlike and uzman_sinif:
                sinif_ok = uzman_sinifi_kontrol(uzman_sinif, tehlike)
                if sinif_ok["yeterli"]:
                    puan = 35   # 25 + 10
                    maddeler.append({
                        "baslik": "İş Güvenliği Uzmanı",
                        "puan": 35, "max_puan": 35,
                        "durum": "ok",
                        "aciklama": f"{uzman_sinif} Sınıfı — {uzman_ad} · {uzman_atama.get('baslangic_tarihi','?')}'dan itibaren"
                    })
                    toplam_puan += 35
                else:
                    puan = 20
                    maddeler.append({
                        "baslik": "İş Güvenliği Uzmanı",
                        "puan": 20, "max_puan": 35,
                        "durum": "uyari",
                        "aciklama": f"{uzman_sinif} Sınıfı uzman bu işyeri için yetkilendirilmemiş!"
                    })
                    toplam_puan += 20
                    uyarilar.append(f"⚠️ {uzman_ad} ({uzman_sinif} Sınıfı) bu tehlike sınıfında görev yapamaz.")
            else:
                puan = 25
                maddeler.append({
                    "baslik": "İş Güvenliği Uzmanı",
                    "puan": 25, "max_puan": 35,
                    "durum": "ok",
                    "aciklama": f"{uzman_ad} atandı · Tehlike sınıfı girilmediği için sınıf uyumu kontrol edilemedi"
                })
                toplam_puan += 25
        else:
            maddeler.append({
                "baslik": "İş Güvenliği Uzmanı",
                "puan": 0, "max_puan": 35,
                "durum": "eksik",
                "aciklama": "Aktif uzman ataması yok"
            })
            uyarilar.append("🔴 İş güvenliği uzmanı atanmamış — yasal zorunluluk!")
            oneriler.append("Firma Atamaları sekmesinden uzman atayın.")
    except Exception as e:
        logger.warning(f"Uzman kontrolü hatası: {e}")
        maddeler.append({"baslik": "İş Güvenliği Uzmanı", "puan": 0, "max_puan": 35, "durum": "hata", "aciklama": str(e)})

    # ── 2. İşyeri Hekimi (15 puan) ─────────────────────────────
    try:
        from isg.atama_gecmisi import aktif_atama_getir
        hekim_atama = aktif_atama_getir(firma_id, "isyeri_hekimi")
        if hekim_atama:
            from isg.uzmanlar import uzman_getir
            hekim = uzman_getir(hekim_atama.get("uzman_id", ""))
            hekim_ad = hekim.get("ad_soyad", "?") if hekim else "?"
            maddeler.append({
                "baslik": "İşyeri Hekimi",
                "puan": 15, "max_puan": 15,
                "durum": "ok",
                "aciklama": f"{hekim_ad} · {hekim_atama.get('baslangic_tarihi','?')}'dan itibaren"
            })
            toplam_puan += 15
        else:
            maddeler.append({
                "baslik": "İşyeri Hekimi",
                "puan": 0, "max_puan": 15,
                "durum": "eksik",
                "aciklama": "Aktif işyeri hekimi ataması yok"
            })
            uyarilar.append("🔴 İşyeri hekimi atanmamış — 01.01.2025'ten itibaren tüm işyerleri zorunlu!")
            oneriler.append("Firma Atamaları sekmesinden hekim atayın.")
    except Exception as e:
        logger.warning(f"Hekim kontrolü hatası: {e}")
        maddeler.append({"baslik": "İşyeri Hekimi", "puan": 0, "max_puan": 15, "durum": "hata", "aciklama": str(e)})

    # ── 3. Yıllık eğitim süresi yeterliliği (20 puan) ──────────
    if tehlike and calisan > 0:
        try:
            from isg.sure_hesap import egitim_sure_hesapla
            from isg.personel_rapor import aylik_egitim_ozeti

            hedef = egitim_sure_hesapla(tehlike, calisan)
            hedef_saat = hedef["yillik_sure_saat"]

            ozet = aylik_egitim_ozeti(firma_id, datetime.now().year)
            gerceklesen_dk = sum(
                c.get("yillik_toplam_dk", 0)
                for c in ozet.get("calisanlar", {}).values()
            )
            gerceklesen_saat = round(gerceklesen_dk / 60, 1)
            oran = (gerceklesen_saat / hedef_saat * 100) if hedef_saat > 0 else 0

            if oran >= 100:
                puan = 20
                durum = "ok"
                aciklama = f"{gerceklesen_saat}s gerçekleşen / {hedef_saat}s hedef — %{int(oran)} tamamlandı"
            elif oran >= 50:
                puan = 10
                durum = "uyari"
                aciklama = f"{gerceklesen_saat}s gerçekleşen / {hedef_saat}s hedef — %{int(oran)} tamamlandı"
                uyarilar.append(f"⚠️ Yıllık eğitim hedefinin %{int(oran)}'i tamamlandı.")
            else:
                puan = 0
                durum = "eksik"
                aciklama = f"{gerceklesen_saat}s gerçekleşen / {hedef_saat}s hedef — %{int(oran)} tamamlandı"
                uyarilar.append(f"🔴 Yıllık eğitim hedefinin yalnızca %{int(oran)}'i tamamlandı!")

            maddeler.append({
                "baslik": "Yıllık Eğitim Süresi",
                "puan": puan, "max_puan": 20,
                "durum": durum, "aciklama": aciklama
            })
            toplam_puan += puan
        except Exception as e:
            logger.warning(f"Eğitim süresi kontrolü hatası: {e}")
            maddeler.append({"baslik": "Yıllık Eğitim Süresi", "puan": 0, "max_puan": 20, "durum": "hata", "aciklama": str(e)})
    else:
        maddeler.append({
            "baslik": "Yıllık Eğitim Süresi",
            "puan": 0, "max_puan": 20,
            "durum": "belirsiz",
            "aciklama": "Tehlike sınıfı veya çalışan sayısı girilmemiş"
        })
        oneriler.append("Süre Hesaplama sekmesinden çalışan sayısı ve tehlike sınıfını girin.")

    # ── 4. Zorunlu eğitim uyumu (25 puan) ──────────────────────
    if tehlike:
        try:
            from isg.zorunlu_egitim import firma_ozet_istatistik
            ze_ozet = firma_ozet_istatistik(firma_id, tehlike)
            toplam_c = ze_ozet.get("toplam_calisan", 0)
            tam      = ze_ozet.get("tam_uyumlu", 0)
            oran_c   = (tam / toplam_c * 100) if toplam_c > 0 else 0

            if oran_c >= 90:
                puan = 25; durum = "ok"
            elif oran_c >= 60:
                puan = 15; durum = "uyari"
                uyarilar.append(f"⚠️ Çalışanların %{int(100-oran_c)}'i zorunlu eğimlerde eksik.")
            else:
                puan = 5; durum = "eksik"
                uyarilar.append(f"🔴 Çalışanların %{int(100-oran_c)}'i zorunlu eğitimleri tamamlamamış!")

            maddeler.append({
                "baslik": "Zorunlu Eğitim Uyumu",
                "puan": puan, "max_puan": 25,
                "durum": durum,
                "aciklama": f"{tam}/{toplam_c} çalışan tam uyumlu (%{int(oran_c)})"
            })
            toplam_puan += puan
        except Exception as e:
            logger.warning(f"Zorunlu eğitim kontrolü hatası: {e}")
            maddeler.append({"baslik": "Zorunlu Eğitim Uyumu", "puan": 0, "max_puan": 25, "durum": "hata", "aciklama": str(e)})
    else:
        maddeler.append({
            "baslik": "Zorunlu Eğitim Uyumu",
            "puan": 0, "max_puan": 25,
            "durum": "belirsiz",
            "aciklama": "Tehlike sınıfı girilmemiş"
        })

    # ── 5. Belgeler / SGK-NACE (5 puan) ────────────────────────
    belge_puan = 0
    belge_aciklama_parts = []
    if sgk_no:
        belge_puan += 3
        belge_aciklama_parts.append("SGK no ✓")
    else:
        oneriler.append("Firma ISG Detayı sekmesinden SGK sicil numarasını girin.")
    if nace:
        belge_puan += 2
        belge_aciklama_parts.append("NACE kodu ✓")
    else:
        oneriler.append("NACE kodunu girin — tehlike sınıfı tespiti için gerekli.")

    maddeler.append({
        "baslik": "Belgeler & Kayıt",
        "puan": belge_puan, "max_puan": 5,
        "durum": "ok" if belge_puan == 5 else ("uyari" if belge_puan > 0 else "eksik"),
        "aciklama": ", ".join(belge_aciklama_parts) if belge_aciklama_parts else "SGK no ve NACE kodu girilmemiş"
    })
    toplam_puan += belge_puan

    # ── Seviye belirleme ────────────────────────────────────────
    if toplam_puan >= 90:
        seviye = "Mükemmel"; renk = "#27a86e"
    elif toplam_puan >= 70:
        seviye = "İyi"; renk = "#2e7de8"
    elif toplam_puan >= 50:
        seviye = "Orta"; renk = "#e8b82e"
    elif toplam_puan >= 30:
        seviye = "Zayıf"; renk = "#e85c2e"
    else:
        seviye = "Kritik"; renk = "#e83a2e"

    return {
        "firma_id":    firma_id,
        "skor":        toplam_puan,
        "max_skor":    100,
        "seviye":      seviye,
        "renk":        renk,
        "tehlike":     tehlike,
        "calisan":     calisan,
        "maddeler":    maddeler,
        "uyarilar":    uyarilar,
        "oneriler":    oneriler,
        "hesap_tarihi": datetime.now().strftime("%d.%m.%Y %H:%M"),
    }


def tum_firmalar_dashboard() -> list:
    """
    Uzmanın atandığı tüm firmaların uyum skorlarını döner.
    """
    try:
        from firma_manager import tum_firmalar
        firmalar = tum_firmalar()
    except Exception as e:
        logger.error(f"Firmalar alınamadı: {e}")
        return []

    sonuc = []
    for firma_id, f in firmalar.items():
        try:
            ozet = firma_uyum_skoru(firma_id)
            sonuc.append({
                "firma_id":  firma_id,
                "firma_ad":  f.get("ad", firma_id),
                "skor":      ozet["skor"],
                "seviye":    ozet["seviye"],
                "renk":      ozet["renk"],
                "tehlike":   ozet["tehlike"],
                "calisan":   ozet["calisan"],
                "uyari_sayisi": len(ozet["uyarilar"]),
            })
        except Exception as e:
            logger.warning(f"Firma {firma_id} skoru hesaplanamadı: {e}")

    sonuc.sort(key=lambda x: x["skor"])   # En düşük skor üstte
    return sonuc
