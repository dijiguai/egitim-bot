"""
E�itim sırası ve izin yönetimi
durum.json dosyasında saklanır — Railway'de kalıcıdır.
"""

import json
import os
import logging
from datetime import date

logger = logging.getLogger(__name__)
DURUM_DOSYA = "durum.json"


def _durum_oku() -> dict:
    if os.path.exists(DURUM_DOSYA):
        try:
            with open(DURUM_DOSYA, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {
        "egitim_index": 0,          # Şu anki eğitim sırası
        "son_egitim_tarihi": "",     # Son gönderim tarihi
        "izinler": {},               # { "user_id": ["12.03.2026", "13.03.2026"] }
        "tamamlananlar": {}          # { "user_id": ["egitim_id1", "egitim_id2"] }
    }


def _durum_yaz(durum: dict):
    with open(DURUM_DOSYA, "w", encoding="utf-8") as f:
        json.dump(durum, f, ensure_ascii=False, indent=2)


def siradaki_egitim_al():
    """
    Sıradaki eğitimi döndürür ve indexi ilerletir.
    Tüm eğitimler tamamlanınca başa döner.
    """
    from config import EGITIMLER
    durum = _durum_oku()
    egitim_listesi = list(EGITIMLER.keys())

    if not egitim_listesi:
        return None, None

    bugun = date.today().strftime("%d.%m.%Y")

    # Bugün zaten gönderildiyse aynısını döndür (tekrar gönderme)
    if durum.get("son_egitim_tarihi") == bugun:
        idx = durum.get("egitim_index", 0)
        # Bir önceki index (bugün zaten gönderildi)
        onceki_idx = (idx - 1) % len(egitim_listesi)
        egitim_id = egitim_listesi[onceki_idx]
        return egitim_id, EGITIMLER[egitim_id]

    # Yeni gün — sıradaki eğitimi al
    idx = durum.get("egitim_index", 0) % len(egitim_listesi)
    egitim_id = egitim_listesi[idx]

    # Indexi ilerlet ve kaydet
    durum["egitim_index"] = (idx + 1) % len(egitim_listesi)
    durum["son_egitim_tarihi"] = bugun
    _durum_yaz(durum)

    logger.info(f"Sıradaki eğitim: {egitim_id} (index {idx}/{len(egitim_listesi)})")
    return egitim_id, EGITIMLER[egitim_id]


def izin_ekle(user_id: int, tarih: str):
    """Çalışanı belirtilen tarihe izinli olarak işaretle."""
    durum = _durum_oku()
    izinler = durum.get("izinler", {})
    anahtar = str(user_id)
    if anahtar not in izinler:
        izinler[anahtar] = []
    if tarih not in izinler[anahtar]:
        izinler[anahtar].append(tarih)
    durum["izinler"] = izinler
    _durum_yaz(durum)


def izin_kaldir(user_id: int, tarih: str):
    """İzni kaldır."""
    durum = _durum_oku()
    izinler = durum.get("izinler", {})
    anahtar = str(user_id)
    if anahtar in izinler and tarih in izinler[anahtar]:
        izinler[anahtar].remove(tarih)
    durum["izinler"] = izinler
    _durum_yaz(durum)


def izinli_mi(user_id: int, tarih: str) -> bool:
    """Çalışan o tarihte izinli mi?"""
    durum = _durum_oku()
    return tarih in durum.get("izinler", {}).get(str(user_id), [])


def tamamlandi_kaydet(user_id: int, egitim_id: str):
    """Çalışanın tamamladığı eğitimi kaydet."""
    durum = _durum_oku()
    tamamlananlar = durum.get("tamamlananlar", {})
    anahtar = str(user_id)
    if anahtar not in tamamlananlar:
        tamamlananlar[anahtar] = []
    if egitim_id not in tamamlananlar[anahtar]:
        tamamlananlar[anahtar].append(egitim_id)
    durum["tamamlananlar"] = tamamlananlar
    _durum_yaz(durum)


def eksik_egitimler(user_id: int) -> list:
    """Çalışanın henüz tamamlamadığı eğitimleri döndür."""
    from config import EGITIMLER
    durum = _durum_oku()
    tamamlananlar = durum.get("tamamlananlar", {}).get(str(user_id), [])
    return [eid for eid in EGITIMLER.keys() if eid not in tamamlananlar]


def durum_ozeti() -> dict:
    """Panel için genel durum özeti."""
    from config import EGITIMLER, CALISANLAR
    durum = _durum_oku()
    toplam_egitim = len(EGITIMLER)
    egitim_listesi = list(EGITIMLER.keys())
    guncel_idx = durum.get("egitim_index", 0) % max(len(egitim_listesi), 1)

    return {
        "guncel_egitim_idx": guncel_idx,
        "toplam_egitim": toplam_egitim,
        "son_gonderim": durum.get("son_egitim_tarihi", "—"),
        "siradaki": egitim_listesi[guncel_idx] if egitim_listesi else "—",
        "toplam_calisan": len(CALISANLAR),
    }
