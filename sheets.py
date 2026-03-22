"""
Egitim kayitlari - firma bazli Google Sheets okuma/yazma
"""

import logging, os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from datetime import datetime

logger = logging.getLogger(__name__)
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

SUTUNLAR = [
    "tarih", "saat", "ad_soyad", "telegram_id",
    "gorev", "egitim_konusu", "egitim_turu",
    "puan", "durum", "kimlik_dogrulandi", "dogum_yili", "deneme_no"
]

def _normalize_durum(d: str) -> str:
    """GEÇTİ / GECTİ / GECTI → GECTI; KALDI → KALDI"""
    if not d:
        return ""
    d = d.upper().strip()
    d = d.replace("Ç","C").replace("İ","I").replace("Ğ","G").replace("Ş","S").replace("Ü","U").replace("Ö","O")
    return d

def _servis():
    creds_path = os.environ.get("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    spreadsheet_id = os.environ.get("SPREADSHEET_ID")
    creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    service = build("sheets", "v4", credentials=creds).spreadsheets()
    return service, spreadsheet_id

def _kayitlar_sekme(firma_id: str = None) -> str:
    if not firma_id or firma_id == "varsayilan":
        return "Sayfa1"
    try:
        from firma_manager import tum_firmalar
        f = tum_firmalar().get(firma_id, {})
        return f.get("kayitlar_sekme", f"Kayitlar_{firma_id}")
    except:
        return "Sayfa1"

def kayit_ekle(kayit: dict, firma_id: str = None):
    sekme = _kayitlar_sekme(firma_id)
    servis, spreadsheet_id = _servis()
    satir = [str(kayit.get(s, "")) for s in SUTUNLAR]
    servis.values().append(
        spreadsheetId=spreadsheet_id,
        range=f"{sekme}!A1",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": [satir]}
    ).execute()

def tum_kayitlar_getir(firma_id: str = None) -> list:
    sekme = _kayitlar_sekme(firma_id)
    try:
        servis, spreadsheet_id = _servis()
        result = servis.values().get(
            spreadsheetId=spreadsheet_id,
            range=f"{sekme}!A2:L"
        ).execute()
        satirlar = result.get("values", [])
        kayitlar = []
        for satir in satirlar:
            if len(satir) < len(SUTUNLAR):
                satir.extend([""] * (len(SUTUNLAR) - len(satir)))
            k = dict(zip(SUTUNLAR, satir))
            k["durum"] = _normalize_durum(k.get("durum", ""))
            kayitlar.append(k)
        return kayitlar
    except Exception as e:
        logger.error(f"Sheets okuma hatasi ({sekme}): {e}")
        return []

def kayitlari_getir(bas: str = "", bitis: str = "", firma_id: str = None) -> list:
    return [
        k for k in tum_kayitlar_getir(firma_id)
        if (not bas or k.get("tarih", "") >= bas) and
           (not bitis or k.get("tarih", "") <= bitis)
    ]
