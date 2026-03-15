"""
Calisan yonetimi - firma bazli Google Sheets
"""

import logging, os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SUTUNLAR = ["telegram_id", "ad_soyad", "dogum_tarihi", "gorev", "aktif"]


def _to_int(val):
    if val is None: return None
    s = str(val).strip()
    if s in ("", "None", "null", "0"): return None
    try: return int(s)
    except: return None


def _servis():
    creds = Credentials.from_service_account_file(
        os.environ.get("GOOGLE_CREDENTIALS_PATH", "credentials.json"), scopes=SCOPES)
    s = build("sheets", "v4", credentials=creds).spreadsheets()
    sid = os.environ.get("SPREADSHEET_ID")
    return s, sid


def _calisanlar_sekme(firma_id: str = None) -> str:
    if not firma_id or firma_id == "varsayilan":
        return "Calisanlar"
    try:
        from firma_manager import tum_firmalar
        f = tum_firmalar().get(firma_id, {})
        return f.get("calisanlar_sekme", f"Calisanlar_{firma_id}")
    except:
        return "Calisanlar"


def _baslik_kontrol(sekme: str):
    try:
        s, sid = _servis()
        r = s.values().get(spreadsheetId=sid, range=f"{sekme}!A1:E1").execute()
        if not r.get("values"):
            s.values().update(spreadsheetId=sid, range=f"{sekme}!A1",
                valueInputOption="RAW", body={"values": [SUTUNLAR]}).execute()
    except Exception as e:
        logger.warning(f"Baslik kontrol ({sekme}): {e}")


def tum_calisanlar(firma_id: str = None) -> dict:
    sekme = _calisanlar_sekme(firma_id)
    try:
        s, sid = _servis()
        r = s.values().get(spreadsheetId=sid, range=f"{sekme}!A2:E").execute()
        calisanlar = {}
        for i, satir in enumerate(r.get("values", [])):
            if len(satir) < 3: continue
            aktif = satir[4] if len(satir) > 4 else "1"
            if aktif == "0": continue
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
        logger.error(f"Calisanlar okunamadi ({sekme}): {e}")
        return {}


def calisan_bul(telegram_id, firma_id: str = None) -> dict:
    tid = _to_int(telegram_id)
    if not tid: return None
    return tum_calisanlar(firma_id).get(tid)


def calisan_bul_dogum(dogum_tarihi: str, firma_id: str = None) -> tuple:
    for tid, c in tum_calisanlar(firma_id).items():
        if c.get("dogum_tarihi") == dogum_tarihi:
            return tid, c
    return None, None


def calisan_bul_tum_firmalar(telegram_id) -> tuple:
    """Tum firmalarda ara, bulunan firma_id ve calisan_dict dondur."""
    tid = _to_int(telegram_id)
    if not tid: return None, None
    try:
        from firma_manager import tum_firmalar
        for fid in tum_firmalar():
            c = calisan_bul(tid, fid)
            if c:
                return fid, c
    except:
        c = calisan_bul(tid, None)
        if c: return "varsayilan", c
    return None, None


def calisan_bul_dogum_tum_firmalar(dogum_tarihi: str) -> tuple:
    """Tum firmalarda dogum tarihi ile ara."""
    try:
        from firma_manager import tum_firmalar
        for fid in tum_firmalar():
            tid, c = calisan_bul_dogum(dogum_tarihi, fid)
            if c:
                return fid, tid, c
    except:
        tid, c = calisan_bul_dogum(dogum_tarihi, None)
        if c: return "varsayilan", tid, c
    return None, None, None


def telegram_id_guncelle(dogum_tarihi: str, telegram_id: int, firma_id: str = None):
    sekme = _calisanlar_sekme(firma_id)
    try:
        s, sid = _servis()
        r = s.values().get(spreadsheetId=sid, range=f"{sekme}!A2:E").execute()
        for i, satir in enumerate(r.get("values", [])):
            if len(satir) > 2 and satir[2].strip() == dogum_tarihi:
                satir_no = i + 2
                s.values().update(spreadsheetId=sid, range=f"{sekme}!A{satir_no}",
                    valueInputOption="RAW", body={"values": [[str(telegram_id)]]}).execute()
                return True
        return False
    except Exception as e:
        logger.error(f"ID guncelleme hatasi: {e}")
        return False


def _satir_bul(telegram_id, sekme: str):
    tid = _to_int(telegram_id)
    if not tid: return None
    try:
        s, sid = _servis()
        r = s.values().get(spreadsheetId=sid, range=f"{sekme}!A2:A").execute()
        for i, satir in enumerate(r.get("values", [])):
            if satir and str(satir[0]).strip() == str(tid):
                return i + 2
    except:
        pass
    return None


def calisan_ekle(telegram_id, ad_soyad: str, dogum_tarihi: str, gorev: str, firma_id: str = None):
    sekme = _calisanlar_sekme(firma_id)
    _baslik_kontrol(sekme)
    tid = _to_int(telegram_id)
    tid_str = str(tid) if tid else "0"
    satir_no = _satir_bul(tid, sekme) if tid else None
    s, sid = _servis()
    deger = [[tid_str, ad_soyad, dogum_tarihi, gorev, "1"]]
    if satir_no:
        s.values().update(spreadsheetId=sid, range=f"{sekme}!A{satir_no}",
            valueInputOption="RAW", body={"values": deger}).execute()
    else:
        s.values().append(spreadsheetId=sid, range=f"{sekme}!A1",
            valueInputOption="RAW", insertDataOption="INSERT_ROWS",
            body={"values": deger}).execute()
    logger.info(f"Calisan eklendi: {ad_soyad} -> {sekme}")


def calisan_guncelle(telegram_id, ad_soyad: str, dogum_tarihi: str, gorev: str, firma_id: str = None):
    calisan_ekle(telegram_id, ad_soyad, dogum_tarihi, gorev, firma_id)


def calisan_sil(telegram_id, firma_id: str = None):
    sekme = _calisanlar_sekme(firma_id)
    tid = _to_int(telegram_id)
    satir_no = _satir_bul(tid, sekme)
    if not satir_no: return
    s, sid = _servis()
    r = s.values().get(spreadsheetId=sid, range=f"{sekme}!A{satir_no}:E{satir_no}").execute()
    satirlar = r.get("values", [[]])
    if satirlar and len(satirlar[0]) >= 4:
        satirlar[0] = satirlar[0][:4] + ["0"]
        s.values().update(spreadsheetId=sid, range=f"{sekme}!A{satir_no}",
            valueInputOption="RAW", body={"values": satirlar}).execute()
