"""
isg/sure_hesap.py
=================
6331 sayılı İSG Kanunu ve İşyerlerinde İş Sağlığı ve Güvenliği Eğitimlerinin
Usul ve Esasları Hakkında Yönetmelik'e göre zorunlu eğitim süre hesaplama.

Yasal Dayanak:
  - Az tehlikeli:  min 8 saat/yıl/çalışan
  - Tehlikeli:     min 12 saat/yıl/çalışan
  - Çok tehlikeli: min 16 saat/yıl/çalışan

Uzman görevlendirme çalışma saati (İSG Hizmetleri Yönetmeliği Ek-1):
  - Az tehlikeli:  ≤1000 çalışan → 10 dk/çalışan/ay
                   >1000 → tam zamanlı
  - Tehlikeli:     ≤500  → 15 dk/çalışan/ay (min 4h/ay)
                   >500  → tam zamanlı
  - Çok tehlikeli: ≤250  → 20 dk/çalışan/ay (min 4h/ay)
                   >250  → tam zamanlı

Uzman sınıfı yetki:
  - A sınıfı: Çok tehlikeli + Tehlikeli + Az tehlikeli
  - B sınıfı: Tehlikeli + Az tehlikeli
  - C sınıfı: Az tehlikeli
  - Hekim:    Tüm sınıflar (sağlık gözetimi)
"""

import logging
from isg.sheets_base import sekme_olustur, tum_satirlar, satir_ekle, satir_guncelle

logger = logging.getLogger(__name__)

SEKME = "ISG_SureHesap"
BASLIKLAR = [
    "firma_id", "calisan_sayisi", "hesaplanan_yillik_sure_saat",
    "uzman_aylik_sure_dk", "uzman_tam_zamanli_mi",
    "guncelleme_tarihi"
]

# ── Yasal eğitim süreleri ───────────────────────────────────────
EGITIM_SURE_YILLIK = {
    "Az Tehlikeli":  8,   # saat/yıl/çalışan
    "Tehlikeli":     12,
    "Çok Tehlikeli": 16,
}

# ── Uzman çalışma süresi tablosu (Ek-1) ────────────────────────
def uzman_sure_hesapla(tehlike_sinifi: str, calisan_sayisi: int) -> dict:
    """
    Uzmanın aylık zorunlu çalışma süresini hesaplar.
    Döner: {
        aylik_sure_dk: int,     # toplam aylık dakika
        tam_zamanli: bool,
        aciklama: str
    }
    """
    n = max(0, calisan_sayisi)

    if tehlike_sinifi == "Az Tehlikeli":
        if n > 1000:
            return {"aylik_sure_dk": None, "tam_zamanli": True,
                    "aciklama": "Tam zamanlı uzman zorunlu (>1000 çalışan)"}
        dk = n * 10
        return {"aylik_sure_dk": dk, "tam_zamanli": False,
                "aciklama": f"{n} × 10 dk = {dk} dk/ay"}

    elif tehlike_sinifi == "Tehlikeli":
        if n > 500:
            return {"aylik_sure_dk": None, "tam_zamanli": True,
                    "aciklama": "Tam zamanlı uzman zorunlu (>500 çalışan)"}
        dk = max(240, n * 15)   # min 4 saat = 240 dk
        return {"aylik_sure_dk": dk, "tam_zamanli": False,
                "aciklama": f"{n} × 15 dk = {n*15} dk → min 240 dk → {dk} dk/ay"}

    elif tehlike_sinifi == "Çok Tehlikeli":
        if n > 250:
            return {"aylik_sure_dk": None, "tam_zamanli": True,
                    "aciklama": "Tam zamanlı uzman zorunlu (>250 çalışan)"}
        dk = max(240, n * 20)   # min 4 saat = 240 dk
        return {"aylik_sure_dk": dk, "tam_zamanli": False,
                "aciklama": f"{n} × 20 dk = {n*20} dk → min 240 dk → {dk} dk/ay"}

    return {"aylik_sure_dk": 0, "tam_zamanli": False, "aciklama": "Tehlike sınıfı tanımsız"}


