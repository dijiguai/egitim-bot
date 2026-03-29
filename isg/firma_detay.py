"""
isg/firma_detay.py
==================
Firma ISG detayları — Google Sheets "ISG_FirmaDetay" sekmesi.
Mevcut firma_manager.py'yi bozmadan genişletir.

Sütunlar:
    firma_id | sgk_sicil_no | nace_kodu | tehlike_sinifi |
    calisan_sayisi | guncelleme_tarihi | guncelleyen
"""

import logging
from datetime import datetime
from isg.sheets_base import sekme_olustur, satir_ekle, tum_satirlar, satir_guncelle

logger = logging.getLogger(__name__)

SEKME     = "ISG_FirmaDetay"
BASLIKLAR = [
    "firma_id", "sgk_sicil_no", "nace_kodu", "tehlike_sinifi",
    "calisan_sayisi", "guncelleme_tarihi", "guncelleyen"
]

TEHLIKE_SINIFLARI = ["Az Tehlikeli", "Tehlikeli", "Çok Tehlikeli"]

# Yaygın NACE kodları → tehlike sınıfı (tam liste ÇSGB yönetmeliğinden)
# Kullanıcı override edebilir; bu sadece otomatik öneri için
NACE_TEHLIKE_MAP = {
    # Çok Tehlikeli
    "05": "Çok Tehlikeli",   # Kömür madenciliği
    "06": "Çok Tehlikeli",   # Ham petrol ve doğalgaz
    "07": "Çok Tehlikeli",   # Metal cevheri madenciliği
    "08": "Çok Tehlikeli",   # Diğer madencilik
    "09": "Çok Tehlikeli",   # Madenciliği destekleyici
    "13": "Çok Tehlikeli",   # Tekstil
    "23": "Çok Tehlikeli",   # Metalik olmayan mineral ürünleri (çimento!)
    "24": "Çok Tehlikeli",   # Ana metal sanayi
    "25": "Çok Tehlikeli",   # Metal ürünleri imalatı
    "41": "Çok Tehlikeli",   # Bina inşaatı
    "42": "Çok Tehlikeli",   # Altyapı inşaatı
    "43": "Çok Tehlikeli",   # Özel inşaat faaliyetleri
    "35": "Çok Tehlikeli",   # Elektrik, gaz
    "38": "Çok Tehlikeli",   # Atık toplama, bertaraf
    "49": "Çok Tehlikeli",   # Kara taşımacılığı
    "50": "Çok Tehlikeli",   # Su taşımacılığı

    # Tehlikeli
    "10": "Tehlikeli",       # Gıda ürünleri imalatı
    "11": "Tehlikeli",       # İçecek imalatı
    "14": "Tehlikeli",       # Giyim eşyası imalatı
    "20": "Tehlikeli",       # Kimyasallar
    "21": "Tehlikeli",       # İlaç
    "28": "Tehlikeli",       # Makine imalatı
    "29": "Tehlikeli",       # Motorlu kara taşıtı
    "45": "Tehlikeli",       # Motorlu taşıt satışı
    "46": "Tehlikeli",       # Toptan ticaret
    "52": "Tehlikeli",       # Depolama
    "56": "Tehlikeli",       # Yiyecek ve içecek hizmetleri

    # Az Tehlikeli
    "47": "Az Tehlikeli",    # Perakende ticaret
    "55": "Az Tehlikeli",    # Konaklama
    "62": "Az Tehlikeli",    # Bilgi ve iletişim teknolojileri
    "63": "Az Tehlikeli",    # Bilgi hizmetleri
    "64": "Az Tehlikeli",    # Finansal hizmetler
    "69": "Az Tehlikeli",    # Hukuk, muhasebe
    "70": "Az Tehlikeli",    # Yönetim danışmanlığı
    "72": "Az Tehlikeli",    # Bilimsel araştırma
    "73": "Az Tehlikeli",    # Reklam
    "74": "Az Tehlikeli",    # Diğer profesyonel
    "75": "Az Tehlikeli",    # Veterinerlik
    "85": "Az Tehlikeli",    # Eğitim
    "86": "Az Tehlikeli",    # Sağlık hizmetleri
    "90": "Az Tehlikeli",    # Yaratıcı sanatlar
}


