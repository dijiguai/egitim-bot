"""
Çalışan yönetimi — Google Sheets'te "Calisanlar" sekmesinde saklanır.
Deploy/restart sonrası veri kaybolmaz.
"""

import logging
import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SEKME = "Calisanlar"
SUTUNLAR = ["telegram_id", "ad_soyad", "dogum_tarihi", "gorev", "aktif"]


def _servis():
    creds_path = os.environ.get("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    spreadsheet_id = os.environ.get("SPREADSHEET_ID")
    creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    service = build("sheets", "v4", credentials=creds).spreadsheets()
    return service, spreadsheet_id


def _baslik_kontrol():
    """İlk satırda başlık yoksa ekle."""
    try:
        servis, sid = _servis()
        result = servis.values().get(
            spreadsheetId=sid, range=f"{SEKME}!A1:E1"
        ).execute()
        satirlar = result.get("values", [])
        if not satirlar or satirlar[0][0] != "telegram_id":
            servis.values().update(
                spreadsheetId=sid,
                range=f"{SEKME}!A1",
                valueInputOption="RAW",
                body={"values": [SUTUNLAR]}
            ).execute()
    except Exception as e:
        logger.warning(f"Başlık kontrol hatası: {e}")


def tum_calisanlar() -> dict:
    """{ telegram_id(int): { ad_soyad, dogum_tarihi, gorev, aktif } }"""
    try:
        servis, sid = _servis()
        result = servis.values().get(
            spreadsheetId=sid, range=f"{SEKME}!A2:E"
        ).execute()
        satirlar = result.get("values", [])
        calisanlar = {}
        for satir in satirlar:
            if len(satir) < 4:
                continue
            try:
                tid = int(satir[0])
            except ValueError:
                continue
            calisanlar[tid] = {
                "ad_soyad": satir[1] if len(satir) > 1 else "",
                "dogum_tarihi": satir[2] if len(satir) > 2 else "",
                "gorev": satir[3] if len(satir) > 3 else "",
                "aktif": (satir[4] if len(satir) > 4 else "1") == "1"
            }
        return calisanlar
    except Exception as e:
        logger.error(f"Çalışanlar okunamadı: {e}")
        return {}


def calisan_bul(telegram_id: int) -> dict:
    return tum_calisanlar().get(telegram_id)


def _satir_bul(telegram_id: int):
    """Çalışanın Sheets'teki satır numarasını bul (1'den başlar, başlık=1)."""
    try:
        servis, sid = _servis()
        result = servis.values().get(
            spreadsheetId=sid, range=f"{SEKME}!A2:A"
        ).execute()
        satirlar = result.get("values", [])
        for i, satir in enumerate(satirlar):
            if satir and str(satir[0]) == str(telegram_id):
                return i + 2  # +2: başlık satırı + 0-index
    except Exception as e:
        logger.error(f"Satır bulunamadı: {e}")
    return None


def calisan_ekle(telegram_id: int, ad_soyad: str, dogum_tarihi: str, gorev: str):
    _baslik_kontrol()
    # Zaten varsa güncelle
    satir_no = _satir_bul(telegram_id)
    servis, sid = _servis()
    deger = [[str(telegram_id), ad_soyad, dogum_tarihi, gorev, "1"]]

    if satir_no:
        servis.values().update(
            spreadsheetId=sid,
            range=f"{SEKME}!A{satir_no}",
            valueInputOption="RAW",
            body={"values": deger}
        ).execute()
    else:
        servis.values().append(
            spreadsheetId=sid,
            range=f"{SEKME}!A1",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": deger}
        ).execute()
    logger.info(f"Çalışan eklendi/güncellendi: {ad_soyad}")


def calisan_guncelle(telegram_id: int, ad_soyad: str, dogum_tarihi: str, gorev: str):
    calisan_ekle(telegram_id, ad_soyad, dogum_tarihi, gorev)


def calisan_sil(telegram_id: int):
    """Aktif=0 yaparak pasife al (veriyi korur)."""
    satir_no = _satir_bul(telegram_id)
    if not satir_no:
        return
    servis, sid = _servis()
    # Mevcut veriyi al
    result = servis.values().get(
        spreadsheetId=sid, range=f"{SEKME}!A{satir_no}:E{satir_no}"
    ).execute()
    satirlar = result.get("values", [[]])
    if satirlar and len(satirlar[0]) >= 4:
        satirlar[0] = satirlar[0][:4] + ["0"]  # aktif=0
        servis.values().update(
            spreadsheetId=sid,
            range=f"{SEKME}!A{satir_no}",
            valueInputOption="RAW",
            body={"values": satirlar}
        ).execute()
    logger.info(f"Çalışan pasife alındı: {telegram_id}")
