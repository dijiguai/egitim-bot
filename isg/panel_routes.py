"""
isg/panel_routes.py
===================
ISG modülü Flask route'ları ve panel HTML'i.
Tüm endpoint'ler /panel/isg/... altında.
"""

import logging
from flask import request, jsonify, session, render_template_string
from isg import isg_blueprint

logger = logging.getLogger(__name__)


def _giris_kontrol():
    if not session.get("panel_giris"):
        return jsonify({"basarili": False, "hata": "Yetkisiz"}), 401
    return None


# ── HTML — ISG Sekmesi (panel.py'deki tab sistemiyle uyumlu) ─────

ISG_SEKME_HTML = """
<div style="max-width:1000px;margin:0 auto">

    <!-- Alt sekmeler -->
    <div style="display:flex;gap:4px;margin-bottom:24px;border-bottom:1px solid var(--border);overflow-x:auto">
      <div class="isg-alt-tab active" onclick="isgAltSekme('uzmanlar',this)" style="padding:10px 16px;font-size:13px;color:#666;cursor:pointer;border-bottom:2px solid transparent;white-space:nowrap;font-weight:500">👤 Uzmanlar</div>
      <div class="isg-alt-tab" onclick="isgAltSekme('atamalar',this)" style="padding:10px 16px;font-size:13px;color:#666;cursor:pointer;border-bottom:2px solid transparent;white-space:nowrap;font-weight:500">🏭 Firma Atamaları</div>
      <div class="isg-alt-tab" onclick="isgAltSekme('firma-detay',this)" style="padding:10px 16px;font-size:13px;color:#666;cursor:pointer;border-bottom:2px solid transparent;white-space:nowrap;font-weight:500">📋 Firma ISG Detayı</div>
      <div class="isg-alt-tab" onclick="isgAltSekme('audit',this)" style="padding:10px 16px;font-size:13px;color:#666;cursor:pointer;border-bottom:2px solid transparent;white-space:nowrap;font-weight:500">📜 Denetim Kaydı</div>
    </div>

    <!-- UZMANLAR -->
    <div id="isg-panel-uzmanlar" class="isg-alt-panel">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;flex-wrap:wrap;gap:10px">
        <div style="font-family:Syne,sans-serif;font-weight:700;font-size:16px">Uzman / Hekim Kartları</div>
        <button class="btn btn-primary" onclick="isgUzmanModalAc()">+ Yeni Uzman Ekle</button>
      </div>
      <div id="isg-uzman-liste"><div class="loading"><div class="spinner"></div></div></div>
    </div>

    <!-- ATAMALAR -->
    <div id="isg-panel-atamalar" class="isg-alt-panel" style="display:none">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;flex-wrap:wrap;gap:10px">
        <div style="font-family:Syne,sans-serif;font-weight:700;font-size:16px">Firma ↔ Uzman Görevlendirmeleri</div>
        <button class="btn btn-primary" onclick="isgAtamaModalAc()">+ Yeni Atama</button>
      </div>
      <div style="margin-bottom:12px">
        <select id="isg-atama-firma-filtre" style="background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:8px 12px;font-size:13px;color:var(--text);outline:none" onchange="isgAtamalariYukle()">
          <option value="">Tüm Firmalar</option>
        </select>
      </div>
      <div id="isg-atama-liste"><div class="loading"><div class="spinner"></div></div></div>
    </div>

    <!-- FİRMA ISG DETAYI -->
    <div id="isg-panel-firma-detay" class="isg-alt-panel" style="display:none">
      <div style="font-family:Syne,sans-serif;font-weight:700;font-size:16px;margin-bottom:16px">Firma ISG Bilgileri</div>
      <div style="margin-bottom:16px">
        <select id="isg-detay-firma-sec" style="width:100%;max-width:360px;background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:9px 12px;font-size:13px;color:var(--text);outline:none" onchange="isgFirmaDetayYukle()">
          <option value="">Firma seçin...</option>
        </select>
      </div>
      <div id="isg-firma-detay-form" style="display:none">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px">
          <div>
            <div style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:6px">SGK Sicil No</div>
            <div style="display:flex;gap:8px">
              <input type="text" id="isg-sgk-no" class="form-input" placeholder="örn: 012345678901234" oninput="isgSgkDenNace()">
              <button class="btn btn-dark btn-sm" onclick="isgSgkDenNace()">NACE Tahmin</button>
            </div>
          </div>
          <div>
            <div style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:6px">NACE Kodu</div>
            <input type="text" id="isg-nace-kodu" class="form-input" placeholder="örn: 23.51">
          </div>
          <div>
            <div style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:6px">Tehlike Sınıfı</div>
            <select id="isg-tehlike-sinifi" class="form-input">
              <option value="">Seçin veya NACE tahminini kullanın</option>
              <option value="Az Tehlikeli">🟢 Az Tehlikeli</option>
              <option value="Tehlikeli">🟡 Tehlikeli</option>
              <option value="Çok Tehlikeli">🔴 Çok Tehlikeli</option>
            </select>
          </div>
          <div>
            <div style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:6px">Çalışan Sayısı</div>
            <input type="number" id="isg-calisan-sayisi" class="form-input" placeholder="örn: 45">
          </div>
        </div>
        <div id="isg-nace-tahmin-uyari" style="display:none;padding:10px 14px;background:#e8f7f0;border:1px solid #b7e8d0;border-radius:8px;font-size:13px;color:var(--green);margin-bottom:14px"></div>
        <button class="btn btn-primary" onclick="isgFirmaDetayKaydet()">Kaydet</button>
      </div>
      <div id="isg-firma-detay-ozet" style="margin-top:20px"></div>
    </div>

    <!-- DENETİM KAYDI -->
    <div id="isg-panel-audit" class="isg-alt-panel" style="display:none">
      <div style="font-family:Syne,sans-serif;font-weight:700;font-size:16px;margin-bottom:16px">Denetim Kaydı (Audit Log)</div>
      <div style="background:#fff8e6;border:1px solid #f5d87a;border-radius:10px;padding:12px 16px;font-size:13px;color:#856404;margin-bottom:16px">
        📜 Bu kayıtlar değiştirilemez. ÇSGB denetiminde ibraz edilebilir.
      </div>
      <div id="isg-audit-liste"><div class="loading"><div class="spinner"></div></div></div>
    </div>

</div>

<!-- UZMAN EKLE/DÜZENLE MODAL -->
<div class="modal-overlay" id="isg-uzman-modal">
  <div class="modal" style="max-width:500px">
    <div class="modal-title" id="isg-uzman-modal-baslik">Uzman / Hekim Ekle</div>
    <input type="hidden" id="isg-uzman-id">
    <div class="form-group">
      <label class="form-label">Ad Soyad *</label>
      <input type="text" class="form-input" id="isg-u-ad" placeholder="Ahmet Yılmaz">
    </div>
    <div class="form-group">
      <label class="form-label">Unvan *</label>
      <select class="form-input" id="isg-u-unvan" onchange="isgUnvanDegisti()">
        <option value="">Seçin</option>
        <option value="is_guvenligi_uzmani">İş Güvenliği Uzmanı</option>
        <option value="isyeri_hekimi">İşyeri Hekimi</option>
        <option value="diger_saglik">Diğer Sağlık Personeli</option>
        <option value="usta_ogretici">Usta Öğretici</option>
        <option value="isveren">İşveren / Vekili</option>
      </select>
    </div>
    <div class="form-group" id="isg-sinif-grup">
      <label class="form-label">Sınıf * <span style="font-size:11px;color:var(--muted)">(Uzman için zorunlu)</span></label>
      <select class="form-input" id="isg-u-sinif">
        <option value="—">— (Hekim / DSP)</option>
        <option value="A">A Sınıfı</option>
        <option value="B">B Sınıfı</option>
        <option value="C">C Sınıfı</option>
      </select>
    </div>
    <div class="form-group">
      <label class="form-label">Sertifika / Belge No *</label>
      <input type="text" class="form-input" id="isg-u-sertifika" placeholder="örn: 384571">
    </div>
    <div class="form-group">
      <label class="form-label">Diploma No <span style="font-size:11px;color:var(--muted)">(Hekim için)</span></label>
      <input type="text" class="form-input" id="isg-u-diploma" placeholder="Opsiyonel">
    </div>
    <div id="isg-uzman-hata" class="alert alert-red" style="display:none"></div>
    <div class="modal-footer">
      <button class="btn btn-primary" style="flex:1" onclick="isgUzmanKaydet()">Kaydet</button>
      <button class="btn btn-dark" onclick="modalKapat('isg-uzman-modal')">İptal</button>
    </div>
  </div>
</div>

<!-- ATAMA MODAL -->
<div class="modal-overlay" id="isg-atama-modal">
  <div class="modal" style="max-width:460px">
    <div class="modal-title">Uzman Firmaya Ata</div>
    <div class="form-group">
      <label class="form-label">Uzman *</label>
      <select class="form-input" id="isg-atama-uzman"></select>
    </div>
    <div class="form-group">
      <label class="form-label">Firma *</label>
      <select class="form-input" id="isg-atama-firma"></select>
    </div>
    <div class="form-group">
      <label class="form-label">Görev Tipi *</label>
      <select class="form-input" id="isg-atama-tip">
        <option value="is_guvenligi_uzmani">İş Güvenliği Uzmanı olarak</option>
        <option value="isyeri_hekimi">İşyeri Hekimi olarak</option>
        <option value="diger_saglik">Diğer Sağlık Personeli olarak</option>
      </select>
    </div>
    <div class="form-group">
      <label class="form-label">Başlangıç Tarihi * (GG.AA.YYYY)</label>
      <input type="text" class="form-input" id="isg-atama-bas" placeholder="01.01.2025">
    </div>
    <div style="background:#fff8e6;border:1px solid #f5d87a;border-radius:8px;padding:10px 14px;font-size:12px;color:#856404;margin-bottom:16px">
      ⚠️ Aynı firmada aynı tipte aktif atama varsa otomatik sonlandırılır.
    </div>
    <div id="isg-atama-hata" class="alert alert-red" style="display:none"></div>
    <div class="modal-footer">
      <button class="btn btn-primary" style="flex:1" onclick="isgAtamaKaydet()">Ata</button>
      <button class="btn btn-dark" onclick="modalKapat('isg-atama-modal')">İptal</button>
    </div>
  </div>
</div>

<!-- AYRILMA MODAL -->
<div class="modal-overlay" id="isg-ayrilma-modal">
  <div class="modal" style="max-width:420px">
    <div class="modal-title">Görevlendirmeyi Sonlandır</div>
    <div class="modal-sub" id="isg-ayrilma-ozet"></div>
    <input type="hidden" id="isg-ayrilma-atama-id">
    <div class="form-group" style="margin-top:16px">
      <label class="form-label">Ayrılış Tarihi * (GG.AA.YYYY)</label>
      <input type="text" class="form-input" id="isg-ayrilma-tarih" placeholder="31.12.2025">
    </div>
    <div style="background:#fdecea;border:1px solid #f5bcb8;border-radius:8px;padding:10px 14px;font-size:12px;color:var(--red);margin-bottom:16px">
      Bu tarihe kadar yapılan eğitimler bu uzmanın kaydında kalır.
    </div>
    <div class="modal-footer">
      <button class="btn btn-red" style="flex:1" onclick="isgAyrılmaKaydet()">Sonlandır</button>
      <button class="btn btn-dark" onclick="modalKapat('isg-ayrilma-modal')">İptal</button>
    </div>
  </div>
</div>

<style>
.isg-alt-tab.active { color: var(--text) !important; border-bottom-color: var(--accent) !important; }
.isg-kart { background:var(--card);border:1px solid var(--border);border-radius:12px;padding:18px;margin-bottom:10px }
.isg-badge { display:inline-block;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600 }
.isg-badge-a { background:#fdecea;color:var(--red) }
.isg-badge-b { background:#fff8e6;color:#856404 }
.isg-badge-c { background:#e8f7f0;color:var(--green) }
.isg-badge-h { background:#e6f1fb;color:#185FA5 }
</style>


"""


