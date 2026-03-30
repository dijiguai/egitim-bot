"""
Egitim yonetimi - Google Sheets "Egitimler" sekmesi
Her egitim bir satir: id | baslik | tur | sure | metin | sorular_json | firmalar | sira
"""

import json, logging, os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SEKME = "Egitimler"
# sira: eğitim gönderim sırası (1,2,3...), boşsa pozisyon sırası kullanılır
SUTUNLAR = ["id", "baslik", "tur", "sure", "metin", "sorular_json", "firmalar", "sira"]

_cache = None


def _get_credentials():
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if creds_json:
        try:
            return Credentials.from_service_account_info(json.loads(creds_json), scopes=SCOPES)
        except Exception as e:
            pass
    creds_path = os.environ.get("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    if os.path.exists(creds_path):
        return Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    raise ValueError("Google credentials bulunamadi!")


def _servis():
    creds = _get_credentials()
    s = build("sheets", "v4", credentials=creds).spreadsheets()
    sid = os.environ.get("SPREADSHEET_ID")
    return s, sid


def _baslik_kontrol():
    try:
        s, sid = _servis()
        r = s.values().get(spreadsheetId=sid, range=f"{SEKME}!A1:H1").execute()
        degerler = r.get("values", [[]])[0] if r.get("values") else []
        if not degerler:
            s.values().update(spreadsheetId=sid, range=f"{SEKME}!A1",
                valueInputOption="RAW", body={"values": [SUTUNLAR]}).execute()
        elif len(degerler) < 8:
            # Eski format — sira sütunu ekle
            s.values().update(spreadsheetId=sid, range=f"{SEKME}!H1",
                valueInputOption="RAW", body={"values": [["sira"]]}).execute()
            logger.info("Egitimler: sira sutunu eklendi")
    except Exception as e:
        logger.warning(f"Baslik kontrol: {e}")


def tum_egitimler(sirali=True) -> dict:
    """Sheets'ten { egitim_id: {...} } dict döndür. sirali=True ise sıra alanına göre."""
    global _cache
    try:
        s, sid = _servis()
        r = s.values().get(spreadsheetId=sid, range=f"{SEKME}!A2:H").execute()
        satirlar = r.get("values", [])
        egitimler_liste = []
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
            firmalar_str = satir[6] if len(satir) > 6 else ""
            sira_str = satir[7] if len(satir) > 7 else ""
            try:
                sira = int(sira_str) if sira_str.strip() else 9999
            except:
                sira = 9999

            egitimler_liste.append((sira, eid, {
                "baslik":   satir[1] if len(satir) > 1 else "",
                "tur":      satir[2] if len(satir) > 2 else "",
                "sure":     satir[3] if len(satir) > 3 else "",
                "metin":    satir[4] if len(satir) > 4 else "",
                "sorular":  sorular,
                "firmalar": [f.strip() for f in firmalar_str.split(",") if f.strip()] if firmalar_str else [],
                "sira":     sira
            }))

        if sirali:
            egitimler_liste.sort(key=lambda x: x[0])

        egitimler = {eid: e for _, eid, e in egitimler_liste}
        _cache = egitimler
        return egitimler
    except Exception as e:
        logger.error(f"Egitimler okunamadi: {e}")
        return _cache or {}


def egitim_ekle(eid: str, baslik: str, tur: str, sure: str, metin: str,
                sorular: list, firmalar: list = None, sira: int = None):
    _baslik_kontrol()
    s, sid = _servis()
    firmalar_str = ",".join(firmalar) if firmalar else ""
    # Sıra belirlenmemişse en sona ekle
    if sira is None:
        mevcut = tum_egitimler(sirali=True)
        siralar = [e.get("sira", 0) for e in mevcut.values() if e.get("sira", 9999) < 9999]
        sira = (max(siralar) + 1) if siralar else 1
    deger = [[eid, baslik, tur, sure, metin, json.dumps(sorular, ensure_ascii=False), firmalar_str, str(sira)]]
    s.values().append(spreadsheetId=sid, range=f"{SEKME}!A1",
        valueInputOption="RAW", insertDataOption="INSERT_ROWS",
        body={"values": deger}).execute()
    logger.info(f"Egitim eklendi: {eid} (sira={sira})")
    tum_egitimler()  # cache yenile


def egitim_sira_guncelle(eid: str, yeni_sira: int) -> bool:
    """Eğitimin gönderim sırasını günceller."""
    try:
        s, sid = _servis()
        r = s.values().get(spreadsheetId=sid, range=f"{SEKME}!A2:H").execute()
        for i, satir in enumerate(r.get("values", [])):
            if satir and satir[0].strip() == eid:
                satir_no = i + 2
                mevcut = list(satir) + [""] * (8 - len(satir))
                mevcut[7] = str(yeni_sira)
                s.values().update(spreadsheetId=sid, range=f"{SEKME}!A{satir_no}",
                    valueInputOption="RAW", body={"values": [mevcut]}).execute()
                global _cache
                _cache = None
                return True
        return False
    except Exception as e:
        logger.error(f"Sira guncelleme hatasi: {e}")
        return False


def egitim_guncelle(eid: str, baslik: str = None, tur: str = None, sure: str = None):
    try:
        s, sid = _servis()
        r = s.values().get(spreadsheetId=sid, range=f"{SEKME}!A2:H").execute()
        for i, satir in enumerate(r.get("values", [])):
            if satir and satir[0].strip() == eid:
                satir_no = i + 2
                mevcut = list(satir) + [""] * (8 - len(satir))
                if baslik: mevcut[1] = baslik
                if tur:    mevcut[2] = tur
                if sure:   mevcut[3] = sure
                s.values().update(spreadsheetId=sid, range=f"{SEKME}!A{satir_no}",
                    valueInputOption="RAW", body={"values": [mevcut]}).execute()
                tum_egitimler()
                return True
        return False
    except Exception as e:
        logger.error(f"Egitim guncelleme hatasi: {e}")
        return False


def egitim_sil(eid: str) -> bool:
    try:
        s, sid = _servis()
        r = s.values().get(spreadsheetId=sid, range=f"{SEKME}!A2:A").execute()
        for i, satir in enumerate(r.get("values", [])):
            if satir and satir[0].strip() == eid:
                satir_no = i + 2
                s.values().clear(spreadsheetId=sid,
                    range=f"{SEKME}!A{satir_no}:H{satir_no}").execute()
                tum_egitimler()
                logger.info(f"Egitim silindi: {eid}")
                return True
        return False
    except Exception as e:
        logger.error(f"Egitim silme hatasi: {e}")
        return False


def egitim_guncelle_tam(eid: str, baslik=None, tur=None, sure=None,
                         metin=None, sorular=None, firmalar=None, sira=None):
    try:
        s, sid = _servis()
        r = s.values().get(spreadsheetId=sid, range=f"{SEKME}!A2:H").execute()
        for i, satir in enumerate(r.get("values", [])):
            if satir and satir[0].strip() == eid:
                satir_no = i + 2
                mevcut = list(satir) + [""] * (8 - len(satir))
                if baslik   is not None: mevcut[1] = baslik
                if tur      is not None: mevcut[2] = tur
                if sure     is not None: mevcut[3] = sure
                if metin    is not None: mevcut[4] = metin
                if sorular  is not None: mevcut[5] = json.dumps(sorular, ensure_ascii=False)
                if firmalar is not None: mevcut[6] = ",".join(firmalar)
                if sira     is not None: mevcut[7] = str(sira)
                s.values().update(spreadsheetId=sid, range=f"{SEKME}!A{satir_no}",
                    valueInputOption="RAW", body={"values": [mevcut]}).execute()
                tum_egitimler()
                return True
        return False
    except Exception as e:
        logger.error(f"Egitim tam guncelleme hatasi: {e}")
        return False


def tum_egitimler_firma(firma_id: str) -> dict:
    tum = tum_egitimler()
    return {eid: e for eid, e in tum.items()
            if not e.get("firmalar") or firma_id in e.get("firmalar", [])}


def egitimler_sirali_liste() -> list:
    """Sıra numarasına göre sıralı [(sira, eid, baslik)] listesi."""
    egitimler = tum_egitimler(sirali=True)
    return [(e.get("sira", idx+1), eid, e.get("baslik", ""))
            for idx, (eid, e) in enumerate(egitimler.items())]


def config_egitimlerini_sheets_e_yukle(config_egitimler: dict):
    _baslik_kontrol()
    mevcut = tum_egitimler()
    eklenen = 0
    for idx, (eid, e) in enumerate(config_egitimler.items()):
        if eid not in mevcut:
            egitim_ekle(eid, e["baslik"], e["tur"], e["sure"],
                        e["metin"], e["sorular"], sira=idx+1)
            eklenen += 1
    logger.info(f"Config'den {eklenen} egitim Sheets'e yuklendi")
    return eklenen
