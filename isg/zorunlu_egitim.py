"""
isg/zorunlu_egitim.py
=====================
6331 sayılı Kanun ve İşyerlerinde İSG Eğitimlerinin Usul ve Esasları
Hakkında Yönetmelik'e göre zorunlu eğitim konuları.

Yönetmelik Ek-1 — Çalışanlara verilecek İSG eğitiminin konuları:

A) Genel konular (tüm tehlike sınıfları, tüm çalışanlar)
B) Tehlike sınıfına ve işe özgü konular

Periyodik yenileme süreleri:
  - Az Tehlikeli:  2 yılda 1
  - Tehlikeli:     1 yılda 1
  - Çok Tehlikeli: 1 yılda 1 (bazı konular 6 ayda 1)

Eğitim kategorileri (tur alanına karşılık gelir):
  - isg_genel       : Genel İSG (hukuki, tehlike, sağlık)
  - isg_is_giris    : İşe giriş / oryantasyon
  - isg_acil        : Acil durum, tahliye, ilk yardım
  - isg_kisisel     : KKD kullanımı
  - isg_ozel        : Tehlike sınıfına özgü (makine, kimyasal, yüksekte vs.)
  - isg_yenileme    : Periyodik yenileme
  - toolbox         : Toolbox meeting / günlük güvenlik toplantısı
"""

import logging
from datetime import datetime, date

logger = logging.getLogger(__name__)

# ── Zorunlu eğitim katalogu ────────────────────────────────────
# Her madde: {id, baslik, kategori, kapsam, periyot_ay, tehlike_siniflari}
# kapsam: "tum" | "yeni_isci" | "belirli_gorev"
# periyot_ay: 0=bir kez (işe girişte), 12=yıllık, 24=2 yıllık, 6=6 aylık

