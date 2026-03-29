"""
isg/atama_gecmisi.py
====================
Uzman ↔ Firma görevlendirme geçmişi.
APPEND ONLY — hiçbir satır silinmez, sadece bitis_tarihi doldurulur.

Sheets: "ISG_UzmanAtamalari"
Sütunlar:
    atama_id | uzman_id | firma_id | unvan_tipi |
    baslangic_tarihi | bitis_tarihi | aktif |
    kayit_zamani | kaydeden
"""

import uuid, logging
from datetime import datetime, date
from isg.sheets_base import sekme_olustur, satir_ekle, tum_satirlar, satir_guncelle

logger = logging.getLogger(__name__)

SEKME     = "ISG_UzmanAtamalari"
BASLIKLAR = [
    "atama_id", "uzman_id", "firma_id", "unvan_tipi",
    "baslangic_tarihi", "bitis_tarihi", "aktif",
    "kayit_zamani", "kaydeden"
]


def _hazirla():
    sekme_olustur(SEKME, BASLIKLAR)


def _satir_to_dict(satir: list) -> dict:
    while len(satir) < len(BASLIKLAR):
        satir.append("")
    return dict(zip(BASLIKLAR, satir))


def _tarih_parse(tarih_str: str):
    """'GG.AA.YYYY' → date nesnesi. Hatalıysa None."""
    if not tarih_str:
        return None
    try:
        p = tarih_str.strip().split(".")
        if len(p) == 3:
            return date(int(p[2]), int(p[1]), int(p[0]))
    except Exception:
        pass
    return None


# ── Atama İşlemleri ─────────────────────────────────────────────

def atama_ekle(uzman_id: str, firma_id: str, unvan_tipi: str,
               baslangic_tarihi: str, yapan: str = "panel") -> str:
    """
    Yeni görevlendirme ekler.
    Aynı firma/unvan için aktif atama varsa önce onu kapatır.

    Returns: atama_id | None
    """
    _hazirla()

    # Varsa mevcut aktif atamayı kapat
    aktif = aktif_atama_getir(firma_id, unvan_tipi)
    if aktif:
        atama_bitir(aktif["atama_id"], baslangic_tarihi, yapan)

    atama_id = f"atm_{uuid.uuid4().hex[:8]}"
    simdi = datetime.now().strftime("%d.%m.%Y %H:%M")

    ok = satir_ekle(SEKME, [
        atama_id, uzman_id, firma_id, unvan_tipi,
        baslangic_tarihi, "", "1", simdi, yapan
    ])

    if ok:
        # Uzman ve firma adlarını audit log için al
        try:
            from isg.uzmanlar import uzman_getir
            from firma_manager import tum_firmalar
            uzman = uzman_getir(uzman_id) or {}
            firma = tum_firmalar().get(firma_id, {})
            from isg.audit_log import log_atama
            log_atama(
                uzman_id, firma_id,
                uzman.get("ad_soyad", uzman_id),
                firma.get("ad", firma_id),
                baslangic_tarihi, yapan
            )
        except Exception as e:
            logger.warning(f"Audit log yazılamadı: {e}")
        return atama_id
    return None


def atama_bitir(atama_id: str, bitis_tarihi: str, yapan: str = "panel") -> bool:
    """Atamanın bitiş tarihini doldurur ve pasife alır."""
    _hazirla()
    for i, satir in enumerate(tum_satirlar(SEKME)):
        if satir and satir[0] == atama_id:
            satir_no = i + 2
            mevcut = list(satir) + [""] * (len(BASLIKLAR) - len(satir))
            mevcut[5] = bitis_tarihi   # bitis_tarihi
            mevcut[6] = "0"            # aktif = 0
            ok = satir_guncelle(SEKME, satir_no, mevcut)
            if ok:
                try:
                    from isg.uzmanlar import uzman_getir
                    from firma_manager import tum_firmalar
                    uzman = uzman_getir(mevcut[1]) or {}
                    firma = tum_firmalar().get(mevcut[2], {})
                    from isg.audit_log import log_ayrilma
                    log_ayrilma(
                        mevcut[1], mevcut[2],
                        uzman.get("ad_soyad", mevcut[1]),
                        firma.get("ad", mevcut[2]),
                        bitis_tarihi, yapan
                    )
                except Exception as e:
                    logger.warning(f"Audit log yazılamadı: {e}")
            return ok
    return False


