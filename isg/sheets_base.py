"""
isg/sheets_base.py
Tüm ISG modülü için ortak Sheets bağlantısı.
sheets.py'deki _servis() ile aynı mantık — bağımsız çalışır.
"""

import os, json, logging
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def _get_credentials():
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if creds_json:
        try:
            return Credentials.from_service_account_info(
                json.loads(creds_json), scopes=SCOPES
            )
        except Exception as e:
            logger.error(f"GOOGLE_CREDENTIALS_JSON parse hatası: {e}")
    path = os.environ.get("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    if os.path.exists(path):
        return Credentials.from_service_account_file(path, scopes=SCOPES)
    raise ValueError("Google credentials bulunamadı!")


def servis():
    """(sheets_service, spreadsheet_id) döner."""
    creds = _get_credentials()
    s = build("sheets", "v4", credentials=creds).spreadsheets()
    sid = os.environ.get("SPREADSHEET_ID")
    if not sid:
        raise ValueError("SPREADSHEET_ID tanımlı değil!")
    return s, sid


def mevcut_sekmeler() -> list:
    try:
        s, sid = servis()
        meta = s.get(spreadsheetId=sid).execute()
        return [sh["properties"]["title"] for sh in meta.get("sheets", [])]
    except Exception as e:
        logger.error(f"Sekme listesi alınamadı: {e}")
        return []


def sekme_olustur(sekme_adi: str, basliklar: list = None) -> bool:
    """Sekme yoksa oluşturur, başlık satırı ekler."""
    try:
        s, sid = servis()
        mevcutlar = mevcut_sekmeler()
        if sekme_adi not in mevcutlar:
            s.batchUpdate(spreadsheetId=sid, body={
                "requests": [{"addSheet": {"properties": {"title": sekme_adi}}}]
            }).execute()
            logger.info(f"Sekme oluşturuldu: {sekme_adi}")

        if basliklar:
            r = s.values().get(spreadsheetId=sid, range=f"{sekme_adi}!A1:A1").execute()
            if not r.get("values"):
                s.values().update(
                    spreadsheetId=sid, range=f"{sekme_adi}!A1",
                    valueInputOption="RAW", body={"values": [basliklar]}
                ).execute()
        return True
    except Exception as e:
        logger.error(f"Sekme oluşturma hatası ({sekme_adi}): {e}")
        return False


def satir_ekle(sekme: str, degerler: list) -> bool:
    """Sekmenin sonuna satır ekler (APPEND)."""
    try:
        s, sid = servis()
        s.values().append(
            spreadsheetId=sid, range=f"{sekme}!A1",
            valueInputOption="RAW", insertDataOption="INSERT_ROWS",
            body={"values": [degerler]}
        ).execute()
        return True
    except Exception as e:
        logger.error(f"Satır ekleme hatası ({sekme}): {e}")
        return False


def tum_satirlar(sekme: str, aralik: str = None) -> list:
    """Sekmeden tüm satırları liste olarak döner (başlık hariç)."""
    try:
        s, sid = servis()
        r = s.values().get(
            spreadsheetId=sid,
            range=aralik or f"{sekme}!A2:Z"
        ).execute()
        return r.get("values", [])
    except Exception as e:
        logger.error(f"Satır okuma hatası ({sekme}): {e}")
        return []


def satir_guncelle(sekme: str, satir_no: int, degerler: list) -> bool:
    """Belirtilen satırı günceller (1-indexed, başlık=1)."""
    try:
        s, sid = servis()
        s.values().update(
            spreadsheetId=sid,
            range=f"{sekme}!A{satir_no}",
            valueInputOption="RAW",
            body={"values": [degerler]}
        ).execute()
        return True
    except Exception as e:
        logger.error(f"Satır güncelleme hatası ({sekme}, satır {satir_no}): {e}")
        return False