ZORUNLU_EGITIM_KATALOGU = [

    # ── A) Genel konular — tüm çalışanlar ──────────────────────
    {
        "zon_id":    "zon_genel_isg_hukuk",
        "baslik":    "Genel İSG Kuralları ve Yasal Haklar",
        "kategori":  "isg_genel",
        "aciklama":  "6331 sayılı Kanun kapsamında çalışan hakları, sorumluluklar, işveren yükümlülükleri",
        "kapsam":    "tum",
        "periyot_ay": 12,
        "tehlike":   ["Az Tehlikeli", "Tehlikeli", "Çok Tehlikeli"],
        "min_sure_dk": 60,
    },
    {
        "zon_id":    "zon_genel_tehlike_risk",
        "baslik":    "İşyeri Tehlikeleri ve Risk Değerlendirmesi",
        "kategori":  "isg_genel",
        "aciklama":  "Çalışma ortamındaki tehlikeler, risk değerlendirme süreci, çalışanın katılımı",
        "kapsam":    "tum",
        "periyot_ay": 12,
        "tehlike":   ["Az Tehlikeli", "Tehlikeli", "Çok Tehlikeli"],
        "min_sure_dk": 60,
    },
    {
        "zon_id":    "zon_genel_kaza_meslek",
        "baslik":    "Kaza ve Meslek Hastalıkları Bildirimi",
        "kategori":  "isg_genel",
        "aciklama":  "İş kazası ve meslek hastalığı tanımı, bildirim yükümlülüğü, kayıt prosedürleri",
        "kapsam":    "tum",
        "periyot_ay": 24,
        "tehlike":   ["Az Tehlikeli", "Tehlikeli", "Çok Tehlikeli"],
        "min_sure_dk": 45,
    },
    {
        "zon_id":    "zon_giris_oryantasyon",
        "baslik":    "İşe Giriş İSG Oryantasyonu",
        "kategori":  "isg_is_giris",
        "aciklama":  "Yeni çalışanlara işyeri tanıtımı, acil çıkışlar, toplanma noktası, temel kurallar",
        "kapsam":    "yeni_isci",
        "periyot_ay": 0,
        "tehlike":   ["Az Tehlikeli", "Tehlikeli", "Çok Tehlikeli"],
        "min_sure_dk": 120,
    },

    # ── B) Acil durum eğitimleri ────────────────────────────────
    {
        "zon_id":    "zon_acil_tahliye",
        "baslik":    "Acil Durum ve Tahliye Prosedürleri",
        "kategori":  "isg_acil",
        "aciklama":  "Yangın, deprem, kimyasal sızıntı tahliye planları, toplanma noktaları, alarm sistemleri",
        "kapsam":    "tum",
        "periyot_ay": 12,
        "tehlike":   ["Az Tehlikeli", "Tehlikeli", "Çok Tehlikeli"],
        "min_sure_dk": 60,
    },
    {
        "zon_id":    "zon_acil_ilkyardim",
        "baslik":    "Temel İlk Yardım",
        "kategori":  "isg_acil",
        "aciklama":  "Temel yaşam desteği, yaralı taşıma, kimyasal yanık, göz yıkama istasyonu kullanımı",
        "kapsam":    "tum",
        "periyot_ay": 24,
        "tehlike":   ["Az Tehlikeli", "Tehlikeli", "Çok Tehlikeli"],
        "min_sure_dk": 90,
    },
    {
        "zon_id":    "zon_acil_yangin",
        "baslik":    "Yangın Güvenliği ve Söndürücü Kullanımı",
        "kategori":  "isg_acil",
        "aciklama":  "Yangın sınıfları, yangın söndürücü seçimi ve kullanımı, yangın hortumu, alarm prosedürü",
        "kapsam":    "tum",
        "periyot_ay": 12,
        "tehlike":   ["Az Tehlikeli", "Tehlikeli", "Çok Tehlikeli"],
        "min_sure_dk": 60,
    },

    # ── C) KKD eğitimleri ───────────────────────────────────────
    {
        "zon_id":    "zon_kkd_genel",
        "baslik":    "Kişisel Koruyucu Donanım (KKD) Kullanımı",
        "kategori":  "isg_kisisel",
        "aciklama":  "İşe uygun KKD seçimi, doğru giyim, bakım, depolama, ömür sonu",
        "kapsam":    "tum",
        "periyot_ay": 12,
        "tehlike":   ["Az Tehlikeli", "Tehlikeli", "Çok Tehlikeli"],
        "min_sure_dk": 45,
    },

    # ── D) Tehlikeli / Çok Tehlikeli'ye özgü ────────────────────
    {
        "zon_id":    "zon_ozel_elektrik",
        "baslik":    "Elektrik Güvenliği",
        "kategori":  "isg_ozel",
        "aciklama":  "Elektrik tehlikeleri, kilitleme/etiketleme (LOTO), yalıtım, topraklama kontrolleri",
        "kapsam":    "tum",
        "periyot_ay": 12,
        "tehlike":   ["Tehlikeli", "Çok Tehlikeli"],
        "min_sure_dk": 60,
    },
    {
        "zon_id":    "zon_ozel_kimyasal",
        "baslik":    "Kimyasal Madde Güvenliği (MSDS/SDS)",
        "kategori":  "isg_ozel",
        "aciklama":  "Güvenlik bilgi formu okuma, kimyasal depolama, dökülme prosedürü, SVHC maddeleri",
        "kapsam":    "tum",
        "periyot_ay": 12,
        "tehlike":   ["Tehlikeli", "Çok Tehlikeli"],
        "min_sure_dk": 60,
    },
    {
        "zon_id":    "zon_ozel_makine",
        "baslik":    "Makine ve Ekipman Güvenliği",
        "kategori":  "isg_ozel",
        "aciklama":  "Hareketli parçalar, koruyucu kapaklar, bakım prosedürleri, düzensiz durdurma",
        "kapsam":    "tum",
        "periyot_ay": 12,
        "tehlike":   ["Tehlikeli", "Çok Tehlikeli"],
        "min_sure_dk": 60,
    },
    {
        "zon_id":    "zon_ozel_yuksel",
        "baslik":    "Yüksekte Çalışma Güvenliği",
        "kategori":  "isg_ozel",
        "aciklama":  "Düşme önleme sistemleri, iskele güvenliği, kişisel düşme koruma ekipmanları",
        "kapsam":    "tum",
        "periyot_ay": 6,
        "tehlike":   ["Çok Tehlikeli"],
        "min_sure_dk": 90,
    },
    {
        "zon_id":    "zon_ozel_forklift",
        "baslik":    "Forklift ve İstif Makinesi Güvenliği",
        "kategori":  "isg_ozel",
        "aciklama":  "Operatör sorumlulukları, yük sınırları, güzergah kontrolü, park prosedürleri",
        "kapsam":    "belirli_gorev",
        "periyot_ay": 12,
        "tehlike":   ["Tehlikeli", "Çok Tehlikeli"],
        "min_sure_dk": 60,
    },

    # ── E) Çimento/mineral sektörüne özgü (NACE 23) ─────────────
    {
        "zon_id":    "zon_cimento_toz",
        "baslik":    "Toz ve Solunum Tehlikeleri (Çimento Sektörü)",
        "kategori":  "isg_ozel",
        "aciklama":  "Çimento tozu MTAL değerleri, solunum koruyucu seçimi, pnömokonyoz önleme",
        "kapsam":    "tum",
        "periyot_ay": 6,
        "tehlike":   ["Çok Tehlikeli"],
        "min_sure_dk": 60,
    },
    {
        "zon_id":    "zon_cimento_gurultu",
        "baslik":    "Gürültü ve Titreşimden Korunma",
        "kategori":  "isg_ozel",
        "aciklama":  "Maruziyet sınır değerleri, kulaklık kullanımı, odyometri takibi",
        "kapsam":    "tum",
        "periyot_ay": 12,
        "tehlike":   ["Çok Tehlikeli"],
        "min_sure_dk": 45,
    },

    # ── F) Toolbox / günlük toplantı ────────────────────────────
    {
        "zon_id":    "zon_toolbox",
        "baslik":    "Günlük İSG Toplantısı (Toolbox Meeting)",
        "kategori":  "toolbox",
        "aciklama":  "Günlük iş güvenliği hatırlatması, o günün tehlikeleri ve önlemler",
        "kapsam":    "tum",
        "periyot_ay": 1,
        "tehlike":   ["Az Tehlikeli", "Tehlikeli", "Çok Tehlikeli"],
        "min_sure_dk": 15,
    },
]


