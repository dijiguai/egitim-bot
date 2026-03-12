"""
Google Sheets entegrasyonu
"""

import logging
import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SHEET_NAME = "Sayfa1"

SUTUNLAR = [
    "tarih", "saat", "ad_soyad", "telegram_id",
    "gorev", "egitim_konusu", "egitim_turu",
    "puan", "durum", "kimlik_dogrulandi", "dogum_yili"
]


def _servis():
    creds_path = os.environ.get("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    spreadsheet_id = os.environ.get("SPREADSHEET_ID")
    creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    service = build("sheets", "v4", credentials=creds).spreadsheets()
    return service, spreadsheet_id


def kayit_ekle(kayit: dict):
    """Yeni kayıt ekle — kayit_handler tarafından çağrılır."""
    satir = [str(kayit.get(s, "")) for s in SUTUNLAR]
    servis, spreadsheet_id = _servis()
    servis.values().append(
        spreadsheetId=spreadsheet_id,
        range=f"{SHEET_NAME}!A1",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": [satir]}
    ).execute()
    logger.info(f"Sheets'e yazıldı: {kayit.get('ad_soyad')} — {kayit.get('durum')}")


# Geriye dönük uyumluluk
sonuc_kaydet = kayit_ekle


def kayitlari_getir(bas: str = "", bitis: str = "") -> list:
    """Tarih aralığına göre kayıt getir."""
    return [
        k for k in tum_kayitlar_getir()
        if (not bas or k.get("tarih", "") >= bas) and
           (not bitis or k.get("tarih", "") <= bitis)
    ]


def tum_kayitlar_getir() -> list:
    """Panel için tüm kayıtları getirir."""
    try:
        servis, spreadsheet_id = _servis()
        result = servis.values().get(
            spreadsheetId=spreadsheet_id,
            range=f"{SHEET_NAME}!A2:K"
        ).execute()
        satirlar = result.get("values", [])
        kayitlar = []
        for satir in satirlar:
            if len(satir) < len(SUTUNLAR):
                satir.extend([""] * (len(SUTUNLAR) - len(satir)))
            kayitlar.append(dict(zip(SUTUNLAR, satir)))
        return kayitlar
    except Exception as e:
        logger.error(f"Sheets okuma hatası: {e}")
        return []
