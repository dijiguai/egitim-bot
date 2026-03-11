"""
Google Sheets entegrasyonu
Sonuçları Sheets'e yazar, raporlar için okur.
"""

import logging
import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from config import SPREADSHEET_ID, SHEET_NAME

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Sütun sırası — Sheets'teki başlık satırıyla eşleşmeli
SUTUNLAR = [
    "tarih", "saat", "ad_soyad", "telegram_id",
    "gorev", "egitim_konusu", "egitim_turu",
    "puan", "durum", "kimlik_dogrulandi", "dogum_tarihi_son4"
]


def _servis():
    """Google Sheets API servisini başlatır."""
    creds_path = os.environ.get("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    return build("sheets", "v4", credentials=creds).spreadsheets()


def sheets_basliklari_olustur():
    """
    İlk kurulumda çağrılır.
    Sheets'te başlık satırını ve Çalışanlar sekmesini oluşturur.
    """
    try:
        servis = _servis()

        # Başlık satırı
        basliklar = [
            "Tarih", "Saat", "Ad Soyad", "Telegram ID",
            "Görev", "Eğitim Konusu", "Eğitim Türü",
            "Puan", "Durum", "Kimlik Doğrulandı", "Doğum Yılı"
        ]

        servis.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A1",
            valueInputOption="RAW",
            body={"values": [basliklar]}
        ).execute()

        logger.info("Sheets başlıkları oluşturuldu.")
    except Exception as e:
        logger.error(f"Başlık oluşturma hatası: {e}")


def sonuc_kaydet(kayit: dict):
    """
    Tek bir eğitim sonucunu Sheets'e ekler.
    kayit: { tarih, saat, ad_soyad, ... }
    """
    satir = [kayit.get(s, "") for s in SUTUNLAR]

    servis = _servis()
    servis.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A1",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": [satir]}
    ).execute()

    logger.info(f"Sheets'e kayıt eklendi: {kayit.get('ad_soyad')} — {kayit.get('durum')}")


def kayitlari_getir(tarih: str) -> list[dict]:
    """
    Belirli bir tarihe ait kayıtları Sheets'ten çeker.
    tarih: "11.03.2026" formatında
    """
    servis = _servis()
    result = servis.values().get(
        spreadsheetId=SPREADSHEET_ID,
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


def tum_egitim_ozeti() -> list[dict]:
    """Arşiv için tüm kayıtları getirir."""
    servis = _servis()
    result = servis.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A2:K"
    ).execute()

    satirlar = result.get("values", [])
    return [dict(zip(SUTUNLAR, s)) for s in satirlar if s]
