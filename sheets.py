"""
Google Sheets entegrasyonu
"""

import logging
import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SHEET_NAME = "Sayfa1"  # Google Sheets'te sekme adı — varsayılan "Sayfa1"

SUTUNLAR = [
    "tarih", "saat", "ad_soyad", "telegram_id",
    "gorev", "egitim_konusu", "egitim_turu",
    "puan", "durum", "kimlik_dogrulandi", "dogum_tarihi_son4"
]


def _servis():
    creds_path = os.environ.get("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    spreadsheet_id = os.environ.get("SPREADSHEET_ID")
    creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    service = build("sheets", "v4", credentials=creds).spreadsheets()
    return service, spreadsheet_id


def sonuc_kaydet(kayit: dict):
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


def kayitlari_getir(tarih: str) -> list:
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
        kayit = dict(zip(SUTUNLAR, satir))
        if kayit.get("tarih") == tarih:
            kayitlar.append(kayit)
    return kayitlar