def tehlike_icin_zorunlu_egitimler(tehlike_sinifi: str) -> list:
    """Tehlike sınıfına göre zorunlu eğitim listesi döner."""
    return [
        e for e in ZORUNLU_EGITIM_KATALOGU
        if tehlike_sinifi in e.get("tehlike", [])
    ]


def calisan_eksik_egitimler(
    telegram_id: str,
    firma_id: str,
    tehlike_sinifi: str
) -> list:
    """
    Çalışanın almadığı veya süresi dolan zorunlu eğitimleri döner.
    Her madde: {zon_id, baslik, kategori, son_alinma, kalan_gun, durum}
    durum: "hic_alinmadi" | "suresi_dolmus" | "suresi_yaklashyor" | "guncel"
    """
    zorunlu = tehlike_icin_zorunlu_egitimler(tehlike_sinifi)
    if not zorunlu:
        return []

    try:
        from sheets import tum_kayitlar_getir
        kayitlar = tum_kayitlar_getir(firma_id=firma_id)
        # Sadece bu çalışanın geçen eğitimleri
        tid_str = str(telegram_id)
        calisan_kayitlar = [
            k for k in kayitlar
            if str(k.get("telegram_id", "")).strip() == tid_str
            and k.get("durum", "").upper() in ("GECTI", "GECTİ", "TAMAMLANDI", "PASSED")
        ]
    except Exception as e:
        logger.error(f"Kayıtlar okunamadı: {e}")
        calisan_kayitlar = []

    # Eğitim başlığı → en son geçme tarihi
    son_gecme = {}
    for k in calisan_kayitlar:
        konu = k.get("egitim_konusu", "").lower().strip()
        tur  = k.get("egitim_turu",   "").lower().strip()
        try:
            tarih = datetime.strptime(k.get("tarih", ""), "%d.%m.%Y").date()
        except:
            continue
        # hem başlık hem tür üzerinden eşleştir
        anahtar = konu or tur
        if anahtar and (anahtar not in son_gecme or tarih > son_gecme[anahtar]):
            son_gecme[anahtar] = tarih

    bugun = date.today()
    sonuc = []

    for z in zorunlu:
        zon_baslik = z["baslik"].lower()
        zon_kat    = z["kategori"].lower()
        periyot    = z["periyot_ay"]

        # Eşleşme bul: başlık veya kategori üzerinden
        son_tarih = None
        for anahtar, tarih in son_gecme.items():
            if (zon_baslik in anahtar or anahtar in zon_baslik
                    or zon_kat in anahtar or anahtar in zon_kat):
                if son_tarih is None or tarih > son_tarih:
                    son_tarih = tarih

        if periyot == 0:
            # İşe giriş eğitimi — bir kez alınması yeterli
            durum = "guncel" if son_tarih else "hic_alinmadi"
            kalan_gun = None
        elif son_tarih is None:
            durum = "hic_alinmadi"
            kalan_gun = None
        else:
            gecen_gun = (bugun - son_tarih).days
            periyot_gun = periyot * 30
            kalan = periyot_gun - gecen_gun
            kalan_gun = kalan
            if kalan < 0:
                durum = "suresi_dolmus"
            elif kalan <= 30:
                durum = "suresi_yaklashyor"
            else:
                durum = "guncel"

        sonuc.append({
            **z,
            "son_alinma":   son_tarih.strftime("%d.%m.%Y") if son_tarih else None,
            "kalan_gun":    kalan_gun,
            "durum":        durum,
        })

    return sonuc


def firma_ozet_istatistik(firma_id: str, tehlike_sinifi: str) -> dict:
    """
    Firmanın tüm çalışanları için zorunlu eğitim uyum özeti.
    Döner: {toplam_calisan, tam_uyumlu, eksik_var, hic_almamis}
    """
    try:
        from isg.personel_rapor import firma_personel_listesi
        calisanlar = firma_personel_listesi(firma_id)
    except Exception as e:
        logger.error(f"Çalışan listesi alınamadı: {e}")
        return {}

    zorunlu_sayisi = len(tehlike_icin_zorunlu_egitimler(tehlike_sinifi))
    tam = eksik = hic = 0

    for c in calisanlar:
        tid = c.get("telegram_id", "")
        if not tid:
            hic += 1
            continue
        eksikler = calisan_eksik_egitimler(tid, firma_id, tehlike_sinifi)
        kritik = [e for e in eksikler if e["durum"] in ("hic_alinmadi", "suresi_dolmus")]
        if not kritik:
            tam += 1
        elif all(e["durum"] == "hic_alinmadi" for e in eksikler):
            hic += 1
        else:
            eksik += 1

    return {
        "toplam_calisan":    len(calisanlar),
        "tam_uyumlu":        tam,
        "eksik_var":         eksik,
        "hic_almamis":       hic,
        "zorunlu_konu_sayisi": zorunlu_sayisi,
    }
