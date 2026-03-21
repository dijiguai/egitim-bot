"""
Egitim sirasi, izin, aktif egitim ve deneme hakki yonetimi
"""

import json, os, logging
from datetime import date

logger = logging.getLogger(__name__)
DOSYA = "durum.json"


def _oku() -> dict:
    if os.path.exists(DOSYA):
        try:
            with open(DOSYA, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {
        "egitim_index": 0,
        "son_tarih": "",
        "izinler": {},
        "tamamlananlar": {},
        "aktif": None,
        "bugun_tamamlayanlar": {},
        "gunluk_haklar": {}   # { "tarih": { "user_id": { "kalan": 1, "deneme": 0 } } }
    }


def _yaz(d: dict):
    with open(DOSYA, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


def _bugun():
    return date.today().strftime("%d.%m.%Y")


# ── DENEME HAKKI ────────────────────────────────────────────

def deneme_hakki_al(user_id: int) -> dict:
    """
    Bugunun deneme durumunu dondur.
    { kalan: int, deneme: int }
    """
    d = _oku()
    bugun = _bugun()
    haklar = d.setdefault("gunluk_haklar", {}).setdefault(bugun, {})
    k = str(user_id)
    if k not in haklar:
        haklar[k] = {"kalan": 1, "deneme": 0}
        _yaz(d)
    return haklar[k]


def deneme_kullan(user_id: int):
    """Bir deneme hakki kullan."""
    d = _oku()
    bugun = _bugun()
    haklar = d.setdefault("gunluk_haklar", {}).setdefault(bugun, {})
    k = str(user_id)
    if k not in haklar:
        haklar[k] = {"kalan": 1, "deneme": 0}
    haklar[k]["kalan"] = max(0, haklar[k]["kalan"] - 1)
    haklar[k]["deneme"] = haklar[k].get("deneme", 0) + 1
    _yaz(d)


def ekstra_hak_ver(user_id: int):
    """Admin 1 ekstra deneme hakki verir."""
    d = _oku()
    bugun = _bugun()
    haklar = d.setdefault("gunluk_haklar", {}).setdefault(bugun, {})
    k = str(user_id)
    if k not in haklar:
        haklar[k] = {"kalan": 0, "deneme": 0}
    haklar[k]["kalan"] += 1
    _yaz(d)
    logger.info(f"Ekstra hak verildi: {user_id}")


def hak_var_mi(user_id: int) -> bool:
    """Bugün hak kaldi mi?"""
    return deneme_hakki_al(user_id)["kalan"] > 0


def kacinci_deneme(user_id: int) -> int:
    """Kacinci denemede oldugunu dondur."""
    return deneme_hakki_al(user_id).get("deneme", 0) + 1


# ── EGITIM SIRASI ──────────────────────────────────────────

def _sheets_index_oku() -> dict:
    """Sheets'ten egitim_index ve son_tarih oku."""
    try:
        from sheets import _servis
        s, sid = _servis()
        r = s.values().get(spreadsheetId=sid, range="Ayarlar!A1:D20").execute()
        satirlar = r.get("values", [])
        ayarlar = {}
        for satir in satirlar:
            if len(satir) >= 2:
                ayarlar[satir[0]] = satir[1]
        return ayarlar
    except:
        return {}


def _sheets_index_yaz(egitim_index: int, son_tarih: str):
    """Sheets'e egitim_index ve son_tarih yaz."""
    try:
        from sheets import _servis
        s, sid = _servis()
        # Ayarlar sekmesi yoksa olustur
        try:
            s.values().get(spreadsheetId=sid, range="Ayarlar!A1").execute()
        except:
            s.batchUpdate(spreadsheetId=sid, body={
                "requests": [{"addSheet": {"properties": {"title": "Ayarlar"}}}]
            }).execute()
        s.values().update(
            spreadsheetId=sid, range="Ayarlar!A1:B2",
            valueInputOption="RAW",
            body={"values": [
                ["egitim_index", str(egitim_index)],
                ["son_tarih", son_tarih]
            ]}
        ).execute()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Sheets index yazma hatasi: {e}")


def siradaki_egitim_al():
    from config import EGITIMLER
    liste = list(EGITIMLER.keys())
    if not liste:
        return None, None
    bugun = _bugun()

    # Once Sheets'ten oku, yoksa durum.json'a bak
    ayarlar = _sheets_index_oku()
    son_tarih = ayarlar.get("son_tarih") or _oku().get("son_tarih", "")
    egitim_index = int(ayarlar.get("egitim_index", _oku().get("egitim_index", 0)))

    if son_tarih == bugun:
        # Bugun zaten secildi - ayni egitimi dondur
        idx = (egitim_index - 1) % len(liste)
        eid = liste[idx]
        return eid, EGITIMLER[eid]

    # Yeni gun - siradaki egitimi sec
    idx = egitim_index % len(liste)
    eid = liste[idx]
    yeni_index = (idx + 1) % len(liste)

    # Hem Sheets'e hem durum.json'a yaz
    _sheets_index_yaz(yeni_index, bugun)
    d = _oku()
    d["egitim_index"] = yeni_index
    d["son_tarih"] = bugun
    _yaz(d)

    return eid, EGITIMLER[eid]


# ── AKTIF EGITIM ───────────────────────────────────────────

def aktif_egitim_set(egitim_id: str, grup_mesaj_id: int = None):
    d = _oku()
    d["aktif"] = {
        "egitim_id": egitim_id,
        "grup_mesaj_id": grup_mesaj_id,
        "tarih": _bugun(),
        "acik": True
    }
    _yaz(d)
    # Sheets'e de yaz (deploy kaliciligi icin)
    try:
        from sheets import _servis
        s, sid = _servis()
        s.values().update(
            spreadsheetId=sid, range="Ayarlar!A3:B4",
            valueInputOption="RAW",
            body={"values": [
                ["aktif_egitim_id", egitim_id],
                ["aktif_egitim_tarih", _bugun()]
            ]}
        ).execute()
    except:
        pass


def aktif_egitim_al() -> dict:
    d = _oku()
    aktif = d.get("aktif")
    # durum.json bossa Sheets'ten oku
    if not aktif or not aktif.get("egitim_id"):
        try:
            ayarlar = _sheets_index_oku()
            eid = ayarlar.get("aktif_egitim_id")
            tarih = ayarlar.get("aktif_egitim_tarih")
            if eid and tarih:
                aktif = {"egitim_id": eid, "tarih": tarih, "acik": tarih == _bugun()}
                d["aktif"] = aktif
                _yaz(d)
        except:
            pass
    return aktif


def aktif_egitim_temizle():
    d = _oku()
    if d.get("aktif"):
        d["aktif"]["acik"] = False
    _yaz(d)


def egitim_acik_mi() -> bool:
    d = _oku()
    aktif = d.get("aktif")
    if not aktif:
        return False
    return aktif.get("acik", False) and aktif.get("tarih") == _bugun()


def gunun_egitim_id() -> str:
    d = _oku()
    aktif = d.get("aktif")
    if aktif and aktif.get("tarih") == _bugun():
        return aktif.get("egitim_id")
    return None


# ── TAMAMLAMA ──────────────────────────────────────────────

def bugun_tamamlandi_kaydet(user_id: int):
    d = _oku()
    bugun = _bugun()
    d.setdefault("bugun_tamamlayanlar", {}).setdefault(bugun, [])
    if str(user_id) not in d["bugun_tamamlayanlar"][bugun]:
        d["bugun_tamamlayanlar"][bugun].append(str(user_id))
    _yaz(d)


def bugun_tamamlayanlar(tarih: str) -> list:
    return _oku().get("bugun_tamamlayanlar", {}).get(tarih, [])


def tamamlandi_kaydet(user_id: int, egitim_id: str):
    """Tamamlanan egitimi hem durum.json'a hem bugun listesine kaydet."""
    d = _oku()
    k = str(user_id)
    d.setdefault("tamamlananlar", {}).setdefault(k, [])
    if egitim_id not in d["tamamlananlar"][k]:
        d["tamamlananlar"][k].append(egitim_id)
    bugun_tamamlandi_kaydet(user_id)
    _yaz(d)


def eksik_egitimler(user_id: int) -> list:
    from config import EGITIMLER
    tamamlananlar = tamamlanan_egitimler(user_id)
    return [e for e in EGITIMLER.keys() if e not in tamamlananlar]


def tamamlanan_egitimler(user_id: int) -> list:
    """
    Sheets kayitlarindan gecilen egitimleri hesapla.
    durum.json'daki listeyle birlestir (her ikisine de bak).
    """
    from config import EGITIMLER
    gecilen = set()

    # 1. Sheets'ten oku — GECTI olan kayitlara bak
    try:
        from sheets import tum_kayitlar_getir
        kayitlar = tum_kayitlar_getir()
        for k in kayitlar:
            if str(k.get("telegram_id","")) == str(user_id):
                if k.get("durum","") in ("GECTI","GECTİ"):
                    # Egitim konusundan ID bul
                    konu = k.get("egitim_konusu","")
                    for eid, e in EGITIMLER.items():
                        if e.get("baslik","") == konu:
                            gecilen.add(eid)
                            break
    except Exception as e:
        logger.warning(f"Sheets tamamlanan okuma hatasi: {e}")

    # 2. durum.json'daki listeyle birlestir
    d = _oku()
    json_liste = d.get("tamamlananlar", {}).get(str(user_id), [])
    gecilen.update(json_liste)

    return list(gecilen)


def tekrar_izni_ver(user_id: int, egitim_id: str):
    d = _oku()
    k = str(user_id)
    t = d.get("tamamlananlar", {}).get(k, [])
    if egitim_id in t:
        t.remove(egitim_id)
        d["tamamlananlar"][k] = t
        _yaz(d)


# ── IZIN ───────────────────────────────────────────────────

def izin_ekle(user_id: int, tarih: str):
    d = _oku()
    d.setdefault("izinler", {}).setdefault(str(user_id), [])
    if tarih not in d["izinler"][str(user_id)]:
        d["izinler"][str(user_id)].append(tarih)
    _yaz(d)


def izin_kaldir(user_id: int, tarih: str):
    d = _oku()
    liste = d.get("izinler", {}).get(str(user_id), [])
    if tarih in liste:
        liste.remove(tarih)
    d.setdefault("izinler", {})[str(user_id)] = liste
    _yaz(d)


def izinli_mi(user_id: int, tarih: str) -> bool:
    return tarih in _oku().get("izinler", {}).get(str(user_id), [])
