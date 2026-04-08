"""
isg/personel_rapor.py
=====================
Firmaya ait çalışanların eğitim kayıtlarını aylık bazda özetler.

Sheets'ten okunan kayıt sütunları (sheets.py SUTUNLAR):
  tarih | saat | ad_soyad | telegram_id | gorev |
  egitim_konusu | egitim_turu | puan | durum | kimlik_dogrulandi |
  dogum_yili | deneme_no

'sure' sütunu egitimler_sheets.py'den (Egitimler sekmesi) alınır.
"""

import logging
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)


def _egitim_sure_dk(egitim_id: str, egitim_konusu: str) -> int:
    """
    Eğitimin süresini dakika cinsinden döner.
    Önce Sheets'teki Egitimler sekmesinden bakar, bulamazsa 60 dk varsayar.
    """
    try:
        from egitimler_sheets import tum_egitimler
        egitimler = tum_egitimler()
        # egitim_id ile bul
        for eid, e in egitimler.items():
            if eid == egitim_id:
                sure_str = str(e.get("sure", "60")).strip()
                try:
                    return int(sure_str)
                except:
                    return 60
        # Başlık ile bul (egitim_id yoksa)
        for eid, e in egitimler.items():
            if e.get("baslik", "").lower() == egitim_konusu.lower():
                try:
                    return int(str(e.get("sure", "60")).strip())
                except:
                    return 60
    except Exception as ex:
        logger.warning(f"Eğitim süresi alınamadı ({egitim_konusu}): {ex}")
    return 60  # varsayılan: 60 dakika


def _tarih_ay(tarih_str: str) -> str:
    """'DD.MM.YYYY' → 'YYYY-MM' (sıralama için)"""
    try:
        dt = datetime.strptime(tarih_str.strip(), "%d.%m.%Y")
        return dt.strftime("%Y-%m")
    except:
        return "0000-00"


def _tarih_ay_etiket(ay_kodu: str) -> str:
    """'2025-03' → 'Mart 2025'"""
    aylar = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
             "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
    try:
        yil, ay = ay_kodu.split("-")
        return f"{aylar[int(ay)]} {yil}"
    except:
        return ay_kodu


def firma_personel_listesi(firma_id: str) -> list:
    """
    Firmaya ait aktif çalışanları döner.
    [{telegram_id, ad_soyad, gorev, aktif}, ...]
    Firma'ya özgü sekme yoksa varsayılan 'Calisanlar' sekmesine düşer.
    """
    try:
        from calisanlar import tum_calisanlar
        calisanlar = tum_calisanlar(firma_id=firma_id)
        # Boş gelirse varsayılan firma ile dene
        if not calisanlar:
            calisanlar = tum_calisanlar(firma_id="varsayilan")
        return [
            {
                "telegram_id": str(c.get("telegram_id", "")),
                "ad_soyad": c.get("ad_soyad", ""),
                "gorev": c.get("gorev", ""),
                "aktif": c.get("aktif", "1") not in ("0", "false", "False", ""),
            }
            for c in calisanlar
            if c.get("aktif", "1") not in ("0", "false", "False")
               and not c.get("arsiv")
        ]
    except Exception as e:
        logger.error(f"Personel listesi alınamadı ({firma_id}): {e}")
        return []


