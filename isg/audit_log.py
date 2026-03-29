"""
isg/audit_log.py
================
Tüm ISG modülündeki değişiklikleri zaman damgalı, değiştirilemez
şekilde Google Sheets "ISG_AuditLog" sekmesine kaydeder.

APPEND ONLY — hiçbir satır silinmez veya değiştirilmez.
ÇSGB denetiminde "kim ne zaman ne yaptı?" sorusuna yanıt verir.
"""

import logging
from datetime import datetime
from isg.sheets_base import sekme_olustur, satir_ekle

logger = logging.getLogger(__name__)

SEKME     = "ISG_AuditLog"
BASLIKLAR = [
    "zaman", "islem", "tablo", "kayit_id",
    "ozet", "eski_deger", "yeni_deger", "yapan_id", "yapan_ad"
]

# İşlem sabitleri
ISLEM_EKLE     = "EKLE"
ISLEM_GUNCELLE = "GUNCELLE"
ISLEM_PASIF    = "PASIF_YAP"
ISLEM_ATAMA    = "ATAMA"
ISLEM_AYRILMA  = "AYRILMA"


def _hazirla():
    sekme_olustur(SEKME, BASLIKLAR)


def log_yaz(
    islem: str,
    tablo: str,
    kayit_id: str,
    ozet: str,
    eski_deger: str = "",
    yeni_deger: str = "",
    yapan_id: str = "panel",
    yapan_ad: str = "Panel Kullanıcısı"
) -> bool:
    """
    Audit log'a bir satır ekler.

    Parametreler:
        islem      : EKLE / GUNCELLE / PASIF_YAP / ATAMA / AYRILMA
        tablo      : Uzmanlar / UzmanAtamalari / FirmaDetay
        kayit_id   : İlgili kaydın ID'si
        ozet       : İnsan okunabilir açıklama
        eski_deger : JSON string — önceki değer (opsiyonel)
        yeni_deger : JSON string — yeni değer (opsiyonel)
        yapan_id   : Kim yaptı (session kullanıcısı)
        yapan_ad   : Görünen ad
    """
    try:
        _hazirla()
        zaman = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        return satir_ekle(SEKME, [
            zaman, islem, tablo, kayit_id,
            ozet, eski_deger, yeni_deger, yapan_id, yapan_ad
        ])
    except Exception as e:
        logger.error(f"Audit log yazılamadı: {e}")
        return False


def log_uzman_ekle(uzman_id: str, ad_soyad: str, yapan: str = "panel"):
    log_yaz(
        islem=ISLEM_EKLE, tablo="Uzmanlar", kayit_id=uzman_id,
        ozet=f"Yeni uzman eklendi: {ad_soyad}", yapan_ad=yapan
    )


def log_uzman_guncelle(uzman_id: str, ad_soyad: str, eski: dict, yeni: dict, yapan: str = "panel"):
    import json
    log_yaz(
        islem=ISLEM_GUNCELLE, tablo="Uzmanlar", kayit_id=uzman_id,
        ozet=f"Uzman güncellendi: {ad_soyad}",
        eski_deger=json.dumps(eski, ensure_ascii=False),
        yeni_deger=json.dumps(yeni, ensure_ascii=False),
        yapan_ad=yapan
    )


def log_atama(uzman_id: str, firma_id: str, uzman_ad: str, firma_ad: str,
              baslangic: str, yapan: str = "panel"):
    log_yaz(
        islem=ISLEM_ATAMA, tablo="UzmanAtamalari",
        kayit_id=f"{uzman_id}_{firma_id}",
        ozet=f"{uzman_ad} → {firma_ad} atandı ({baslangic})",
        yeni_deger=f"baslangic={baslangic}",
        yapan_ad=yapan
    )


def log_ayrilma(uzman_id: str, firma_id: str, uzman_ad: str, firma_ad: str,
                bitis: str, yapan: str = "panel"):
    log_yaz(
        islem=ISLEM_AYRILMA, tablo="UzmanAtamalari",
        kayit_id=f"{uzman_id}_{firma_id}",
        ozet=f"{uzman_ad} ← {firma_ad} ayrıldı ({bitis})",
        yeni_deger=f"bitis={bitis}",
        yapan_ad=yapan
    )


def log_firma_detay(firma_id: str, firma_ad: str, eski: dict, yeni: dict, yapan: str = "panel"):
    import json
    log_yaz(
        islem=ISLEM_GUNCELLE, tablo="FirmaDetay", kayit_id=firma_id,
        ozet=f"Firma detayı güncellendi: {firma_ad}",
        eski_deger=json.dumps(eski, ensure_ascii=False),
        yeni_deger=json.dumps(yeni, ensure_ascii=False),
        yapan_ad=yapan
    )