# ── API Route'ları ────────────────────────────────────────────────

@isg_blueprint.route("/uzmanlar", methods=["GET"])
def uzmanlar_listele():
    k = _giris_kontrol()
    if k: return k
    try:
        from isg.uzmanlar import tum_uzmanlar
        return jsonify(tum_uzmanlar())
    except Exception as e:
        logger.error(f"Uzmanlar listele hatası: {e}")
        return jsonify({"hata": str(e)}), 500


@isg_blueprint.route("/uzmanlar/<uzman_id>", methods=["GET"])
def uzman_getir_route(uzman_id):
    k = _giris_kontrol()
    if k: return k
    from isg.uzmanlar import uzman_getir
    u = uzman_getir(uzman_id)
    if u: return jsonify(u)
    return jsonify({"hata": "Bulunamadı"}), 404


@isg_blueprint.route("/uzmanlar", methods=["POST"])
def uzman_ekle_route():
    k = _giris_kontrol()
    if k: return k
    veri = request.get_json() or {}
    try:
        from isg.uzmanlar import uzman_ekle
        uzman_id = uzman_ekle(
            ad_soyad=veri.get("ad_soyad", ""),
            unvan=veri.get("unvan", ""),
            sinif=veri.get("sinif", "—"),
            sertifika_no=veri.get("sertifika_no", ""),
            diploma_no=veri.get("diploma_no", ""),
        )
        if uzman_id:
            return jsonify({"basarili": True, "uzman_id": uzman_id})
        return jsonify({"basarili": False, "hata": "Eklenemedi. Unvan ve sertifika no kontrol edin."})
    except Exception as e:
        return jsonify({"basarili": False, "hata": str(e)})


