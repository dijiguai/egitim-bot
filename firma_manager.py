"""
Firma yonetimi - Google Sheets "Firmalar" sekmesi
Her firma: id | ad | grup_id | kayitlar_sekme | calisanlar_sekme | aktif
"""

import json, logging, os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
FIRMALAR_SEKME = "Firmalar"
SUTUNLAR = ["firma_id", "ad", "grup_id", "kayitlar_sekme", "calisanlar_sekme", "aktif"]

_cache = None  # { firma_id: {...} }


def _servis():
    creds = Credentials.from_service_account_file(
        os.environ.get("GOOGLE_CREDENTIALS_PATH", "credentials.json"), scopes=SCOPES)
    s = build("sheets", "v4", credentials=creds).spreadsheets()
    sid = os.environ.get("SPREADSHEET_ID")
    return s, sid


def _baslik_kontrol():
    """Firmalar sekmesi yoksa olustur, baslik yoksa ekle."""
    try:
        s, sid = _servis()
        # Once sekmenin var olup olmadigini kontrol et
        mevcut = _mevcut_sekmeler()
        if FIRMALAR_SEKME not in mevcut:
            # Sekmeyi olustur
            s.batchUpdate(spreadsheetId=sid, body={
                "requests": [{"addSheet": {"properties": {"title": FIRMALAR_SEKME}}}]
            }).execute()
            logger.info(f"'{FIRMALAR_SEKME}' sekmesi olusturuldu")

        # Baslik satiri ekle
        r = s.values().get(spreadsheetId=sid, range=f"{FIRMALAR_SEKME}!A1:F1").execute()
        if not r.get("values"):
            s.values().update(spreadsheetId=sid, range=f"{FIRMALAR_SEKME}!A1",
                valueInputOption="RAW", body={"values": [SUTUNLAR]}).execute()
    except Exception as e:
        logger.warning(f"Firmalar baslik: {e}")


def tum_firmalar(force=False) -> dict:
    """{ firma_id: {ad, grup_id, kayitlar_sekme, calisanlar_sekme, aktif} }"""
    global _cache
    if _cache is not None and not force:
        return _cache
    try:
        s, sid = _servis()
        r = s.values().get(spreadsheetId=sid, range=f"{FIRMALAR_SEKME}!A2:F").execute()
        firmalar = {}
        for satir in r.get("values", []):
            if len(satir) < 3:
                continue
            aktif = satir[5] if len(satir) > 5 else "1"
            if aktif == "0":
                continue
            fid = satir[0].strip()
            firmalar[fid] = {
                "ad":               satir[1] if len(satir) > 1 else "",
                "grup_id":          int(satir[2]) if len(satir) > 2 and satir[2] else 0,
                "kayitlar_sekme":   satir[3] if len(satir) > 3 else f"Kayitlar_{fid}",
                "calisanlar_sekme": satir[4] if len(satir) > 4 else f"Calisanlar_{fid}",
                "aktif": True
            }
        _cache = firmalar
        return firmalar
    except Exception as e:
        logger.error(f"Firmalar okunamadi: {e}")
        return _cache or {}


def grup_id_den_firma(grup_id: int) -> tuple:
    """Grup ID'sine gore firma bul. (firma_id, firma_dict)"""
    for fid, f in tum_firmalar().items():
        if str(f.get("grup_id","")) == str(grup_id):
            return fid, f
    return None, None


