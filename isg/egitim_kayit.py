"""
isg/egitim_kayit.py
====================
ISG zorunlu eğitim tamamlama kayıtları.
Sheets: ISG_EgitimKayitlari

Sütunlar:
  kayit_id | telegram_id | ad_soyad | egitim_id | egitim_baslik |
  tarih | puan | gecti | deneme_no | firma_id |
  drive_link | imzali_belge_link | imzali_belge_tarih
"""

import uuid, logging
from datetime import datetime
from isg.sheets_base import sekme_olustur, satir_ekle, tum_satirlar

logger = logging.getLogger(__name__)

SEKME = "ISG_EgitimKayitlari"
BASLIKLAR = [
    "kayit_id", "telegram_id", "ad_soyad", "egitim_id", "egitim_baslik",
    "tarih", "puan", "gecti", "deneme_no", "firma_id",
    "drive_link", "imzali_belge_link", "imzali_belge_tarih"
]


def _hazirla():
    sekme_olustur(SEKME, BASLIKLAR)


def kayit_ekle(telegram_id: str, ad_soyad: str, egitim_id: str,
               egitim_baslik: str, puan: int, gecti: bool,
               deneme_no: int, firma_id: str,
               drive_link: str = "") -> str:
    """Eğitim tamamlama kaydı ekler. kayit_id döner."""
    _hazirla()
    kayit_id = str(uuid.uuid4())[:8]
    tarih = datetime.now().strftime("%d.%m.%Y %H:%M")
    satir_ekle(SEKME, [
        kayit_id, str(telegram_id), ad_soyad, egitim_id, egitim_baslik,
        tarih, str(puan), "1" if gecti else "0", str(deneme_no), firma_id,
        drive_link, "", ""
    ])
    return kayit_id


def imzali_belge_guncelle(kayit_id: str, belge_link: str) -> bool:
    """Belirli kayda imzalı belge linki ekler."""
    try:
        satirlar = tum_satirlar(SEKME)
        for i, satir in enumerate(satirlar):
            if satir and satir[0] == kayit_id:
                from isg.sheets_base import satir_guncelle
                satir = list(satir) + [""] * (len(BASLIKLAR) - len(satir))
                satir[11] = belge_link
                satir[12] = datetime.now().strftime("%d.%m.%Y")
                satir_guncelle(SEKME, i + 2, satir)
                return True
        return False
    except Exception as e:
        logger.error(f"İmzalı belge güncelleme hatası: {e}")
        return False


def calisan_kayitlari(telegram_id: str, firma_id: str = "") -> list:
    """Çalışanın tüm ISG eğitim kayıtlarını döner."""
    try:
        tum = tum_satirlar(SEKME)
        sonuc = []
        for satir in tum:
            if len(satir) < 2:
                continue
            if str(satir[1]) != str(telegram_id):
                continue
            if firma_id and len(satir) > 9 and satir[9] != firma_id:
                continue
            sonuc.append({
                "kayit_id":          satir[0] if len(satir) > 0 else "",
                "telegram_id":       satir[1] if len(satir) > 1 else "",
                "ad_soyad":          satir[2] if len(satir) > 2 else "",
                "egitim_id":         satir[3] if len(satir) > 3 else "",
                "egitim_baslik":     satir[4] if len(satir) > 4 else "",
                "tarih":             satir[5] if len(satir) > 5 else "",
                "puan":              int(satir[6]) if len(satir) > 6 and satir[6].isdigit() else 0,
                "gecti":             satir[7] == "1" if len(satir) > 7 else False,
                "deneme_no":         int(satir[8]) if len(satir) > 8 and satir[8].isdigit() else 1,
                "firma_id":          satir[9] if len(satir) > 9 else "",
                "drive_link":        satir[10] if len(satir) > 10 else "",
                "imzali_belge_link": satir[11] if len(satir) > 11 else "",
                "imzali_belge_tarih":satir[12] if len(satir) > 12 else "",
            })
        return sorted(sonuc, key=lambda x: x["tarih"], reverse=True)
    except Exception as e:
        logger.error(f"Çalışan kayıtları hatası: {e}")
        return []


def egitim_son_kayit(telegram_id: str, egitim_id: str, firma_id: str = "") -> dict | None:
    """Çalışanın belirli eğitimdeki son başarılı kaydını döner."""
    kayitlar = calisan_kayitlari(telegram_id, firma_id)
    basarili = [k for k in kayitlar if k["egitim_id"] == egitim_id and k["gecti"]]
    return basarili[0] if basarili else None


def firma_egitim_ozeti(firma_id: str) -> dict:
    """Firma çalışanlarının eğitim durumu özeti."""
    try:
        tum = tum_satirlar(SEKME)
        ozet = {}  # {egitim_id: {baslik, alan_ids: set, gecen_ids: set}}
        for satir in tum:
            if len(satir) < 10 or satir[9] != firma_id:
                continue
            eid = satir[3] if len(satir) > 3 else ""
            baslik = satir[4] if len(satir) > 4 else ""
            tid = satir[1] if len(satir) > 1 else ""
            gecti = satir[7] == "1" if len(satir) > 7 else False
            if not eid:
                continue
            if eid not in ozet:
                ozet[eid] = {"baslik": baslik, "alan_ids": set(), "gecen_ids": set()}
            ozet[eid]["alan_ids"].add(tid)
            if gecti:
                ozet[eid]["gecen_ids"].add(tid)
        # Convert sets to counts for JSON serialization
        return {eid: {
            "baslik": v["baslik"],
            "alan": len(v["alan_ids"]),
            "gecen": len(v["gecen_ids"]),
            "alan_ids": list(v["alan_ids"]),
            "gecen_ids": list(v["gecen_ids"]),
        } for eid, v in ozet.items()}
    except Exception as e:
        logger.error(f"Firma eğitim özeti hatası: {e}")
        return {}