# ── Sorgular ────────────────────────────────────────────────────

def aktif_atama_getir(firma_id: str, unvan_tipi: str) -> dict:
    """
    Firma + unvan tipine göre şu an aktif olan atamayı döner.
    Kullanım: firma kartında 'şu an atanmış uzman kim?'
    """
    _hazirla()
    for satir in tum_satirlar(SEKME):
        d = _satir_to_dict(satir)
        if (d.get("firma_id") == firma_id
                and d.get("unvan_tipi") == unvan_tipi
                and d.get("aktif") == "1"):
            return d
    return {}


def tarihteki_uzman_getir(firma_id: str, unvan_tipi: str, egitim_tarihi: str) -> dict:
    """
    KRİTİK FONKSİYON — Yasal uyumluluk için.

    Verilen tarihte firmada görevli olan uzmanı döner.
    Bot mesajına ve eğitim belgelerine bu bilgi yazılır.

    Algoritma:
        baslangic_tarihi <= egitim_tarihi <= bitis_tarihi
        (bitis_tarihi boş = hala aktif)
    """
    _hazirla()
    hedef = _tarih_parse(egitim_tarihi)
    if not hedef:
        # Tarih parse edilemezse aktif olanı döndür
        return aktif_atama_getir(firma_id, unvan_tipi)

    eslesen = []
    for satir in tum_satirlar(SEKME):
        d = _satir_to_dict(satir)
        if d.get("firma_id") != firma_id or d.get("unvan_tipi") != unvan_tipi:
            continue
        bas = _tarih_parse(d.get("baslangic_tarihi", ""))
        bit = _tarih_parse(d.get("bitis_tarihi", ""))
        if bas and bas <= hedef:
            if bit is None or hedef <= bit:
                eslesen.append((bas, d))

    if not eslesen:
        return {}
    # En geç başlayan atamayı al (tarih çakışması olursa)
    eslesen.sort(key=lambda x: x[0], reverse=True)
    return eslesen[0][1]


def firma_atama_gecmisi(firma_id: str) -> list:
    """Bir firmanın tüm uzman atama geçmişini döner (aktif + pasif)."""
    _hazirla()
    sonuc = []
    for satir in tum_satirlar(SEKME):
        d = _satir_to_dict(satir)
        if d.get("firma_id") == firma_id:
            sonuc.append(d)
    return sorted(sonuc, key=lambda x: x.get("baslangic_tarihi", ""), reverse=True)


def uzman_atama_gecmisi(uzman_id: str) -> list:
    """Bir uzmanın tüm görevlendirme geçmişini döner."""
    _hazirla()
    sonuc = []
    for satir in tum_satirlar(SEKME):
        d = _satir_to_dict(satir)
        if d.get("uzman_id") == uzman_id:
            sonuc.append(d)
    return sorted(sonuc, key=lambda x: x.get("baslangic_tarihi", ""), reverse=True)


def uzman_bilgisi_bul(firma_id: str, egitim_tarihi: str) -> dict:
    """
    Eğitim tamamlanma mesajı için kullanılır.
    Firmaya göre her iki uzman tipini de döner.

    Returns:
        {
          "is_guvenligi_uzmani": { uzman dict + atama dict },
          "isyeri_hekimi":       { uzman dict + atama dict } veya {}
        }
    """
    from isg.uzmanlar import uzman_getir

    sonuc = {}
    for tip in ["is_guvenligi_uzmani", "isyeri_hekimi"]:
        atama = tarihteki_uzman_getir(firma_id, tip, egitim_tarihi)
        if atama and atama.get("uzman_id"):
            uzman = uzman_getir(atama["uzman_id"]) or {}
            sonuc[tip] = {**uzman, **atama}
        else:
            sonuc[tip] = {}

    return sonuc