def egitim_sure_hesapla(tehlike_sinifi: str, calisan_sayisi: int) -> dict:
    """
    Yıllık zorunlu eğitim süresini hesaplar.
    Döner: {
        yillik_sure_saat: int,   # tüm çalışanlar toplamı
        kisi_basi_saat: int,
        aylik_sure_saat: float,
        aciklama: str
    }
    """
    kisi_basi = EGITIM_SURE_YILLIK.get(tehlike_sinifi, 0)
    toplam = kisi_basi * calisan_sayisi
    return {
        "kisi_basi_saat": kisi_basi,
        "yillik_sure_saat": toplam,
        "aylik_sure_saat": round(toplam / 12, 1),
        "aciklama": f"{calisan_sayisi} çalışan × {kisi_basi} saat = {toplam} saat/yıl"
    }


def uzman_sinifi_kontrol(uzman_sinifi: str, tehlike_sinifi: str) -> dict:
    """
    Uzman sınıfının tehlike sınıfı için yeterliliğini kontrol eder.
    Döner: {yeterli: bool, mesaj: str}
    """
    yetki = {
        "A": ["Az Tehlikeli", "Tehlikeli", "Çok Tehlikeli"],
        "B": ["Az Tehlikeli", "Tehlikeli"],
        "C": ["Az Tehlikeli"],
        "—": ["Az Tehlikeli", "Tehlikeli", "Çok Tehlikeli"],  # Hekim
    }
    izinliler = yetki.get(uzman_sinifi, [])
    yeterli = tehlike_sinifi in izinliler

    if yeterli:
        return {"yeterli": True, "mesaj": f"{uzman_sinifi} sınıfı uzman bu işyeri için yetkilendirilmiştir."}
    else:
        sinif_map = {"B": "A", "C": "A veya B"}
        gereken = sinif_map.get(uzman_sinifi, "A")
        return {"yeterli": False,
                "mesaj": f"⚠️ {uzman_sinifi} sınıfı uzman Çok Tehlikeli işyerinde çalışamaz! "
                         f"En az {gereken} sınıfı uzman atanmalıdır."}


def firma_sure_ozeti(firma_id: str, tehlike_sinifi: str,
                     calisan_sayisi: int, uzman_sinifi: str = None) -> dict:
    """
    Panel için tam özet: eğitim süresi + uzman süresi + uyumluluk.
    """
    egitim = egitim_sure_hesapla(tehlike_sinifi, calisan_sayisi)
    uzman = uzman_sure_hesapla(tehlike_sinifi, calisan_sayisi)

    sinif_kontrol = None
    if uzman_sinifi and uzman_sinifi != "—":
        sinif_kontrol = uzman_sinifi_kontrol(uzman_sinifi, tehlike_sinifi)

    return {
        "firma_id": firma_id,
        "tehlike_sinifi": tehlike_sinifi,
        "calisan_sayisi": calisan_sayisi,
        "egitim": egitim,
        "uzman": uzman,
        "sinif_kontrol": sinif_kontrol,
    }


def sure_kaydet(firma_id: str, calisan_sayisi: int,
                yillik_sure: int, aylik_uzman_dk,
                tam_zamanli: bool) -> bool:
    """Hesaplanan süreyi Sheets'e kaydet."""
    from datetime import datetime
    sekme_olustur(SEKME, BASLIKLAR)
    simdi = datetime.now().strftime("%d.%m.%Y %H:%M")

    satirlar = tum_satirlar(SEKME)
    for i, satir in enumerate(satirlar):
        if satir and satir[0] == firma_id:
            return satir_guncelle(SEKME, i + 2, [
                firma_id, calisan_sayisi, yillik_sure,
                aylik_uzman_dk or "Tam zamanlı",
                "Evet" if tam_zamanli else "Hayır", simdi
            ])

    return satir_ekle(SEKME, [
        firma_id, calisan_sayisi, yillik_sure,
        aylik_uzman_dk or "Tam zamanlı",
        "Evet" if tam_zamanli else "Hayır", simdi
    ])
