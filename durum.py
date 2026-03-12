"""
E�itim sırası ve izin yönetimi — durum.json ile saklanır
"""

import json
import os
import logging
from datetime import date

logger = logging.getLogger(__name__)
DURUM_DOSYA = "durum.json"


def _oku() -> dict:
    if os.path.exists(DURUM_DOSYA):
        try:
            with open(DURUM_DOSYA, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"egitim_index": 0, "son_tarih": "", "izinler": {}, "tamamlananlar": {}}


def _yaz(d: dict):
    with open(DURUM_DOSYA, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


def siradaki_egitim_al():
    from config import EGITIMLER
    d = _oku()
    liste = list(EGITIMLER.keys())
    if not liste:
        return None, None

    bugun = date.today().strftime("%d.%m.%Y")

    if d.get("son_tarih") == bugun:
        onceki = (d.get("egitim_index", 0) - 1) % len(liste)
        eid = liste[onceki]
        return eid, EGITIMLER[eid]

    idx = d.get("egitim_index", 0) % len(liste)
    eid = liste[idx]
    d["egitim_index"] = (idx + 1) % len(liste)
    d["son_tarih"] = bugun
    _yaz(d)
    logger.info(f"Eğitim sırası: {eid} ({idx + 1}/{len(liste)})")
    return eid, EGITIMLER[eid]


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
    izinler = d.get("izinler", {}).get(k, [])
    if tarih in izinler:
        izinler.remove(tarih)
    d.setdefault("izinler", {})[k] = izinler
    _yaz(d)


def izinli_mi(user_id: int, tarih: str) -> bool:
    d = _oku()
    return tarih in d.get("izinler", {}).get(str(user_id), [])


def tamamlandi_kaydet(user_id: int, egitim_id: str):
    d = _oku()
    k = str(user_id)
    d.setdefault("tamamlananlar", {}).setdefault(k, [])
    if egitim_id not in d["tamamlananlar"][k]:
        d["tamamlananlar"][k].append(egitim_id)
    _yaz(d)


def eksik_egitimler(user_id: int) -> list:
    from config import EGITIMLER
    d = _oku()
    tamamlananlar = d.get("tamamlananlar", {}).get(str(user_id), [])
    return [e for e in EGITIMLER.keys() if e not in tamamlananlar]
