"""
Egitim sirasi, izin, aktif egitim ve deneme hakki yonetimi.
Tüm kalıcı durum Sheets'te tutulur — durum.json sadece cache.
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
        "egitim_index": 0, "son_tarih": "", "izinler": {},
        "tamamlananlar": {}, "aktif": None,
        "bugun_tamamlayanlar": {}, "gunluk_haklar": {}
    }


def _yaz(d: dict):
    with open(DOSYA, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


def _bugun():
    return date.today().strftime("%d.%m.%Y")


# ── DENEME HAKKI ────────────────────────────────────────────────

def deneme_hakki_al(user_id: int) -> dict:
    d = _oku()
    bugun = _bugun()
    haklar = d.setdefault("gunluk_haklar", {}).setdefault(bugun, {})
    k = str(user_id)
    if k not in haklar:
        haklar[k] = {"kalan": 1, "deneme": 0}
        _yaz(d)
    return haklar[k]


def deneme_kullan(user_id: int):
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
    return deneme_hakki_al(user_id)["kalan"] > 0


def kacinci_deneme(user_id: int) -> int:
    return deneme_hakki_al(user_id).get("deneme", 0) + 1


# ── EĞİTİM SIRASI — Sheets tabanlı ──────────────────────────────

def _ayarlar_oku() -> dict:
    try:
        from sheets import _servis
        s, sid = _servis()
        r = s.values().get(spreadsheetId=sid, range="Ayarlar!A1:B30").execute()
        ayarlar = {}
        for satir in r.get("values", []):
            if len(satir) >= 2:
                ayarlar[satir[0].strip()] = satir[1].strip()
        return ayarlar
    except Exception as e:
        logger.warning(f"Ayarlar okunamadi: {e}")
        return {}


def _ayar_yaz(anahtar: str, deger: str):
    try:
        from sheets import _servis
        s, sid = _servis()
        # Sekme varsa güncelle
        try:
            r = s.values().get(spreadsheetId=sid, range="Ayarlar!A1:B30").execute()
            for i, satir in enumerate(r.get("values", [])):
                if satir and satir[0].strip() == anahtar:
                    s.values().update(spreadsheetId=sid,
                        range=f"Ayarlar!A{i+1}:B{i+1}",
                        valueInputOption="RAW",
                        body={"values": [[anahtar, deger]]}).execute()
                    return
        except:
            pass
        # Yoksa append
        s.values().append(spreadsheetId=sid, range="Ayarlar!A1",
            valueInputOption="RAW", insertDataOption="INSERT_ROWS",
            body={"values": [[anahtar, deger]]}).execute()
    except Exception as e:
        logger.warning(f"Ayar yazma hatasi ({anahtar}): {e}")


def siradaki_egitim_al():
    """
    Bugün için eğitim seç.
    - Bugün zaten seçildiyse aynısını döndür
    - Yeni günse bir sonrakini seç (sıralı, döngüsel)
    - Sıra Sheets'te 'Egitimler' sekmesinin 'sira' sütununa göre
    """
    from egitimler_sheets import tum_egitimler
    egitimler = tum_egitimler(sirali=True)  # sıra sütununa göre sıralı

    if not egitimler:
        logger.error("Egitim listesi bos!")
        return None, None

    liste = list(egitimler.keys())   # sıralı key listesi
    bugun = _bugun()

    # Sheets + json'dan mevcut durumu al
    ayarlar = _ayarlar_oku()
    son_tarih     = ayarlar.get("son_tarih") or _oku().get("son_tarih", "")
    egitim_index  = int(ayarlar.get("egitim_index", _oku().get("egitim_index", 0)))

    if son_tarih == bugun:
        # Bugün zaten seçildi — aynısını döndür
        idx = (egitim_index - 1) % len(liste)
        eid = liste[idx]
        return eid, egitimler.get(eid)

    # Yeni gün — sıradakini seç
    idx = egitim_index % len(liste)
    eid = liste[idx]
    yeni_index = (idx + 1) % len(liste)   # döngüsel: son eğitim bittikten sonra başa döner

    # Sheets ve json'a yaz
    _ayar_yaz("egitim_index", str(yeni_index))
    _ayar_yaz("son_tarih", bugun)
    d = _oku()
    d["egitim_index"] = yeni_index
    d["son_tarih"] = bugun
    _yaz(d)

    logger.info(f"Bugünün eğitimi seçildi: {eid} (index={idx}, yarınki={yeni_index})")
    return eid, egitimler.get(eid)


def sonraki_egitim_bilgisi() -> dict:
    """
    Panel için: bugünün ve yarının eğitimini döndür.
    Returns: { bugun_id, bugun_baslik, sonraki_id, sonraki_baslik, toplam, mevcut_index }
    """
    from egitimler_sheets import tum_egitimler
    egitimler = tum_egitimler(sirali=True)
    if not egitimler:
        return {}

    liste = list(egitimler.keys())
    toplam = len(liste)
    ayarlar = _ayarlar_oku()
    son_tarih    = ayarlar.get("son_tarih", "")
    egitim_index = int(ayarlar.get("egitim_index", 0))
    bugun = _bugun()

    # Bugünün eğitimi
    if son_tarih == bugun:
        bugun_idx = (egitim_index - 1) % toplam
    else:
        bugun_idx = egitim_index % toplam

    sonraki_idx = (bugun_idx + 1) % toplam

    bugun_eid    = liste[bugun_idx]
    sonraki_eid  = liste[sonraki_idx]

    return {
        "bugun_id":       bugun_eid,
        "bugun_baslik":   egitimler[bugun_eid].get("baslik", ""),
        "sonraki_id":     sonraki_eid,
        "sonraki_baslik": egitimler[sonraki_eid].get("baslik", ""),
        "toplam":         toplam,
        "mevcut_index":   bugun_idx + 1,  # 1-tabanlı
        "son_tarih":      son_tarih,
    }


def sonraki_egitim_sec(egitim_id: str) -> bool:
    """
    Admin yarının eğitimini manuel seçer.
    egitim_index = seçilen eğitimin konumu (yarın bu index'ten başlanır)
    son_tarih sıfırlanmaz — bugünün eğitimi değişmez, sadece yarın etki eder.
    """
    from egitimler_sheets import tum_egitimler
    egitimler = tum_egitimler(sirali=True)
    liste = list(egitimler.keys())
    if egitim_id not in liste:
        logger.warning(f"sonraki_egitim_sec: '{egitim_id}' listede yok")
        return False
    idx = liste.index(egitim_id)
    # egitim_index = yarın gönderilecek eğitimin index'i
    _ayar_yaz("egitim_index", str(idx))
    # json'ı da güncelle
    d = _oku()
    d["egitim_index"] = idx
    _yaz(d)
    logger.info(f"Yarının eğitimi seçildi: {egitim_id} (index={idx}, baslik={egitimler[egitim_id].get('baslik','')})")
    return True


# ── AKTİF EĞİTİM ────────────────────────────────────────────────

def aktif_egitim_set(egitim_id: str, grup_mesaj_id: int = None):
    d = _oku()
    d["aktif"] = {
        "egitim_id": egitim_id,
        "grup_mesaj_id": grup_mesaj_id,
        "tarih": _bugun(),
        "acik": True
    }
    _yaz(d)
    try:
        _ayar_yaz("aktif_egitim_id", egitim_id)
        _ayar_yaz("aktif_egitim_tarih", _bugun())
    except:
        pass


def aktif_egitim_al() -> dict:
    d = _oku()
    aktif = d.get("aktif")
    if not aktif or not aktif.get("egitim_id"):
        try:
            ayarlar = _ayarlar_oku()
            eid   = ayarlar.get("aktif_egitim_id")
            tarih = ayarlar.get("aktif_egitim_tarih")
            if eid and tarih:
                aktif = {"egitim_id": eid, "tarih": tarih, "acik": tarih == _bugun()}
                d["aktif"] = aktif
                _yaz(d)
        except:
            pass
    return aktif or {}


def aktif_egitim_temizle():
    d = _oku()
    if d.get("aktif"):
        d["aktif"]["acik"] = False
    _yaz(d)


def egitim_acik_mi() -> bool:
    bugun = _bugun()
    d = _oku()
    aktif = d.get("aktif")
    if aktif and aktif.get("tarih") == bugun:
        return aktif.get("acik", False)
    try:
        ayarlar = _ayarlar_oku()
        eid   = ayarlar.get("aktif_egitim_id")
        tarih = ayarlar.get("aktif_egitim_tarih")
        if eid and tarih == bugun:
            d["aktif"] = {"egitim_id": eid, "tarih": tarih, "acik": True}
            _yaz(d)
            return True
    except:
        pass
    return False


def gunun_egitim_id() -> str:
    bugun = _bugun()
    d = _oku()
    aktif = d.get("aktif")
    if aktif and aktif.get("tarih") == bugun and aktif.get("egitim_id"):
        return aktif["egitim_id"]
    try:
        ayarlar = _ayarlar_oku()
        eid   = ayarlar.get("aktif_egitim_id")
        tarih = ayarlar.get("aktif_egitim_tarih")
        if eid and tarih == bugun:
            d["aktif"] = {"egitim_id": eid, "tarih": tarih, "acik": True}
            _yaz(d)
            return eid
    except Exception as e:
        logger.warning(f"Sheets'ten egitim id alinamadi: {e}")
    return None


# ── TAMAMLAMA ────────────────────────────────────────────────────

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
    d = _oku()
    k = str(user_id)
    d.setdefault("tamamlananlar", {}).setdefault(k, [])
    if egitim_id not in d["tamamlananlar"][k]:
        d["tamamlananlar"][k].append(egitim_id)
    bugun_tamamlandi_kaydet(user_id)
    _yaz(d)


def eksik_egitimler(user_id: int) -> list:
    from egitimler_sheets import tum_egitimler
    egitimler = tum_egitimler()
    tamamlananlar = tamamlanan_egitimler(user_id)
    return [e for e in egitimler.keys() if e not in tamamlananlar]


def tamamlanan_egitimler(user_id: int) -> list:
    from egitimler_sheets import tum_egitimler
    EGITIMLER = tum_egitimler()
    gecilen = set()
    try:
        from sheets import tum_kayitlar_getir
        for k in tum_kayitlar_getir():
            if str(k.get("telegram_id", "")) == str(user_id):
                if k.get("durum", "") in ("GECTI", "GECTİ"):
                    konu = k.get("egitim_konusu", "")
                    for eid, e in EGITIMLER.items():
                        if e.get("baslik", "") == konu:
                            gecilen.add(eid)
                            break
    except Exception as e:
        logger.warning(f"Sheets tamamlanan okuma hatasi: {e}")
    d = _oku()
    gecilen.update(d.get("tamamlananlar", {}).get(str(user_id), []))
    return list(gecilen)


def tekrar_izni_ver(user_id: int, egitim_id: str):
    d = _oku()
    k = str(user_id)
    t = d.get("tamamlananlar", {}).get(k, [])
    if egitim_id in t:
        t.remove(egitim_id)
        d["tamamlananlar"][k] = t
        _yaz(d)


# ── İZİN ─────────────────────────────────────────────────────────

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


def izinli_mi(user_id: int, tarih: str = None) -> bool:
    tarih = tarih or _bugun()
    return tarih in _oku().get("izinler", {}).get(str(user_id), [])
