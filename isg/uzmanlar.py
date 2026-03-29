"""
isg/uzmanlar.py
===============
Uzman kişi kartları — Google Sheets "ISG_Uzmanlar" sekmesi.

Sütunlar:
    uzman_id | ad_soyad | unvan | sinif | sertifika_no |
    diploma_no | aktif | kayit_tarihi | guncelleme_tarihi
"""

import uuid, logging
from datetime import datetime
from isg.sheets_base import sekme_olustur, satir_ekle, tum_satirlar, satir_guncelle

logger = logging.getLogger(__name__)

SEKME     = "ISG_Uzmanlar"
BASLIKLAR = [
    "uzman_id", "ad_soyad", "unvan", "sinif",
    "sertifika_no", "diploma_no", "aktif",
    "kayit_tarihi", "guncelleme_tarihi"
]

UNVANLAR = {
    "is_guvenligi_uzmani": "İş Güvenliği Uzmanı",
    "isyeri_hekimi":       "İşyeri Hekimi",
    "diger_saglik":        "Diğer Sağlık Personeli",
    "usta_ogretici":       "Usta Öğretici",
    "isveren":             "İşveren / Vekili",
}

SINIF_GEREKTIREN = {"is_guvenligi_uzmani"}


def _hazirla():
    sekme_olustur(SEKME, BASLIKLAR)


def _satir_to_dict(satir: list) -> dict:
    while len(satir) < len(BASLIKLAR):
        satir.append("")
    return dict(zip(BASLIKLAR, satir))


def tum_uzmanlar(sadece_aktif=True) -> list:
    _hazirla()
    satirlar = tum_satirlar(SEKME)
    uzmanlar = [_satir_to_dict(s) for s in satirlar if s]
    if sadece_aktif:
        uzmanlar = [u for u in uzmanlar if u.get("aktif", "1") == "1"]
    return uzmanlar


def uzman_getir(uzman_id: str):
    for u in tum_uzmanlar(sadece_aktif=False):
        if u.get("uzman_id") == uzman_id:
            return u
    return None


def uzman_ekle(ad_soyad, unvan, sinif, sertifika_no, diploma_no="", yapan="panel"):
    if unvan not in UNVANLAR:
        logger.error(f"Geçersiz unvan: {unvan}")
        return None
    if unvan in SINIF_GEREKTIREN and sinif not in ["A", "B", "C"]:
        logger.error("İş güvenliği uzmanı için A/B/C sınıfı zorunlu")
        return None

    _hazirla()
    uzman_id = f"uzm_{uuid.uuid4().hex[:8]}"
    simdi = datetime.now().strftime("%d.%m.%Y %H:%M")

    ok = satir_ekle(SEKME, [
        uzman_id, ad_soyad, unvan, sinif,
        sertifika_no, diploma_no, "1", simdi, simdi
    ])

    if ok:
        from isg.audit_log import log_uzman_ekle
        log_uzman_ekle(uzman_id, ad_soyad, yapan)
        return uzman_id
    return None


def uzman_guncelle(uzman_id, ad_soyad=None, unvan=None, sinif=None,
                   sertifika_no=None, diploma_no=None, yapan="panel"):
    _hazirla()
    for i, satir in enumerate(tum_satirlar(SEKME)):
        if satir and satir[0] == uzman_id:
            satir_no = i + 2
            eski = _satir_to_dict(list(satir))
            mevcut = list(satir) + [""] * (len(BASLIKLAR) - len(satir))
            if ad_soyad     is not None: mevcut[1] = ad_soyad
            if unvan        is not None: mevcut[2] = unvan
            if sinif        is not None: mevcut[3] = sinif
            if sertifika_no is not None: mevcut[4] = sertifika_no
            if diploma_no   is not None: mevcut[5] = diploma_no
            mevcut[8] = datetime.now().strftime("%d.%m.%Y %H:%M")
            ok = satir_guncelle(SEKME, satir_no, mevcut)
            if ok:
                from isg.audit_log import log_uzman_guncelle
                log_uzman_guncelle(uzman_id, mevcut[1], eski,
                                   _satir_to_dict(mevcut), yapan)
            return ok
    return False


def uzman_pasif_yap(uzman_id, yapan="panel"):
    _hazirla()
    for i, satir in enumerate(tum_satirlar(SEKME)):
        if satir and satir[0] == uzman_id:
            satir_no = i + 2
            mevcut = list(satir) + [""] * (len(BASLIKLAR) - len(satir))
            mevcut[6] = "0"
            mevcut[8] = datetime.now().strftime("%d.%m.%Y %H:%M")
            ok = satir_guncelle(SEKME, satir_no, mevcut)
            if ok:
                from isg.audit_log import log_yaz, ISLEM_PASIF
                log_yaz(ISLEM_PASIF, "Uzmanlar", uzman_id,
                        f"Uzman pasife alındı: {satir[1]}", yapan_ad=yapan)
            return ok
    return False


def uzman_unvan_str(uzman: dict) -> str:
    """Bot mesajı için: 'A Sınıfı İş Güvenliği Uzmanı, Sert. No: 384571, Ahmet Bulut'"""
    unvan_label = UNVANLAR.get(uzman.get("unvan", ""), uzman.get("unvan", ""))
    sinif = uzman.get("sinif", "")
    sertifika = uzman.get("sertifika_no", "")
    ad = uzman.get("ad_soyad", "")
    parcalar = []
    if sinif and sinif != "—":
        parcalar.append(f"{sinif} Sınıfı {unvan_label}")
    else:
        parcalar.append(unvan_label)
    if sertifika:
        parcalar.append(f"Sert. No: {sertifika}")
    if ad:
        parcalar.append(ad)
    return ", ".join(parcalar)
