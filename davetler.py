"""
Davet yonetimi - firma bazli Google Sheets
Her davet: ad_soyad | telefon | durum | davet_tarihi | katilma_tarihi | telegram_id | token
"""

import logging, os, secrets, string
from datetime import date
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SUTUNLAR = ["ad_soyad", "telefon", "durum", "davet_tarihi", "katilma_tarihi", "telegram_id", "token"]
DURUM_BEKLIYOR = "bekliyor"
DURUM_GONDERILDI = "gonderildi"
DURUM_KATILDI = "katildi"


def _get_credentials():
    creds_json = __import__('os').environ.get("GOOGLE_CREDENTIALS_JSON")
    if creds_json:
        try:
            import json as _json
            info = _json.loads(creds_json)
            return Credentials.from_service_account_info(info, scopes=SCOPES)
        except Exception as e:
            pass
    creds_path = __import__('os').environ.get("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    if __import__('os').path.exists(creds_path):
        return Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    raise ValueError("Google credentials bulunamadi!")

def _servis():
    creds = _get_credentials()
    s = build("sheets", "v4", credentials=creds).spreadsheets()
    sid = __import__('os').environ.get("SPREADSHEET_ID")
    return s, sid


def _davet_sekme(firma_id: str = None) -> str:
    if not firma_id or firma_id == "varsayilan":
        return "Davetler"
    return f"Davetler_{firma_id}"


def _sekme_hazirla(firma_id: str = None):
    """Sekme yoksa olustur, baslik ekle."""
    sekme = _davet_sekme(firma_id)
    try:
        s, sid = _servis()
        try:
            s.values().get(spreadsheetId=sid, range=f"{sekme}!A1").execute()
        except:
            s.batchUpdate(spreadsheetId=sid, body={
                "requests": [{"addSheet": {"properties": {"title": sekme}}}]
            }).execute()
        r = s.values().get(spreadsheetId=sid, range=f"{sekme}!A1:G1").execute()
        if not r.get("values"):
            s.values().update(spreadsheetId=sid, range=f"{sekme}!A1",
                valueInputOption="RAW", body={"values": [SUTUNLAR]}).execute()
    except Exception as e:
        logger.warning(f"Sekme hazirla hatasi ({sekme}): {e}")


def _token_uret() -> str:
    alfabe = string.ascii_lowercase + string.digits
    return ''.join(secrets.choice(alfabe) for _ in range(8))


def tum_davetler(firma_id: str = None) -> list:
    sekme = _davet_sekme(firma_id)
    try:
        s, sid = _servis()
        r = s.values().get(spreadsheetId=sid, range=f"{sekme}!A2:G").execute()
        davetler = []
        for i, satir in enumerate(r.get("values", [])):
            if len(satir) < 2: continue
            satir_no = i + 2
            davetler.append({
                "satir_no": satir_no,
                "ad_soyad":      satir[0] if len(satir) > 0 else "",
                "telefon":       satir[1] if len(satir) > 1 else "",
                "durum":         satir[2] if len(satir) > 2 else DURUM_BEKLIYOR,
                "davet_tarihi":  satir[3] if len(satir) > 3 else "",
                "katilma_tarihi":satir[4] if len(satir) > 4 else "",
                "telegram_id":   satir[5] if len(satir) > 5 else "",
                "token":         satir[6] if len(satir) > 6 else "",
            })
        return davetler
    except Exception as e:
        logger.error(f"Davetler okunamadi: {e}")
        return []


def davet_ekle(ad_soyad: str, telefon: str, firma_id: str = None) -> dict:
    """Yeni davet ekle. Ayni telefon varsa hata dondur."""
    _sekme_hazirla(firma_id)
    sekme = _davet_sekme(firma_id)

    # Telefon normalize et
    telefon = telefon.strip().replace(" ", "").replace("-", "")
    if not telefon.startswith("+"):
        if telefon.startswith("0"):
            telefon = "+9" + telefon
        elif telefon.startswith("5"):
            telefon = "+90" + telefon

    # Ayni telefon var mi?
    mevcut = tum_davetler(firma_id)
    for d in mevcut:
        if d["telefon"] == telefon:
            return {"hata": "Bu telefon zaten listede", "mevcut": d}

    token = _token_uret()
    s, sid = _servis()
    s.values().append(
        spreadsheetId=sid, range=f"{sekme}!A1",
        valueInputOption="RAW", insertDataOption="INSERT_ROWS",
        body={"values": [[ad_soyad, telefon, DURUM_BEKLIYOR, "", "", "", token]]}
    ).execute()
    logger.info(f"Davet eklendi: {ad_soyad} {telefon}")
    return {"basarili": True, "token": token}


def davet_gonderildi_isaretle(satir_no: int, firma_id: str = None):
    """Davet gonderildi olarak isaretле."""
    sekme = _davet_sekme(firma_id)
    try:
        s, sid = _servis()
        bugun = date.today().strftime("%d.%m.%Y")
        s.values().update(
            spreadsheetId=sid, range=f"{sekme}!C{satir_no}:D{satir_no}",
            valueInputOption="RAW",
            body={"values": [[DURUM_GONDERILDI, bugun]]}
        ).execute()
    except Exception as e:
        logger.error(f"Davet isaretleme hatasi: {e}")


def davet_katildi_isaretle(token: str, telegram_id: int, firma_id: str = None) -> dict:
    """Token ile kisiyi bul ve katildi olarak isaretle."""
    sekme = _davet_sekme(firma_id)
    try:
        s, sid = _servis()
        r = s.values().get(spreadsheetId=sid, range=f"{sekme}!A2:G").execute()
        bugun = date.today().strftime("%d.%m.%Y")
        for i, satir in enumerate(r.get("values", [])):
            if len(satir) > 6 and satir[6].strip() == token:
                satir_no = i + 2
                s.values().update(
                    spreadsheetId=sid, range=f"{sekme}!C{satir_no}:F{satir_no}",
                    valueInputOption="RAW",
                    body={"values": [[DURUM_KATILDI, satir[3], bugun, str(telegram_id)]]}
                ).execute()
                return {"basarili": True, "ad_soyad": satir[0], "telefon": satir[1]}
        return {"hata": "Token bulunamadi"}
    except Exception as e:
        logger.error(f"Katildi isaretleme hatasi: {e}")
        return {"hata": str(e)}


def token_ile_bul(token: str) -> dict:
    """Tum firmalarda token ara."""
    try:
        from firma_manager import tum_firmalar
        firmalar = list(tum_firmalar().keys()) + [None]
    except:
        firmalar = [None]

    for fid in firmalar:
        davetler = tum_davetler(fid)
        for d in davetler:
            if d.get("token") == token:
                d["firma_id"] = fid or "varsayilan"
                return d
    return {}


def davet_sil(satir_no: int, firma_id: str = None):
    sekme = _davet_sekme(firma_id)
    try:
        s, sid = _servis()
        s.values().clear(spreadsheetId=sid, range=f"{sekme}!A{satir_no}:G{satir_no}").execute()
    except Exception as e:
        logger.error(f"Davet sil hatasi: {e}")