@isg_blueprint.route("/uzmanlar/<uzman_id>", methods=["PUT"])
def uzman_guncelle_route(uzman_id):
    k = _giris_kontrol()
    if k: return k
    veri = request.get_json() or {}
    try:
        from isg.uzmanlar import uzman_guncelle
        ok = uzman_guncelle(
            uzman_id,
            ad_soyad=veri.get("ad_soyad"),
            unvan=veri.get("unvan"),
            sinif=veri.get("sinif"),
            sertifika_no=veri.get("sertifika_no"),
            diploma_no=veri.get("diploma_no"),
        )
        return jsonify({"basarili": ok})
    except Exception as e:
        return jsonify({"basarili": False, "hata": str(e)})


@isg_blueprint.route("/uzmanlar/<uzman_id>/pasif", methods=["POST"])
def uzman_pasif_route(uzman_id):
    k = _giris_kontrol()
    if k: return k
    from isg.uzmanlar import uzman_pasif_yap
    ok = uzman_pasif_yap(uzman_id)
    return jsonify({"basarili": ok})


@isg_blueprint.route("/atamalar", methods=["GET"])
def atamalar_listele():
    k = _giris_kontrol()
    if k: return k
    firma_id = request.args.get("firma_id", "")
    try:
        from isg.atama_gecmisi import firma_atama_gecmisi
        from isg.uzmanlar import uzman_getir
        from firma_manager import tum_firmalar

        firmalar = tum_firmalar()
        if firma_id:
            atamalar = firma_atama_gecmisi(firma_id)
        else:
            from isg.sheets_base import tum_satirlar
            from isg.atama_gecmisi import SEKME, BASLIKLAR, _satir_to_dict
            satirlar = tum_satirlar(SEKME)
            atamalar = [_satir_to_dict(s) for s in satirlar if s]

        # Uzman ve firma adlarını ekle
        for a in atamalar:
            u = uzman_getir(a.get("uzman_id", "")) or {}
            a["uzman_ad_soyad"] = u.get("ad_soyad", "")
            a["uzman_sinif"] = u.get("sinif", "")
            a["firma_ad"] = firmalar.get(a.get("firma_id", ""), {}).get("ad", "")

        return jsonify(atamalar)
    except Exception as e:
        logger.error(f"Atamalar listele hatası: {e}")
        return jsonify([])


