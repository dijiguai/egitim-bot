"""
Egitim yonetimi - Google Sheets "Egitimler" sekmesi
Her egitim bir satir: id | baslik | tur | sure | metin | sorular_json
"""

import json, logging, os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SEKME = "Egitimler"
SUTUNLAR = ["id", "baslik", "tur", "sure", "metin", "sorular_json"]

_cache = None  # Bellekte tutuyoruz, her istekte Sheets'e gitmeyelim


def _servis():
    creds = Credentials.from_service_account_file(
        os.environ.get("GOOGLE_CREDENTIALS_PATH", "credentials.json"), scopes=SCOPES)
    s = build("sheets", "v4", credentials=creds).spreadsheets()
    sid = os.environ.get("SPREADSHEET_ID")
    return s, sid


def _baslik_kontrol():
    try:
        s, sid = _servis()
        r = s.values().get(spreadsheetId=sid, range=f"{SEKME}!A1:F1").execute()
        if not r.get("values"):
            s.values().update(spreadsheetId=sid, range=f"{SEKME}!A1",
                valueInputOption="RAW", body={"values": [SUTUNLAR]}).execute()
            logger.info("Egitimler sekmesi baslik eklendi")
    except Exception as e:
        logger.warning(f"Baslik kontrol: {e}")


def tum_egitimler() -> dict:
    """Sheets'ten { egitim_id: {...} } dict dondur."""
    global _cache
    try:
        s, sid = _servis()
        r = s.values().get(spreadsheetId=sid, range=f"{SEKME}!A2:F").execute()
        satirlar = r.get("values", [])
        egitimler = {}
        for satir in satirlar:
            if len(satir) < 2:
                continue
            eid = satir[0].strip()
            if not eid:
                continue
            try:
                sorular = json.loads(satir[5]) if len(satir) > 5 and satir[5] else []
            except:
                sorular = []
            egitimler[eid] = {
                "baslik": satir[1] if len(satir) > 1 else "",
                "tur":    satir[2] if len(satir) > 2 else "",
                "sure":   satir[3] if len(satir) > 3 else "",
                "metin":  satir[4] if len(satir) > 4 else "",
                "sorular": sorular
            }
        _cache = egitimler
        return egitimler
    except Exception as e:
        logger.error(f"Egitimler okunamadi: {e}")
        return _cache or {}


def egitim_ekle(eid: str, baslik: str, tur: str, sure: str, metin: str, sorular: list):
    _baslik_kontrol()
    s, sid = _servis()
    deger = [[eid, baslik, tur, sure, metin, json.dumps(sorular, ensure_ascii=False)]]
    s.values().append(spreadsheetId=sid, range=f"{SEKME}!A1",
        valueInputOption="RAW", insertDataOption="INSERT_ROWS",
        body={"values": deger}).execute()
    logger.info(f"Egitim eklendi: {eid}")
    tum_egitimler()  # cache yenile


def egitim_guncelle(eid: str, baslik: str = None, tur: str = None, sure: str = None):
    """Baslik/tur/sure guncelle (metin ve sorular degismez)."""
    try:
        s, sid = _servis()
        r = s.values().get(spreadsheetId=sid, range=f"{SEKME}!A2:F").execute()
        satirlar = r.get("values", [])
        for i, satir in enumerate(satirlar):
            if satir and satir[0].strip() == eid:
                satir_no = i + 2
                mevcut = list(satir) + [""] * (6 - len(satir))
                if baslik: mevcut[1] = baslik
                if tur:    mevcut[2] = tur
                if sure:   mevcut[3] = sure
                s.values().update(spreadsheetId=sid,
                    range=f"{SEKME}!A{satir_no}",
                    valueInputOption="RAW",
                    body={"values": [mevcut[:6]]}).execute()
                tum_egitimler()
                return True
        return False
    except Exception as e:
        logger.error(f"Egitim guncelleme hatasi: {e}")
        return False


def egitim_sil(eid: str) -> bool:
    """Egitimi sil (satiri temizle)."""
    try:
        s, sid = _servis()
        r = s.values().get(spreadsheetId=sid, range=f"{SEKME}!A2:A").execute()
        for i, satir in enumerate(r.get("values", [])):
            if satir and satir[0].strip() == eid:
                satir_no = i + 2
                # Satiri bos yap
                s.values().clear(spreadsheetId=sid,
                    range=f"{SEKME}!A{satir_no}:F{satir_no}").execute()
                tum_egitimler()
                logger.info(f"Egitim silindi: {eid}")
                return True
        return False
    except Exception as e:
        logger.error(f"Egitim silme hatasi: {e}")
        return False


def egitim_guncelle_tam(eid: str, baslik=None, tur=None, sure=None, metin=None, sorular=None):
    """Tum alanlari guncelle."""
    try:
        s, sid = _servis()
        r = s.values().get(spreadsheetId=sid, range=f"{SEKME}!A2:F").execute()
        satirlar = r.get("values", [])
        for i, satir in enumerate(satirlar):
            if satir and satir[0].strip() == eid:
                satir_no = i + 2
                mevcut = list(satir) + [""] * (6 - len(satir))
                if baslik  is not None: mevcut[1] = baslik
                if tur     is not None: mevcut[2] = tur
                if sure    is not None: mevcut[3] = sure
                if metin   is not None: mevcut[4] = metin
                if sorular is not None: mevcut[5] = json.dumps(sorular, ensure_ascii=False)
                s.values().update(spreadsheetId=sid,
                    range=f"{SEKME}!A{satir_no}",
                    valueInputOption="RAW",
                    body={"values": [mevcut[:6]]}).execute()
                tum_egitimler()  # cache yenile
                return True
        return False
    except Exception as e:
        logger.error(f"Egitim tam guncelleme hatasi: {e}")
        return False


def config_egitimlerini_sheets_e_yukle(config_egitimler: dict):
    """
    Ilk kurulumda config.py'deki egitimler Sheets'e aktarilir.
    Zaten varsa atlanir.
    """
    _baslik_kontrol()
    mevcut = tum_egitimler()
    eklenen = 0
    for eid, e in config_egitimler.items():
        if eid not in mevcut:
            egitim_ekle(eid, e["baslik"], e["tur"], e["sure"],
                        e["metin"], e["sorular"])
            eklenen += 1
    logger.info(f"Config'den {eklenen} egitim Sheets'e yuklendi")
    return eklenen
