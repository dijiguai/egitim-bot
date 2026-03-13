"""
Calisan yonetimi - Google Sheets Calisanlar sekmesi
Telegram ID opsiyonel - dogum tarihi ile eslestirme yapilabilir
"""

import logging, os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SEKME = "Calisanlar"
SUTUNLAR = ["telegram_id", "ad_soyad", "dogum_tarihi", "gorev", "aktif"]


def _to_int(val):
    """Guvenli int donusumu - None, bos string, 'None' string hepsini None yapar."""
    if val is None:
        return None
    s = str(val).strip()
    if s in ("", "None", "null", "0"):
        return None
    try:
        return int(s)
    except (ValueError, TypeError):
        return None


def _servis():
    creds = Credentials.from_service_account_file(
        os.environ.get("GOOGLE_CREDENTIALS_PATH", "credentials.json"), scopes=SCOPES)
    s = build("sheets", "v4", credentials=creds).spreadsheets()
    sid = os.environ.get("SPREADSHEET_ID")
    return s, sid


def _baslik_kontrol():
    try:
        s, sid = _servis()
        r = s.values().get(spreadsheetId=sid, range=f"{SEKME}!A1:E1").execute()
        if not r.get("values"):
            s.values().update(spreadsheetId=sid, range=f"{SEKME}!A1",
                valueInputOption="RAW", body={"values": [SUTUNLAR]}).execute()
    except Exception as e:
        logger.warning(f"Baslik kontrol: {e}")


def tum_calisanlar() -> dict:
    try:
        s, sid = _servis()
        r = s.values().get(spreadsheetId=sid, range=f"{SEKME}!A2:E").execute()
        satirlar = r.get("values", [])
        calisanlar = {}
        for i, satir in enumerate(satirlar):
            if len(satir) < 3:
                continue
            aktif = satir[4] if len(satir) > 4 else "1"
            if aktif == "0":
                continue
            tid_str = satir[0].strip() if satir[0] else ""
            tid = _to_int(tid_str)
            key = tid if tid else -(i + 1)
            calisanlar[key] = {
                "ad_soyad":     satir[1] if len(satir) > 1 else "",
                "dogum_tarihi": satir[2] if len(satir) > 2 else "",
                "gorev":        satir[3] if len(satir) > 3 else "",
                "aktif": True
            }
        return calisanlar
    except Exception as e:
        logger.error(f"Calisanlar okunamadi: {e}")
        return {}


def calisan_bul(telegram_id) -> dict:
    tid = _to_int(telegram_id)
    if not tid:
        return None
    return tum_calisanlar().get(tid)


def calisan_bul_dogum(dogum_tarihi: str) -> tuple:
    for tid, c in tum_calisanlar().items():
        if c.get("dogum_tarihi") == dogum_tarihi:
            return tid, c
    return None, None


def telegram_id_guncelle(dogum_tarihi: str, telegram_id: int):
    try:
        s, sid = _servis()
        r = s.values().get(spreadsheetId=sid, range=f"{SEKME}!A2:E").execute()
        satirlar = r.get("values", [])
        for i, satir in enumerate(satirlar):
            if len(satir) > 2 and satir[2].strip() == dogum_tarihi:
                satir_no = i + 2
                s.values().update(
                    spreadsheetId=sid,
                    range=f"{SEKME}!A{satir_no}",
                    valueInputOption="RAW",
                    body={"values": [[str(telegram_id)]]}
                ).execute()
                logger.info(f"Telegram ID guncellendi: {dogum_tarihi} -> {telegram_id}")
                return True
        return False
    except Exception as e:
        logger.error(f"ID guncelleme hatasi: {e}")
        return False


def _satir_bul(telegram_id) -> int:
    tid = _to_int(telegram_id)
    if not tid:
        return None
    try:
        s, sid = _servis()
        r = s.values().get(spreadsheetId=sid, range=f"{SEKME}!A2:A").execute()
        for i, satir in enumerate(r.get("values", [])):
            if satir and str(satir[0]).strip() == str(tid):
                return i + 2
    except Exception as e:
        logger.error(f"Satir bulunamadi: {e}")
    return None


def calisan_ekle(telegram_id, ad_soyad: str, dogum_tarihi: str, gorev: str):
    _baslik_kontrol()
    tid = _to_int(telegram_id)
    tid_str = str(tid) if tid else ""
    satir_no = _satir_bul(tid) if tid else None
    s, sid = _servis()
    deger = [[tid_str, ad_soyad, dogum_tarihi, gorev, "1"]]
    if satir_no:
        s.values().update(spreadsheetId=sid, range=f"{SEKME}!A{satir_no}",
            valueInputOption="RAW", body={"values": deger}).execute()
    else:
        s.values().append(spreadsheetId=sid, range=f"{SEKME}!A1",
            valueInputOption="RAW", insertDataOption="INSERT_ROWS",
            body={"values": deger}).execute()
    logger.info(f"Calisan eklendi: {ad_soyad}")


def calisan_guncelle(telegram_id, ad_soyad: str, dogum_tarihi: str, gorev: str):
    calisan_ekle(telegram_id, ad_soyad, dogum_tarihi, gorev)


def calisan_sil(telegram_id):
    tid = _to_int(telegram_id)
    if not tid:
        return
    satir_no = _satir_bul(tid)
    if not satir_no:
        return
    s, sid = _servis()
    r = s.values().get(spreadsheetId=sid, range=f"{SEKME}!A{satir_no}:E{satir_no}").execute()
    satirlar = r.get("values", [[]])
    if satirlar and len(satirlar[0]) >= 4:
        satirlar[0] = satirlar[0][:4] + ["0"]
        s.values().update(spreadsheetId=sid, range=f"{SEKME}!A{satir_no}",
            valueInputOption="RAW", body={"values": satirlar}).execute()