@isg_blueprint.route("/atamalar", methods=["POST"])
def atama_ekle_route():
    k = _giris_kontrol()
    if k: return k
    veri = request.get_json() or {}
    try:
        from isg.atama_gecmisi import atama_ekle
        atama_id = atama_ekle(
            uzman_id=veri.get("uzman_id", ""),
            firma_id=veri.get("firma_id", ""),
            unvan_tipi=veri.get("unvan_tipi", "is_guvenligi_uzmani"),
            baslangic_tarihi=veri.get("baslangic_tarihi", ""),
        )
        if atama_id:
            return jsonify({"basarili": True, "atama_id": atama_id})
        return jsonify({"basarili": False, "hata": "Atama kaydedilemedi"})
    except Exception as e:
        return jsonify({"basarili": False, "hata": str(e)})


@isg_blueprint.route("/atamalar/<atama_id>/bitir", methods=["POST"])
def atama_bitir_route(atama_id):
    k = _giris_kontrol()
    if k: return k
    veri = request.get_json() or {}
    from isg.atama_gecmisi import atama_bitir
    ok = atama_bitir(atama_id, veri.get("bitis_tarihi", ""))
    return jsonify({"basarili": ok})


@isg_blueprint.route("/firma-detay", methods=["GET"])
def firma_detay_getir_route():
    k = _giris_kontrol()
    if k: return k
    firma_id = request.args.get("firma_id", "")
    from isg.firma_detay import firma_detay_getir
    return jsonify(firma_detay_getir(firma_id))