def firma_ekle(firma_id: str, ad: str, grup_id: int) -> bool:
    """
    Yeni firma ekle + Sheets'te gerekli sekmeleri olustur.
    """
    _baslik_kontrol()
    kayitlar_sekme = f"Kayitlar_{firma_id}"
    calisanlar_sekme = f"Calisanlar_{firma_id}"

    s, sid = _servis()

    # Zaten var mi? (duplicate onle)
    r_kontrol = s.values().get(spreadsheetId=sid, range=f"{FIRMALAR_SEKME}!A2:A").execute()
    for satir in r_kontrol.get("values", []):
        if satir and satir[0].strip() == firma_id:
            logger.warning(f"Firma zaten var: {firma_id}")
            return False

    # Firmalar sekmesine ekle
    s.values().append(
        spreadsheetId=sid, range=f"{FIRMALAR_SEKME}!A1",
        valueInputOption="RAW", insertDataOption="INSERT_ROWS",
        body={"values": [[firma_id, ad, str(grup_id), kayitlar_sekme, calisanlar_sekme, "1"]]}
    ).execute()

    # Sheets'te yeni sekmeler olustur
    mevcut_sekmeler = _mevcut_sekmeler()
    eklenecekler = []

    if kayitlar_sekme not in mevcut_sekmeler:
        eklenecekler.append(kayitlar_sekme)
    if calisanlar_sekme not in mevcut_sekmeler:
        eklenecekler.append(calisanlar_sekme)

    if eklenecekler:
        requests = [{"addSheet": {"properties": {"title": t}}} for t in eklenecekler]
        s.batchUpdate(spreadsheetId=sid, body={"requests": requests}).execute()

    # Baslik satirlarini ekle
    _sekme_baslik_ekle(s, sid, kayitlar_sekme, [
        "tarih", "saat", "ad_soyad", "telegram_id",
        "gorev", "egitim_konusu", "egitim_turu",
        "puan", "durum", "kimlik_dogrulandi", "dogum_yili", "deneme_no"
    ])
    _sekme_baslik_ekle(s, sid, calisanlar_sekme, [
        "telegram_id", "ad_soyad", "dogum_tarihi", "gorev", "aktif"
    ])

    # Cache'i yenile
    global _cache
    _cache = None
    tum_firmalar(force=True)
    logger.info(f"Firma eklendi: {ad} ({firma_id}), grup: {grup_id}")
    return True


def firma_sil(firma_id: str):
    """Firmay aktif=0 yap."""
    try:
        s, sid = _servis()
        r = s.values().get(spreadsheetId=sid, range=f"{FIRMALAR_SEKME}!A2:A").execute()
        for i, satir in enumerate(r.get("values", [])):
            if satir and satir[0].strip() == firma_id:
                satir_no = i + 2
                s.values().update(
                    spreadsheetId=sid, range=f"{FIRMALAR_SEKME}!F{satir_no}",
                    valueInputOption="RAW", body={"values": [["0"]]}
                ).execute()
                global _cache
                _cache = None
                tum_firmalar(force=True)
                return True
        return False
    except Exception as e:
        logger.error(f"Firma silme hatasi: {e}")
        return False


def _mevcut_sekmeler() -> list:
    try:
        s, sid = _servis()
        meta = s.get(spreadsheetId=sid).execute()
        return [sheet["properties"]["title"] for sheet in meta.get("sheets", [])]
    except:
        return []


def _sekme_baslik_ekle(s, sid, sekme_adi, basliklar):
    try:
        r = s.values().get(spreadsheetId=sid, range=f"{sekme_adi}!A1:A1").execute()
        if not r.get("values"):
            s.values().update(
                spreadsheetId=sid, range=f"{sekme_adi}!A1",
                valueInputOption="RAW", body={"values": [basliklar]}
            ).execute()
    except Exception as e:
        logger.warning(f"Baslik eklenemedi {sekme_adi}: {e}")


def varsayilan_firma_id() -> str:
    """Eski sistemi (Calisanlar + Sayfa1) kullanan varsayilan firma."""
    return "varsayilan"


def varsayilan_firma_kontrol():
    """
    Eski sekmeleri (Calisanlar, Sayfa1) kullanan varsayilan firmay
    Firmalar listesine ekle (yoksa).
    """
    firmalar = tum_firmalar(force=True)
    if "varsayilan" not in firmalar:
        _baslik_kontrol()
        s, sid = _servis()
        from config import GRUP_ID
        s.values().append(
            spreadsheetId=sid, range=f"{FIRMALAR_SEKME}!A1",
            valueInputOption="RAW", insertDataOption="INSERT_ROWS",
            body={"values": [["varsayilan", "Varsayılan", str(GRUP_ID), "Sayfa1", "Calisanlar", "1"]]}
        ).execute()
        tum_firmalar(force=True)
        logger.info("Varsayilan firma Firmalar listesine eklendi")