def _hazirla():
    sekme_olustur(SEKME, BASLIKLAR)


def _satir_to_dict(satir: list) -> dict:
    while len(satir) < len(BASLIKLAR):
        satir.append("")
    return dict(zip(BASLIKLAR, satir))


def nace_tahmin(nace_kodu: str) -> str:
    """
    NACE kodundan tehlike sınıfı tahmin eder.
    İlk 2 hane üzerinden eşleştirme yapar.
    Kullanıcı her zaman override edebilir.
    """
    if not nace_kodu:
        return ""
    ilk_iki = nace_kodu.strip().replace(".", "")[:2]
    return NACE_TEHLIKE_MAP.get(ilk_iki, "")


def sgk_den_nace(sgk_sicil_no: str) -> str:
    """
    SGK sicil no'sundan NACE kodu çıkar.
    Format: NNNNNN... → 2-7. haneler NACE (bazı kaynaklara göre)
    NOT: Bu yöntem her zaman doğru değil, kullanıcı onaylamalı.
    """
    temiz = "".join(c for c in str(sgk_sicil_no) if c.isdigit())
    if len(temiz) >= 7:
        # İlk iki hane il kodu, 3-6. haneler NACE olabilir
        nace_ham = temiz[2:6]
        if len(nace_ham) == 4:
            return f"{nace_ham[:2]}.{nace_ham[2:]}"
    return ""


def firma_detay_getir(firma_id: str) -> dict:
    """Firmanın ISG detaylarını döner. Yoksa boş dict."""
    _hazirla()
    for satir in tum_satirlar(SEKME):
        d = _satir_to_dict(satir)
        if d.get("firma_id") == firma_id:
            return d
    return {"firma_id": firma_id, "sgk_sicil_no": "", "nace_kodu": "",
            "tehlike_sinifi": "", "calisan_sayisi": ""}


def firma_detay_kaydet(firma_id: str, sgk_sicil_no: str, nace_kodu: str,
                       tehlike_sinifi: str, calisan_sayisi: str = "",
                       yapan: str = "panel") -> bool:
    """Firma ISG detaylarını ekler veya günceller."""
    _hazirla()
    simdi = datetime.now().strftime("%d.%m.%Y %H:%M")
    satirlar = tum_satirlar(SEKME)

    for i, satir in enumerate(satirlar):
        if satir and satir[0] == firma_id:
            # Güncelle
            satir_no = i + 2
            eski = _satir_to_dict(list(satir))
            yeni = [firma_id, sgk_sicil_no, nace_kodu, tehlike_sinifi,
                    calisan_sayisi, simdi, yapan]
            ok = satir_guncelle(SEKME, satir_no, yeni)
            if ok:
                try:
                    from firma_manager import tum_firmalar
                    firma_ad = tum_firmalar().get(firma_id, {}).get("ad", firma_id)
                    from isg.audit_log import log_firma_detay
                    log_firma_detay(firma_id, firma_ad, eski,
                                    _satir_to_dict(yeni), yapan)
                except Exception as e:
                    logger.warning(f"Audit log: {e}")
            return ok

    # Yeni ekle
    ok = satir_ekle(SEKME, [firma_id, sgk_sicil_no, nace_kodu, tehlike_sinifi,
                             calisan_sayisi, simdi, yapan])
    if ok:
        try:
            from firma_manager import tum_firmalar
            firma_ad = tum_firmalar().get(firma_id, {}).get("ad", firma_id)
            from isg.audit_log import log_firma_detay
            log_firma_detay(firma_id, firma_ad, {}, {
                "sgk": sgk_sicil_no, "nace": nace_kodu,
                "tehlike": tehlike_sinifi
            }, yapan)
        except Exception as e:
            logger.warning(f"Audit log: {e}")
    return ok


def tehlike_sinifi_str(sinif: str) -> str:
    """Bot mesajı için tehlike sınıfı emoji + metin."""
    emojiler = {
        "Az Tehlikeli":  "🟢",
        "Tehlikeli":     "🟡",
        "Çok Tehlikeli": "🔴",
    }
    emoji = emojiler.get(sinif, "⚪")
    return f"{emoji} {sinif}" if sinif else ""