@isg_blueprint.route("/firma-detay", methods=["POST"])
def firma_detay_kaydet_route():
    k = _giris_kontrol()
    if k: return k
    veri = request.get_json() or {}
    try:
        from isg.firma_detay import firma_detay_kaydet
        ok = firma_detay_kaydet(
            firma_id=veri.get("firma_id", ""),
            sgk_sicil_no=veri.get("sgk_sicil_no", ""),
            nace_kodu=veri.get("nace_kodu", ""),
            tehlike_sinifi=veri.get("tehlike_sinifi", ""),
            calisan_sayisi=veri.get("calisan_sayisi", ""),
        )
        return jsonify({"basarili": ok})
    except Exception as e:
        return jsonify({"basarili": False, "hata": str(e)})


@isg_blueprint.route("/sgk-nace", methods=["GET"])
def sgk_nace_route():
    k = _giris_kontrol()
    if k: return k
    sgk = request.args.get("sgk", "")
    from isg.firma_detay import sgk_den_nace, nace_tahmin
    nace = sgk_den_nace(sgk)
    tehlike = nace_tahmin(nace) if nace else ""
    return jsonify({"nace_kodu": nace, "tehlike_sinifi": tehlike})


@isg_blueprint.route("/audit", methods=["GET"])
def audit_listele():
    k = _giris_kontrol()
    if k: return k
    try:
        from isg.sheets_base import tum_satirlar
        from isg.audit_log import SEKME, BASLIKLAR
        satirlar = tum_satirlar(SEKME)
        kayitlar = []
        for s in reversed(satirlar):  # en yenisi üstte
            if s:
                while len(s) < len(BASLIKLAR):
                    s.append("")
                kayitlar.append(dict(zip(BASLIKLAR, s)))
        return jsonify(kayitlar[:200])  # son 200 kayıt
    except Exception as e:
        return jsonify([])


@isg_blueprint.route("/egitim-uzman-bilgisi", methods=["GET"])
def egitim_uzman_bilgisi():
    """Bot mesajı için: firma + tarih → uzman bilgisi."""
    firma_id = request.args.get("firma_id", "")
    tarih = request.args.get("tarih", "")
    try:
        from isg.atama_gecmisi import uzman_bilgisi_bul
        return jsonify(uzman_bilgisi_bul(firma_id, tarih))
    except Exception as e:
        return jsonify({})


@isg_blueprint.route("/html", methods=["GET"])
def isg_html():
    """Panel'e gömülecek HTML bloğunu döner."""
    return ISG_SEKME_HTML, 200, {"Content-Type": "text/html"}
