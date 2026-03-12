"""
Çalışan yönetimi — calisanlar.json ile saklanır
config.py'deki CALISANLAR sözlüğünün yerini alır
"""

import json
import os
import logging
from datetime import date

logger = logging.getLogger(__name__)
DOSYA = "calisanlar.json"


def _oku() -> dict:
    if os.path.exists(DOSYA):
        try:
            with open(DOSYA, "r", encoding="utf-8") as f:
                data = json.load(f)
                # key'leri int'e çevir (JSON'da string olarak saklanır)
                return {int(k): v for k, v in data.items()}
        except:
            pass
    return {}


def _yaz(d: dict):
    with open(DOSYA, "w", encoding="utf-8") as f:
        json.dump({str(k): v for k, v in d.items()}, f, ensure_ascii=False, indent=2)


def tum_calisanlar() -> dict:
    return _oku()


def calisan_ekle(telegram_id: int, ad_soyad: str, dogum_tarihi: str, gorev: str):
    d = _oku()
    d[telegram_id] = {
        "ad_soyad": ad_soyad,
        "dogum_tarihi": dogum_tarihi,
        "gorev": gorev,
        "aktif": True
    }
    _yaz(d)


def calisan_guncelle(telegram_id: int, ad_soyad: str, dogum_tarihi: str, gorev: str):
    d = _oku()
    if telegram_id in d:
        d[telegram_id].update({
            "ad_soyad": ad_soyad,
            "dogum_tarihi": dogum_tarihi,
            "gorev": gorev
        })
        _yaz(d)


def calisan_sil(telegram_id: int):
    d = _oku()
    d.pop(telegram_id, None)
    _yaz(d)


def calisan_bul(telegram_id: int) -> dict:
    return _oku().get(telegram_id)