def aylik_egitim_ozeti(firma_id: str, yil: int = None) -> dict:
    """
    Firmanın eğitim kayıtlarını aylık bazda özetler.

    Döner:
    {
      "aylar": ["2025-01", "2025-02", ...],   # sıralı
      "calisanlar": {
        "telegram_id": {
          "ad_soyad": str,
          "gorev": str,
          "aylar": {
            "2025-01": {
              "toplam_dk": int,
              "toplam_saat": float,
              "egitimler": [
                {"konu": str, "tur": str, "sure_dk": int, "durum": str}
              ]
            }
          },
          "yillik_toplam_dk": int,
          "yillik_toplam_saat": float,
          "egitim_sayisi": int,
        }
      },
      "firma_ozet": {
        "ay": {"toplam_dk": int, "calisan_sayisi": int}
      }
    }
    """
    hedef_yil = yil or datetime.now().year

    # Kayıtları oku
    try:
        from sheets import tum_kayitlar
        kayitlar = tum_kayitlar(firma_id=firma_id)
    except Exception as e:
        logger.error(f"Kayıt okunamadı: {e}")
        return {"aylar": [], "calisanlar": {}, "firma_ozet": {}}

    # Aktif çalışan listesi
    personel_map = {p["telegram_id"]: p for p in firma_personel_listesi(firma_id)}

    # Eğitim süresi önbelleği
    sure_cache = {}

    ozet = defaultdict(lambda: {
        "ad_soyad": "", "gorev": "",
        "aylar": defaultdict(lambda: {"toplam_dk": 0, "egitimler": []}),
        "yillik_toplam_dk": 0, "egitim_sayisi": 0
    })

    tum_aylar = set()

    for k in kayitlar:
        # Sadece geçen / tamamlanan kayıtlar ve hedef yıl
        tarih = k.get("tarih", "")
        ay = _tarih_ay(tarih)
        if not ay.startswith(str(hedef_yil)):
            continue
        # Sadece geçti / bitti
        durum = k.get("durum", "").upper()
        if durum not in ("GECTI", "GECTİ", "TAMAMLANDI", "PASSED"):
            continue

        tid = str(k.get("telegram_id", "")).strip()
        konu = k.get("egitim_konusu", "")
        tur = k.get("egitim_turu", "")

        # Süre
        cache_key = konu
        if cache_key not in sure_cache:
            sure_cache[cache_key] = _egitim_sure_dk("", konu)
        sure_dk = sure_cache[cache_key]

        # Çalışan bilgisi
        if tid not in ozet:
            p = personel_map.get(tid, {})
            ozet[tid]["ad_soyad"] = p.get("ad_soyad", k.get("ad_soyad", tid))
            ozet[tid]["gorev"] = p.get("gorev", k.get("gorev", ""))

        ozet[tid]["aylar"][ay]["toplam_dk"] += sure_dk
        ozet[tid]["aylar"][ay]["egitimler"].append({
            "konu": konu, "tur": tur, "sure_dk": sure_dk,
            "durum": durum, "tarih": tarih
        })
        ozet[tid]["yillik_toplam_dk"] += sure_dk
        ozet[tid]["egitim_sayisi"] += 1
        tum_aylar.add(ay)

    # Firma özeti (ay bazlı toplam)
    firma_ozet = defaultdict(lambda: {"toplam_dk": 0, "calisan_sayisi": 0})
    for tid, veri in ozet.items():
        for ay, ay_veri in veri["aylar"].items():
            firma_ozet[ay]["toplam_dk"] += ay_veri["toplam_dk"]
            firma_ozet[ay]["calisan_sayisi"] += 1

    # Saat hesapla ve defaultdict'i normal dict'e çevir
    sonuc_calisanlar = {}
    for tid, veri in ozet.items():
        aylar_dict = {}
        for ay, av in veri["aylar"].items():
            aylar_dict[ay] = {
                "toplam_dk": av["toplam_dk"],
                "toplam_saat": round(av["toplam_dk"] / 60, 1),
                "egitimler": av["egitimler"],
                "ay_etiket": _tarih_ay_etiket(ay)
            }
        sonuc_calisanlar[tid] = {
            "ad_soyad": veri["ad_soyad"],
            "gorev": veri["gorev"],
            "aylar": aylar_dict,
            "yillik_toplam_dk": veri["yillik_toplam_dk"],
            "yillik_toplam_saat": round(veri["yillik_toplam_dk"] / 60, 1),
            "egitim_sayisi": veri["egitim_sayisi"],
        }

    firma_ozet_dict = {}
    for ay, av in firma_ozet.items():
        firma_ozet_dict[ay] = {
            "toplam_dk": av["toplam_dk"],
            "toplam_saat": round(av["toplam_dk"] / 60, 1),
            "calisan_sayisi": av["calisan_sayisi"],
            "ay_etiket": _tarih_ay_etiket(ay)
        }

    sirali_aylar = sorted(tum_aylar)

    return {
        "aylar": sirali_aylar,
        "ay_etiketleri": {a: _tarih_ay_etiket(a) for a in sirali_aylar},
        "calisanlar": sonuc_calisanlar,
        "firma_ozet": firma_ozet_dict,
        "yil": hedef_yil,
    }


def calisan_egitim_detay(firma_id: str, telegram_id: str, yil: int = None) -> dict:
    """
    Tek bir çalışanın yıllık eğitim detayı.
    """
    ozet = aylik_egitim_ozeti(firma_id, yil)
    calisan = ozet["calisanlar"].get(str(telegram_id), {})
    return {
        "telegram_id": telegram_id,
        "ad_soyad": calisan.get("ad_soyad", ""),
        "gorev": calisan.get("gorev", ""),
        "aylar": calisan.get("aylar", {}),
        "yillik_toplam_dk": calisan.get("yillik_toplam_dk", 0),
        "yillik_toplam_saat": calisan.get("yillik_toplam_saat", 0),
        "egitim_sayisi": calisan.get("egitim_sayisi", 0),
    }
