"""
E�itim sırası, izin ve aktif eğitim yönetimi
"""

import json
import os
import logging
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
        "aktif": None,           # { egitim_id, grup_mesaj_id, tarih }
        "bugun_tamamlayanlar": {}  # { "tarih": [user_id, ...] }
    }


def _yaz(d: dict):
    with open(DOSYA, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


# ── EĞİTİM SIRASI ──────────────────────────────────────────

def siradaki_egitim_al():
    from config import EGITIMLER
    d = _oku()
    liste = list(EGITIMLER.keys())
    if not liste:
        return None, None

    bugun = date.today().strftime("%d.%m.%Y")

    if d.get("son_tarih") == bugun:
        # Bugün zaten seçildi — aynısını döndür
        idx = (d.get("egitim_index", 1) - 1) % len(liste)
        eid = liste[idx]
        return eid, EGITIMLER[eid]

    idx = d.get("egitim_index", 0) % len(liste)
    eid = liste[idx]
    d["egitim_index"] = (idx + 1) % len(liste)
    d["son_tarih"] = bugun
    _yaz(d)
    logger.info(f"Yeni eğitim seçildi: {eid} ({idx+1}/{len(liste)})")
    return eid, EGITIMLER[eid]


# ── AKTİF EĞİTİM ───────────────────────────────────────────

def aktif_egitim_set(egitim_id: str, grup_mesaj_id: int = None):
    d = _oku()
    d["aktif"] = {
        "egitim_id": egitim_id,
        "grup_mesaj_id": grup_mesaj_id,
        "tarih": date.today().strftime("%d.%m.%Y"),
        "acik": True
    }
    _yaz(d)


def aktif_egitim_al() -> dict:
    return _oku().get("aktif")


def aktif_egitim_temizle():
    d = _oku()
    if d.get("aktif"):
        d["aktif"]["acik"] = False
    _yaz(d)


def egitim_acik_mi() -> bool:
    """Gün içinde eğitim hâlâ açık mı?"""
    d = _oku()
    aktif = d.get("aktif")
    if not aktif:
        return False
    if not aktif.get("acik", False):
        return False
    # Bugünün eğitimi mi?
    return aktif.get("tarih") == date.today().strftime("%d.%m.%Y")


def gunun_egitim_id() -> str:
    """Bugünün aktif eğitim ID'si."""
    d = _oku()
    aktif = d.get("aktif")
    if aktif and aktif.get("tarih") == date.today().strftime("%d.%m.%Y"):
        return aktif.get("egitim_id")
    return None


# ── TAMAMLAMA TAKİBİ ────────────────────────────────────────

def bugun_tamamlandi_kaydet(user_id: int):
    """Bugün eğitimi tamamlayanları kaydet (kapanış mesajı için)."""
    d = _oku()
    bugun = date.today().strftime("%d.%m.%Y")
    bt = d.setdefault("bugun_tamamlayanlar", {})
    bt.setdefault(bugun, [])
    if str(user_id) not in bt[bugun]:
        bt[bugun].append(str(user_id))
    _yaz(d)


def bugun_tamamlayanlar(tarih: str) -> list:
    d = _oku()
    return d.get("bugun_tamamlayanlar", {}).get(tarih, [])


def tamamlandi_kaydet(user_id: int, egitim_id: str):
    """Genel eğitim tamamlama kaydı (ilerleme için)."""
    d = _oku()
    k = str(user_id)
    d.setdefault("tamamlananlar", {}).setdefault(k, [])
    if egitim_id not in d["tamamlananlar"][k]:
        d["tamamlananlar"][k].append(egitim_id)
    bugun_tamamlandi_kaydet(user_id)
    _yaz(d)


def eksik_egitimler(user_id: int) -> list:
    from config import EGITIMLER
    d = _oku()
    tamamlananlar = d.get("tamamlananlar", {}).get(str(user_id), [])
    return [e for e in EGITIMLER.keys() if e not in tamamlananlar]


# ── İZİN ───────────────────────────────────────────────────

def izin_ekle(user_id: int, tarih: str):
    d = _oku()
    k = str(user_id)
    d.setdefault("izinler", {}).setdefault(k, [])
    if tarih not in d["izinler"][k]:
        d["izinler"][k].append(tarih)
    _yaz(d)


def izin_kaldir(user_id: int, tarih: str):
    d = _oku()
    k = str(user_id)
    liste = d.get("izinler", {}).get(k, [])
    if tarih in liste:
        liste.remove(tarih)
    d.setdefault("izinler", {})[k] = liste
    _yaz(d)


def izinli_mi(user_id: int, tarih: str) -> bool:
    d = _oku()
    return tarih in d.get("izinler", {}).get(str(user_id), [])


# ── TEKRAR İZNİ ────────────────────────────────────────────

def tekrar_izni_ver(user_id: int, egitim_id: str):
    """Admin kaldıyı tekrar denesin diye kaydından siler."""
    d = _oku()
    k = str(user_id)
    tamamlananlar = d.get("tamamlananlar", {}).get(k, [])
    if egitim_id in tamamlananlar:
        tamamlananlar.remove(egitim_id)
        d["tamamlananlar"][k] = tamamlananlar
        _yaz(d)
