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


# ── HTML — ISG Sekmesi (Yan menü düzeni) ─────────────────────────

ISG_SEKME_HTML = """
<style data-isg>
.isg-layout{display:flex;gap:0;min-height:500px}
.isg-sidebar{width:200px;flex-shrink:0;border-right:1px solid var(--border);padding:8px 0;background:var(--bg)}
.isg-sidebar-item{display:flex;align-items:center;gap:10px;padding:10px 16px;font-size:13px;color:var(--muted);cursor:pointer;border-left:3px solid transparent;transition:all .15s;white-space:nowrap;font-weight:500;user-select:none}
.isg-sidebar-item:hover{background:var(--card);color:var(--text)}
.isg-sidebar-item.active{background:var(--card);color:var(--text);border-left-color:var(--accent);font-weight:600}
.isg-sidebar-item .isg-ikon{font-size:16px;width:20px;text-align:center}
.isg-main{flex:1;padding:20px 24px;min-width:0;overflow-x:auto}
.isg-panel-icerik{display:none}
.isg-panel-icerik.aktif{display:block}
.isg-badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600}
.isg-badge-a{background:#e8f7f0;color:#0a6640}
.isg-badge-b{background:#e6f1fb;color:#185FA5}
.isg-badge-c{background:#fff8e6;color:#856404}
.isg-badge-h{background:#fdecea;color:#a32d2d}
.isg-kart{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:16px;margin-bottom:12px}
/* Sınav modal */
.sinav-modal{display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:9999;align-items:center;justify-content:center}
.sinav-modal.open{display:flex}
.sinav-kart{background:var(--card);border-radius:16px;padding:28px;max-width:620px;width:90%;max-height:90vh;overflow-y:auto;box-shadow:0 8px 40px rgba(0,0,0,.2)}
.sinav-secenek{display:block;width:100%;text-align:left;padding:11px 16px;margin-bottom:8px;background:var(--bg);border:1.5px solid var(--border);border-radius:8px;cursor:pointer;font-size:14px;transition:all .15s}
.sinav-secenek:hover{border-color:var(--accent);background:var(--card)}
.sinav-secenek.dogru{background:#e8f7f0!important;border-color:#1a8a56!important;color:#0a6640!important}
.sinav-secenek.yanlis{background:#fdecea!important;border-color:#c0392b!important;color:#922b21!important}
.sinav-ilerleme{height:6px;background:var(--border);border-radius:3px;margin-bottom:20px;overflow:hidden}
.sinav-ilerleme-bar{height:100%;background:var(--accent);border-radius:3px;transition:width .3s}
</style>

<div class="isg-layout">
  <!-- YAN MENÜ -->
  <div class="isg-sidebar">
    <div class="isg-sidebar-item active" id="isg-nav-dashboard"   onclick="isgAltSekme('dashboard',this)">   <span class="isg-ikon">📈</span>Dashboard</div>
    <div class="isg-sidebar-item"        id="isg-nav-atamalar"    onclick="isgAltSekme('atamalar',this)">    <span class="isg-ikon">🏭</span>Atamalar</div>
    <div class="isg-sidebar-item"        id="isg-nav-firma-detay" onclick="isgAltSekme('firma-detay',this)"> <span class="isg-ikon">📋</span>Firma Detayı</div>
    <div class="isg-sidebar-item"        id="isg-nav-sure-hesap"  onclick="isgAltSekme('sure-hesap',this)">  <span class="isg-ikon">⏱️</span>Süre Hesap</div>
    <div class="isg-sidebar-item"        id="isg-nav-personel"    onclick="isgAltSekme('personel-rapor',this)"><span class="isg-ikon">📊</span>Pers. Raporu</div>
    <div class="isg-sidebar-item"        id="isg-nav-zorunlu"     onclick="isgAltSekme('zorunlu-egitim',this)" style="color:var(--red)"><span class="isg-ikon">⚠️</span>Zorunlu Eğt.</div>
    <div class="isg-sidebar-item"        id="isg-nav-audit"       onclick="isgAltSekme('audit',this)">       <span class="isg-ikon">📜</span>Denetim Kaydı</div>
  </div>

  <!-- ANA İÇERİK -->
  <div class="isg-main">

    <!-- DASHBOARD -->
    <div id="isg-panel-dashboard" class="isg-panel-icerik aktif">
      <div id="db-yukleniyor" style="text-align:center;padding:40px"><div class="spinner" style="margin:0 auto 12px"></div>Uyum skoru hesaplanıyor...</div>
      <div id="db-icerik" style="display:none">
        <div style="display:flex;align-items:center;gap:24px;margin-bottom:24px;flex-wrap:wrap">
          <div id="db-skor-daire" style="width:120px;height:120px;flex-shrink:0;position:relative">
            <svg viewBox="0 0 120 120" style="width:100%;height:100%;transform:rotate(-90deg)">
              <circle cx="60" cy="60" r="50" fill="none" stroke="var(--border)" stroke-width="10"/>
              <circle id="db-skor-arc" cx="60" cy="60" r="50" fill="none" stroke="var(--accent)" stroke-width="10"
                      stroke-dasharray="314" stroke-dashoffset="314" stroke-linecap="round" style="transition:stroke-dashoffset 1s ease"/>
            </svg>
            <div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center">
              <div id="db-skor-yazi" style="font-size:26px;font-weight:800;font-family:'Syne',sans-serif">—</div>
              <div style="font-size:10px;color:var(--muted)">/ 100</div>
            </div>
          </div>
          <div>
            <div id="db-seviye" style="font-size:18px;font-weight:700;margin-bottom:4px">—</div>
            <div id="db-firma-adi" style="font-size:13px;color:var(--muted)"></div>
            <div id="db-uyarilar" style="margin-top:8px"></div>
          </div>
        </div>
        <div id="db-maddeler" style="margin-bottom:20px"></div>
        <div id="db-aksiyonlar"></div>
      </div>
    </div>

    <!-- ATAMALAR -->
    <div id="isg-panel-atamalar" class="isg-panel-icerik">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;flex-wrap:wrap;gap:8px">
        <div style="font-size:16px;font-weight:700">Firma Atamaları</div>
        <div style="display:flex;gap:8px;flex-wrap:wrap">
          <select id="isg-atama-firma-filtre" class="form-input" style="min-width:180px" onchange="isgAtamalariYukle()">
            <option value="">Tüm Firmalar</option>
          </select>
          <button class="btn btn-primary btn-sm" onclick="isgAtamaModalAc()">+ Yeni Atama</button>
        </div>
      </div>
      <div id="isg-atama-liste"><div class="loading"><div class="spinner"></div></div></div>
    </div>

    <!-- FİRMA DETAYI -->
    <div id="isg-panel-firma-detay" class="isg-panel-icerik">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;flex-wrap:wrap;gap:8px">
        <div style="font-size:16px;font-weight:700">Firma ISG Detayı</div>
        <select id="isg-detay-firma-sec" class="form-input" style="min-width:200px" onchange="isgDetayYukle(this.value)">
          <option value="">Firma seçin...</option>
        </select>
      </div>
      <div id="isg-detay-icerik">
        <div class="isg-kart">
          <div style="font-size:13px;font-weight:600;color:var(--muted);margin-bottom:14px;text-transform:uppercase;letter-spacing:.5px">Yasal Bilgiler</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
            <div><label style="font-size:12px;color:var(--muted)">SGK Sicil No</label><input id="isg-sgk-no" class="form-input" placeholder="SGK sicil numarası"></div>
            <div><label style="font-size:12px;color:var(--muted)">NACE Kodu</label><input id="isg-nace-kodu" class="form-input" placeholder="örn: 2651"></div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:12px">
            <div>
              <label style="font-size:12px;color:var(--muted)">Tehlike Sınıfı</label>
              <select id="isg-tehlike-sinifi" class="form-input">
                <option value="">Seçin...</option>
                <option value="Az Tehlikeli">Az Tehlikeli</option>
                <option value="Tehlikeli">Tehlikeli</option>
                <option value="Çok Tehlikeli">Çok Tehlikeli</option>
              </select>
            </div>
            <div>
              <label style="font-size:12px;color:var(--muted)">Aktif Çalışan Sayısı</label>
              <input id="isg-calisan-sayisi" class="form-input" type="number" placeholder="Otomatik hesaplanır" readonly style="background:var(--bg);cursor:not-allowed">
              <div style="font-size:11px;color:var(--muted);margin-top:4px" id="isg-calisan-bilgi">Çalışanlar sekmesinden otomatik</div>
            </div>
          </div>
          <button class="btn btn-primary" style="margin-top:16px" onclick="isgDetayKaydet()">💾 Kaydet</button>
          <div id="isg-detay-mesaj" style="display:none;margin-top:8px;font-size:13px;padding:8px 12px;border-radius:6px"></div>
        </div>
      </div>
    </div>

    <!-- SÜRE HESAPLAMA -->
    <div id="isg-panel-sure-hesap" class="isg-panel-icerik">
      <div style="font-size:16px;font-weight:700;margin-bottom:16px">Süre Hesaplama</div>
      <div class="isg-kart">
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:16px">
          <div>
            <label style="font-size:12px;color:var(--muted)">Tehlike Sınıfı</label>
            <select id="sh-tehlike" class="form-input" onchange="shHesapla()">
              <option value="">Seçin...</option>
              <option value="Az Tehlikeli">Az Tehlikeli</option>
              <option value="Tehlikeli">Tehlikeli</option>
              <option value="Çok Tehlikeli">Çok Tehlikeli</option>
            </select>
          </div>
          <div>
            <label style="font-size:12px;color:var(--muted)">Aktif Çalışan Sayısı</label>
            <input id="sh-calisan" type="number" class="form-input" placeholder="Otomatik yükleniyor..." oninput="shHesapla()" readonly style="background:var(--bg)">
            <div style="font-size:11px;color:var(--muted);margin-top:4px" id="sh-calisan-bilgi"></div>
          </div>
          <div>
            <label style="font-size:12px;color:var(--muted)">Uzman Sınıfı</label>
            <select id="sh-uzman-sinif" class="form-input" onchange="shHesapla()">
              <option value="">Seçin...</option>
              <option value="A">A Sınıfı</option>
              <option value="B">B Sınıfı</option>
              <option value="C">C Sınıfı</option>
            </select>
          </div>
        </div>
        <div id="sh-bos" style="text-align:center;padding:20px;color:var(--muted)">Tehlike sınıfı ve çalışan sayısını girin</div>
        <div id="sh-sonuc" style="display:none">
          <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px;margin-bottom:16px">
            <div class="isg-kart" style="margin:0;text-align:center">
              <div style="font-size:26px;font-weight:800;font-family:'Syne',sans-serif;color:var(--accent)" id="sh-toplam-saat">—</div>
              <div style="font-size:11px;color:var(--muted)">Yıllık Toplam Eğitim Saati</div>
              <div style="font-size:11px;color:var(--muted);margin-top:4px" id="sh-egitim-aciklama"></div>
            </div>
            <div class="isg-kart" style="margin:0;text-align:center">
              <div style="font-size:26px;font-weight:800;font-family:'Syne',sans-serif;color:#1a8a56" id="sh-aylik-saat">—</div>
              <div style="font-size:11px;color:var(--muted)">Aylık Ortalama Saat</div>
            </div>
            <div class="isg-kart" style="margin:0;text-align:center">
              <div style="font-size:26px;font-weight:800;font-family:'Syne',sans-serif" id="sh-kisi-saat">—</div>
              <div style="font-size:11px;color:var(--muted)">Kişi Başı Yıllık Saat</div>
            </div>
          </div>
          <div class="isg-kart" style="margin:0">
            <div style="font-size:13px;font-weight:600;margin-bottom:10px">İSG Uzmanı Zorunlu Çalışma Süresi</div>
            <div id="sh-tam-zamanli-badge" style="display:none;background:#fdecea;color:var(--red);padding:8px 12px;border-radius:8px;font-weight:600;font-size:13px;margin-bottom:10px">⚠️ TAM ZAMANLI UZMAN ZORUNLU</div>
            <div id="sh-uzman-saat-row">
              <span style="font-size:22px;font-weight:800;font-family:'Syne',sans-serif" id="sh-uzman-dk">—</span>
              <span style="font-size:13px;color:var(--muted)" id="sh-uzman-birim">dakika/ay</span>
            </div>
            <div style="font-size:12px;color:var(--muted);margin-top:6px" id="sh-uzman-aciklama"></div>
            <div id="sh-sinif-uyari" style="display:none;margin-top:10px;padding:8px 12px;border-radius:8px;font-size:12px"></div>
          </div>
          <button class="btn btn-primary" style="margin-top:14px" onclick="shKaydet()">💾 Hesabı Kaydet</button>
        </div>
      </div>
    </div>

    <!-- PERSONEL RAPORU -->
    <div id="isg-panel-personel-rapor" class="isg-panel-icerik">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;flex-wrap:wrap;gap:8px">
        <div style="font-size:16px;font-weight:700">Personel Eğitim Raporu</div>
        <div style="display:flex;gap:8px">
          <select id="pr-yil" class="form-input" onchange="prYukle()"></select>
          <button class="btn btn-dark btn-sm" onclick="prYukle()">🔄 Yenile</button>
        </div>
      </div>
      <div id="pr-yukleniyor" style="text-align:center;padding:40px;display:none"><div class="spinner" style="margin:0 auto 12px"></div>Yükleniyor...</div>
      <div id="pr-bos" style="text-align:center;padding:40px;color:var(--muted);display:none">Veri yok</div>
      <div id="pr-firma-ozet" style="display:none">
        <div class="isg-kart" style="margin-bottom:16px">
          <div style="font-size:13px;font-weight:600;margin-bottom:10px">Aylık Eğitim Saati</div>
          <div style="display:flex;align-items:flex-end;gap:6px;height:80px" id="pr-bar-chart"></div>
          <div style="display:flex;gap:6px;margin-top:4px;overflow-x:auto" id="pr-bar-labels"></div>
        </div>
      </div>
      <div id="pr-tablo-wrap" style="display:none">
        <div style="overflow-x:auto">
          <table>
            <thead><tr id="pr-thead-row"><th>Çalışan</th><th>Görev</th><th>Yıllık Toplam</th></tr></thead>
            <tbody id="pr-tbody"></tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- ZORUNLU EĞİTİMLER -->
    <div id="isg-panel-zorunlu-egitim" class="isg-panel-icerik">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;flex-wrap:wrap;gap:8px">
        <div style="font-size:16px;font-weight:700">Zorunlu İSG Eğitimleri</div>
        <div style="display:flex;gap:6px;flex-wrap:wrap">
          <button class="btn btn-dark btn-sm" id="ze-f-tum"    onclick="zeFiltre('tum',this)"  style="background:var(--accent);color:#fff;border:none">Tümü</button>
          <button class="btn btn-dark btn-sm" id="ze-f-eksik"  onclick="zeFiltre('eksik',this)">Eksik Var</button>
          <button class="btn btn-dark btn-sm" id="ze-f-hic"    onclick="zeFiltre('hic',this)">Hiç Almamış</button>
          <button class="btn btn-dark btn-sm" id="ze-f-tamam"  onclick="zeFiltre('tamam',this)">Uyumlu</button>
          <button class="btn btn-primary btn-sm" id="ze-toplu-btn" onclick="zeTopluGonder()" style="display:none">📤 Seçililere Gönder</button>
          <button class="btn btn-dark btn-sm" onclick="zeYukle()">🔄 Yenile</button>
        </div>
      </div>
      <div id="ze-yukleniyor" style="text-align:center;padding:40px;display:none"><div class="spinner" style="margin:0 auto 12px"></div>Yükleniyor...</div>
      <div id="ze-ozet" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:10px;margin-bottom:16px"></div>
      <div id="ze-liste"></div>
    </div>

    <!-- DENETİM KAYDI -->
    <div id="isg-panel-audit" class="isg-panel-icerik">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;flex-wrap:wrap;gap:8px">
        <div style="font-size:16px;font-weight:700">Denetim Kaydı</div>
        <select id="isg-audit-firma-filtre" class="form-input" style="min-width:180px" onchange="isgAuditYukle()">
          <option value="">Tüm Firmalar</option>
        </select>
      </div>
      <div id="isg-audit-liste"><div class="loading"><div class="spinner"></div></div></div>
    </div>

  </div><!-- /isg-main -->
</div><!-- /isg-layout -->

<!-- SINAV MODAL -->
<div id="sinav-modal" class="sinav-modal">
  <div class="sinav-kart">
    <div style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;color:var(--muted);margin-bottom:6px">🛡️ Zorunlu İSG Eğitimi Sınavı</div>
    <div id="sinav-egitim-baslik" style="font-size:16px;font-weight:700;margin-bottom:16px">—</div>
    <div class="sinav-ilerleme"><div class="sinav-ilerleme-bar" id="sinav-ilerleme-bar" style="width:0%"></div></div>
    <div id="sinav-soru-no" style="font-size:12px;color:var(--muted);margin-bottom:8px">Soru 1/10</div>
    <div id="sinav-soru-metin" style="font-size:15px;font-weight:600;margin-bottom:14px;line-height:1.5">—</div>
    <div id="sinav-secenekler"></div>
    <div id="sinav-sonuc-panel" style="display:none;margin-top:16px">
      <div id="sinav-sonuc-kutu" style="padding:16px;border-radius:10px;text-align:center"></div>
      <div style="display:flex;gap:8px;margin-top:12px;justify-content:center">
        <button class="btn btn-dark" onclick="sinavModalKapat()">Kapat</button>
        <button class="btn btn-primary" id="sinav-tekrar-btn" onclick="sinavBaslat(_sinavVeri)" style="display:none">🔄 Tekrar Dene</button>
      </div>
    </div>
    <button onclick="sinavModalKapat()" style="position:absolute;top:16px;right:16px;background:none;border:none;font-size:18px;cursor:pointer;color:var(--muted)">✕</button>
  </div>
</div>
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
        return jsonify({"hata": str(e)}), 500

@isg_blueprint.route("/uzmanlar/<uzman_id>", methods=["GET"])
def uzman_getir_route(uzman_id):
    k = _giris_kontrol()
    if k: return k
    try:
        from isg.uzmanlar import uzman_getir
        u = uzman_getir(uzman_id)
        return jsonify(u) if u else (jsonify({"hata": "Bulunamadı"}), 404)
    except Exception as e:
        return jsonify({"hata": str(e)}), 500

@isg_blueprint.route("/uzmanlar", methods=["POST"])
def uzman_ekle_route():
    k = _giris_kontrol()
    if k: return k
    veri = request.get_json()
    try:
        from isg.uzmanlar import uzman_ekle, tum_uzmanlar
        mevcut = tum_uzmanlar()
        if any(u.get("sertifika_no") == veri.get("sertifika_no") and veri.get("sertifika_no") for u in mevcut):
            return jsonify({"basarili": False, "hata": "Bu sertifika no ile kayıtlı uzman var"})
        uzman_id = uzman_ekle(veri)
        return jsonify({"basarili": True, "uzman_id": uzman_id})
    except Exception as e:
        return jsonify({"basarili": False, "hata": str(e)})

@isg_blueprint.route("/uzmanlar/<uzman_id>", methods=["PUT"])
def uzman_guncelle_route(uzman_id):
    k = _giris_kontrol()
    if k: return k
    veri = request.get_json()
    try:
        from isg.uzmanlar import uzman_guncelle
        uzman_guncelle(uzman_id, veri)
        return jsonify({"basarili": True})
    except Exception as e:
        return jsonify({"basarili": False, "hata": str(e)})

@isg_blueprint.route("/uzmanlar/<uzman_id>/pasif", methods=["POST"])
def uzman_pasif_route(uzman_id):
    k = _giris_kontrol()
    if k: return k
    try:
        from isg.uzmanlar import uzman_pasif_yap
        uzman_pasif_yap(uzman_id)
        return jsonify({"basarili": True})
    except Exception as e:
        return jsonify({"basarili": False, "hata": str(e)})

@isg_blueprint.route("/atamalar", methods=["GET"])
def atamalar_listele():
    k = _giris_kontrol()
    if k: return k
    firma_id = request.args.get("firma_id", "")
    try:
        from isg.atama_gecmisi import tum_satirlar as atama_satirlar, SEKME as ATAMA_SEKME, BASLIKLAR as ATAMA_BASLIKLAR
        from isg.sheets_base import tum_satirlar
        from isg.uzmanlar import uzman_getir
        atamalar = tum_satirlar(ATAMA_SEKME, ATAMA_BASLIKLAR)
        sonuc = []
        for a in atamalar:
            if firma_id and a.get("firma_id") != firma_id:
                continue
            if a.get("aktif", "1") == "0":
                continue
            u = uzman_getir(a.get("uzman_id", "")) or {}
            sonuc.append({**a, "uzman_ad": u.get("ad_soyad", "—"), "uzman_sinifi": u.get("sinif", ""), "uzman_unvan": u.get("unvan", "")})
        return jsonify(sonuc)
    except Exception as e:
        logger.error(f"Atamalar hatası: {e}")
        return jsonify([])

@isg_blueprint.route("/atamalar", methods=["POST"])
def atama_ekle_route():
    k = _giris_kontrol()
    if k: return k
    veri = request.get_json()
    try:
        from isg.atama_gecmisi import atama_ekle
        from isg.audit_log import log_yaz
        atama_id = atama_ekle(veri)
        log_yaz("atama_ekle", veri.get("firma_id", ""), f"Uzman {veri.get('uzman_id')} atandı")
        return jsonify({"basarili": True, "atama_id": atama_id})
    except Exception as e:
        return jsonify({"basarili": False, "hata": str(e)})

@isg_blueprint.route("/atamalar/<atama_id>/bitir", methods=["POST"])
def atama_bitir_route(atama_id):
    k = _giris_kontrol()
    if k: return k
    try:
        from isg.atama_gecmisi import atama_bitir
        atama_bitir(atama_id)
        return jsonify({"basarili": True})
    except Exception as e:
        return jsonify({"basarili": False, "hata": str(e)})

@isg_blueprint.route("/firma-detay", methods=["GET"])
def firma_detay_getir_route():
    k = _giris_kontrol()
    if k: return k
    firma_id = request.args.get("firma_id", "")
    try:
        from isg.firma_detay import firma_detay_getir
        d = firma_detay_getir(firma_id) if firma_id else {}
        try:
            from calisanlar import tum_calisanlar
            calisanlar = tum_calisanlar(firma_id=firma_id)
            aktif_sayi = len([c for c in calisanlar.values()
                              if str(c.get("aktif", "1")) not in ("0", "false", "False")])
            d["aktif_calisan_sayisi"] = aktif_sayi
        except:
            d["aktif_calisan_sayisi"] = 0
        return jsonify(d)
    except Exception as e:
        return jsonify({"hata": str(e)}), 500

@isg_blueprint.route("/firma-detay", methods=["POST"])
def firma_detay_kaydet_route():
    k = _giris_kontrol()
    if k: return k
    veri = request.get_json()
    try:
        from isg.firma_detay import firma_detay_kaydet
        from isg.audit_log import log_yaz
        fid = veri.get("firma_id", "")
        firma_detay_kaydet(
            fid,
            veri.get("sgk_sicil_no") or veri.get("sgk_no", ""),
            veri.get("nace_kodu", ""),
            veri.get("tehlike_sinifi", ""),
            str(veri.get("calisan_sayisi", "")),
        )
        log_yaz("firma_detay_guncelle", fid, "Firma ISG detayı güncellendi")
        return jsonify({"basarili": True})
    except Exception as e:
        return jsonify({"basarili": False, "hata": str(e)})

@isg_blueprint.route("/sgk-nace", methods=["GET"])
def sgk_nace_route():
    k = _giris_kontrol()
    if k: return k
    firma_id = request.args.get("firma_id", "")
    try:
        from isg.firma_detay import firma_detay_getir
        d = firma_detay_getir(firma_id)
        return jsonify({"sgk_no": d.get("sgk_no", ""), "nace_kodu": d.get("nace_kodu", ""), "tehlike_sinifi": d.get("tehlike_sinifi", "")})
    except Exception as e:
        return jsonify({"hata": str(e)}), 500

@isg_blueprint.route("/audit", methods=["GET"])
def audit_listele():
    k = _giris_kontrol()
    if k: return k
    firma_id = request.args.get("firma_id", "")
    try:
        from isg.audit_log import log_listesi
        return jsonify(log_listesi(firma_id=firma_id or None, limit=100))
    except Exception as e:
        return jsonify([])

@isg_blueprint.route("/egitim-uzman-bilgisi", methods=["GET"])
def egitim_uzman_bilgisi():
    k = _giris_kontrol()
    if k: return k
    firma_id = request.args.get("firma_id", "")
    try:
        from isg.firma_detay import firma_detay_getir
        from isg.atama_gecmisi import tum_satirlar as atama_satirlar, SEKME as ATAMA_SEKME, BASLIKLAR as ATAMA_BASLIKLAR
        from isg.sheets_base import tum_satirlar
        from isg.uzmanlar import uzman_getir
        detay = firma_detay_getir(firma_id)
        atamalar = tum_satirlar(ATAMA_SEKME, ATAMA_BASLIKLAR)
        aktif_atama = next((a for a in atamalar if a.get("firma_id") == firma_id and a.get("aktif", "1") != "0"), None)
        uzman = uzman_getir(aktif_atama["uzman_id"]) if aktif_atama else None
        return jsonify({
            "tehlike_sinifi": detay.get("tehlike_sinifi", ""),
            "uzman_ad": uzman.get("ad_soyad", "") if uzman else "",
            "uzman_sinif": uzman.get("sinif", "") if uzman else "",
        })
    except Exception as e:
        return jsonify({"hata": str(e)}), 500

@isg_blueprint.route("/sure-hesap", methods=["POST"])
def sure_hesap():
    k = _giris_kontrol()
    if k: return k
    veri = request.get_json()
    firma_id = veri.get("firma_id", "")
    try:
        from isg.sure_hesap import firma_sure_ozeti
        try:
            calisan_sayisi = int(veri.get("calisan_sayisi", 0)) or None
        except:
            calisan_sayisi = None
        ozet = firma_sure_ozeti(firma_id, calisan_sayisi_override=calisan_sayisi)
        try:
            from isg.sure_hesap import sure_hesap_kaydet
            sure_hesap_kaydet(firma_id, ozet)
        except:
            pass
        return jsonify({"basarili": True, "ozet": ozet})
    except Exception as e:
        return jsonify({"basarili": False, "hata": str(e)})

@isg_blueprint.route("/sure-hesap", methods=["GET"])
def sure_hesap_get():
    k = _giris_kontrol()
    if k: return k
    firma_id = request.args.get("firma_id", "")
    try:
        from isg.sure_hesap import firma_sure_ozeti
        from calisanlar import tum_calisanlar
        calisanlar = tum_calisanlar(firma_id=firma_id)
        aktif_sayi = len([c for c in calisanlar.values()
                          if str(c.get("aktif", "1")) not in ("0", "false", "False")])
        ozet = firma_sure_ozeti(firma_id, calisan_sayisi_override=aktif_sayi if aktif_sayi else None)
        ozet["aktif_calisan_sayisi"] = aktif_sayi
        return jsonify(ozet)
    except Exception as e:
        return jsonify({"hata": str(e)}), 500

@isg_blueprint.route("/personel-rapor", methods=["GET"])
def personel_rapor():
    k = _giris_kontrol()
    if k: return k
    firma_id = request.args.get("firma_id", "")
    try:
        yil = int(request.args.get("yil", 0)) or None
    except:
        yil = None
    if not firma_id:
        return jsonify({"hata": "firma_id zorunlu"}), 400
    try:
        from isg.personel_rapor import aylik_egitim_ozeti, firma_personel_listesi
        ozet = aylik_egitim_ozeti(firma_id, yil)
        personel = firma_personel_listesi(firma_id)
        for p in personel:
            tid = str(p.get("telegram_id", ""))
            if tid and tid not in ozet.get("calisanlar", {}):
                ozet.setdefault("calisanlar", {})[tid] = {
                    "ad_soyad": p["ad_soyad"],
                    "gorev": p.get("gorev", ""),
                    "aylar": {},
                    "yillik_toplam_dk": 0,
                    "yillik_toplam_saat": 0,
                    "egitim_sayisi": 0,
                }
        return jsonify(ozet)
    except Exception as e:
        logger.error(f"Personel rapor hatası: {e}")
        return jsonify({"hata": str(e)}), 500

@isg_blueprint.route("/dashboard", methods=["GET"])
def isg_dashboard():
    k = _giris_kontrol()
    if k: return k
    firma_id = request.args.get("firma_id", "")
    if not firma_id:
        return jsonify({"hata": "firma_id zorunlu"}), 400
    try:
        from isg.dashboard import firma_uyum_skoru
        return jsonify(firma_uyum_skoru(firma_id))
    except Exception as e:
        logger.error(f"Dashboard hatası: {e}")
        return jsonify({"hata": str(e)}), 500

@isg_blueprint.route("/dashboard-tum", methods=["GET"])
def isg_dashboard_tum():
    k = _giris_kontrol()
    if k: return k
    try:
        from isg.dashboard import tum_firmalar_dashboard
        return jsonify(tum_firmalar_dashboard())
    except Exception as e:
        return jsonify([])

@isg_blueprint.route("/zorunlu-egitimler", methods=["GET"])
def zorunlu_egitimler():
    k = _giris_kontrol()
    if k: return k
    firma_id = request.args.get("firma_id", "")
    if not firma_id:
        return jsonify({"hata": "firma_id zorunlu"}), 400
    try:
        tehlike = request.args.get("tehlike_sinifi", "")
        if not tehlike:
            from isg.firma_detay import firma_detay_getir
            tehlike = firma_detay_getir(firma_id).get("tehlike_sinifi", "")

        from isg.zorunlu_egitim import tehlike_icin_zorunlu_egitimler, calisan_eksik_egitimler, firma_ozet_istatistik
        from isg.personel_rapor import firma_personel_listesi

        calisanlar = firma_personel_listesi(firma_id)
        zorunlu_liste = tehlike_icin_zorunlu_egitimler(tehlike)
        ozet = firma_ozet_istatistik(firma_id, tehlike)

        calisan_durumlar = []
        for c in calisanlar:
            tid = c.get("telegram_id", "")
            eksikler = calisan_eksik_egitimler(tid, firma_id, tehlike) if tid else [
                {**e, "durum": "hic_alinmadi", "son_alinma": None, "kalan_gun": None}
                for e in zorunlu_liste
            ]
            calisan_durumlar.append({
                "telegram_id": tid,
                "ad_soyad":    c.get("ad_soyad", ""),
                "gorev":       c.get("gorev", ""),
                "egitimler":   eksikler,
                "eksik_sayisi": len([e for e in eksikler if e["durum"] in ("hic_alinmadi", "suresi_dolmus")]),
                "yaklasan_sayisi": len([e for e in eksikler if e["durum"] == "suresi_yaklashyor"]),
            })

        calisan_durumlar.sort(key=lambda x: x["eksik_sayisi"], reverse=True)
        return jsonify({"firma_id": firma_id, "tehlike": tehlike, "zorunlu_liste": zorunlu_liste, "calisanlar": calisan_durumlar, "ozet": ozet})
    except Exception as e:
        logger.error(f"Zorunlu eğitim hatası: {e}")
        return jsonify({"hata": str(e)}), 500


@isg_blueprint.route("/zorunlu-egitim-sorular", methods=["POST"])
def zorunlu_egitim_sorular():
    """Belirli bir zorunlu eğitim konusu için 10 soru döner."""
    k = _giris_kontrol()
    if k: return k
    veri = request.get_json()
    zon_id = veri.get("zon_id", "")
    baslik = veri.get("baslik", "")
    try:
        sorular = _soru_uret(zon_id)
        return jsonify({"basarili": True, "sorular": sorular, "baslik": baslik})
    except Exception as e:
        return jsonify({"basarili": False, "hata": str(e)})


@isg_blueprint.route("/zorunlu-egitim-sinav-sonuc", methods=["POST"])
def zorunlu_egitim_sinav_sonuc():
    """Sınav sonucunu kaydeder. Geçerse eğitim kaydı oluşturur."""
    k = _giris_kontrol()
    if k: return k
    veri = request.get_json()
    firma_id    = veri.get("firma_id", "")
    telegram_id = veri.get("telegram_id", "")
    baslik      = veri.get("baslik", "")
    puan        = int(veri.get("puan", 0))
    gecti       = veri.get("gecti", False)
    try:
        if gecti and telegram_id:
            from datetime import date
            from sheets import _servis
            bugun = date.today().strftime("%d.%m.%Y")
            s, sid = _servis()
            try:
                from firma_manager import firma_kayit_sekme_bul
                sekme = firma_kayit_sekme_bul(firma_id)
            except:
                sekme = "Sayfa1"
            yeni_satir = [
                bugun, "00:00",
                veri.get("ad_soyad", ""), str(telegram_id),
                veri.get("gorev", ""), baslik,
                "isg_zorunlu", str(puan), "GEÇTİ", "—", "", "1",
            ]
            try:
                s.values().append(
                    spreadsheetId=sid, range=f"{sekme}!A:L",
                    valueInputOption="RAW", body={"values": [yeni_satir]}
                ).execute()
            except Exception as ex:
                logger.warning(f"Kayıt yazılamadı: {ex}")
        return jsonify({"basarili": True, "gecti": gecti, "puan": puan})
    except Exception as e:
        logger.error(f"Sınav sonuç hatası: {e}")
        return jsonify({"basarili": False, "hata": str(e)})


@isg_blueprint.route("/zorunlu-egitim-gonder", methods=["POST"])
def zorunlu_egitim_gonder():
    """Çalışana zorunlu eğitim bildirimi + sınav hatırlatması gönderir."""
    k = _giris_kontrol()
    if k: return k
    veri = request.get_json()
    firma_id       = veri.get("firma_id", "")
    egitim_id      = veri.get("egitim_id", "")
    konu           = veri.get("konu", "")
    telegram_idler = veri.get("telegram_idler", [])
    if not firma_id or not telegram_idler:
        return jsonify({"basarili": False, "hata": "firma_id ve en az bir telegram_id zorunlu"})
    try:
        import os, requests as req_lib, time
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        base  = f"https://api.telegram.org/bot{token}"
        mesaj_baslik = konu or "Zorunlu İSG Eğitimi"
        if egitim_id:
            try:
                from egitimler_sheets import tum_egitimler
                eg = tum_egitimler().get(egitim_id)
                if eg: mesaj_baslik = eg["baslik"]
            except: pass
        basarili = gonderilemeyen = 0
        for tid in telegram_idler:
            try:
                metin = (
                    f"🛡️ *Zorunlu İSG Eğitimi*\n\n*{mesaj_baslik}*\n\n"
                    f"Bu eğitim, 6331 sayılı İş Sağlığı ve Güvenliği Kanunu kapsamında "
                    f"*yasal zorunluluktur*.\n\nPanelden sınava girmeniz bekleniyor.\n"
                    f"Minimum geçer puan: *70/100*"
                )
                payload = {"chat_id": int(tid), "text": metin, "parse_mode": "Markdown"}
                if egitim_id:
                    payload["reply_markup"] = {"inline_keyboard": [[{"text": "▶️ Eğitime Başla", "callback_data": f"egitim_baslat:{egitim_id}"}]]}
                    try:
                        from durum import ekstra_hak_ver, aktif_egitim_set
                        aktif_egitim_set(egitim_id); ekstra_hak_ver(int(tid))
                    except: pass
                r = req_lib.post(f"{base}/sendMessage", json=payload, timeout=10)
                if r.json().get("ok"): basarili += 1
                else: gonderilemeyen += 1
                time.sleep(0.05)
            except: gonderilemeyen += 1
        return jsonify({"basarili": True, "gonderilen": basarili, "gonderilemeyen": gonderilemeyen})
    except Exception as e:
        logger.error(f"Zorunlu eğitim gönderme hatası: {e}")
        return jsonify({"basarili": False, "hata": str(e)})


@isg_blueprint.route("/html", methods=["GET"])
def isg_html():
    return ISG_SEKME_HTML, 200, {"Content-Type": "text/html"}


# ── Soru bankası ─────────────────────────────────────────────────

def _soru_uret(zon_id: str) -> list:
    import random
    BANKA = {
        "zon_genel_isg_hukuk": [
            {"soru":"6331 sayılı İSG Kanunu hangi yılda yürürlüğe girmiştir?","secenekler":["2010","2012","2015","2018"],"dogru_idx":1},
            {"soru":"İşverenin temel İSG yükümlülüğü hangisidir?","secenekler":["Maaş ödemek","Sağlık ve güvenliği sağlamak","Sözleşme yapmak","Sigorta yapmak"],"dogru_idx":1},
            {"soru":"İSG eğitimine katılım zorunlu mudur?","secenekler":["Gönüllülük esasıdır","Evet, zorunludur","Sadece yeni işçiler için","İşveren isterse"],"dogru_idx":1},
            {"soru":"İSG kurulu kaç çalışanın üzerinde kurulur?","secenekler":["10","25","50","100"],"dogru_idx":2},
            {"soru":"Risk değerlendirmesi en az ne sıklıkla yenilenmeli?","secenekler":["10 yılda bir","2 yılda bir ve tehlike değişince","Hiç yenilenmez","Kaza olunca"],"dogru_idx":1},
            {"soru":"Çalışan ciddi tehlikede çalışmaktan kaçınabilir mi?","secenekler":["Hayır","Evet","Sadece yönetici onayıyla","Tazminat ödeyerek"],"dogru_idx":1},
            {"soru":"İSG eğitimi çalışma süresinden sayılır mı?","secenekler":["Hayır","Evet","Yarı sayılır","Çalışan seçer"],"dogru_idx":1},
            {"soru":"En yetkili iş güvenliği uzmanı sınıfı hangisidir?","secenekler":["C","B","A","Eşit yetkili"],"dogru_idx":2},
            {"soru":"OSGB ne demektir?","secenekler":["Ortak Sağlık ve Güvenlik Birimi","Özel Sigorta Güvence Birliği","Ortak Sigorta Güvence Bürosu","Ofis Sağlık Güvenlik Belgesi"],"dogru_idx":0},
            {"soru":"Çok tehlikeli sınıfta tam zamanlı uzman zorunluluğu kaç çalışandan başlar?","secenekler":["500","250","1000","100"],"dogru_idx":1},
        ],
        "zon_genel_tehlike_risk": [
            {"soru":"Risk değerlendirmesinin amacı nedir?","secenekler":["Yasal zorunluluk","Tehlikeleri tanımlayıp önlem almak","Sigorta azaltmak","Çalışan belirlemek"],"dogru_idx":1},
            {"soru":"Tehlike ile risk arasındaki fark nedir?","secenekler":["Aynı anlama gelir","Tehlike: zarar potansiyeli, Risk: olasılık","Risk: zarar potansiyeli, Tehlike: olasılık","Fark yoktur"],"dogru_idx":1},
            {"soru":"Risk azaltmada ilk adım nedir?","secenekler":["KKD","İdari kontrol","Kaynakta yok etmek","İkaz levhası"],"dogru_idx":2},
            {"soru":"Hangisi fiziksel tehlike değildir?","secenekler":["Gürültü","Titreşim","Kimyasal soluma","Yetersiz aydınlatma"],"dogru_idx":2},
            {"soru":"GBF/SDS belgesi ne anlama gelir?","secenekler":["Garanti Belgesi Formu","Güvenlik Bilgi Formu","Gümrük Beyanname Formu","Genel Bilgi Formu"],"dogru_idx":1},
            {"soru":"Ergonomik risk faktörü hangisidir?","secenekler":["Gürültü","Tekrarlayan hareketler","Kimyasal toz","Elektrik"],"dogru_idx":1},
            {"soru":"Risk matrisi neyi gösterir?","secenekler":["Çalışan sayısını","Olasılık × Şiddet","Tazminat miktarını","Uzman sayısını"],"dogru_idx":1},
            {"soru":"Psikososyal risk faktörü hangisidir?","secenekler":["Gürültü","İş stresi","Toz","Titreşim"],"dogru_idx":1},
            {"soru":"Çimento fabrikasında sık meslek hastalığı nedir?","secenekler":["Astım","Pnömokonyoz/Silikoz","Egzama","Alerji"],"dogru_idx":1},
            {"soru":"Risk değerlendirmesinde çalışan temsilcisi yer almalı mı?","secenekler":["Hayır","Evet, zorunlu","Tercihe bağlı","Sadece tehlikeli işyerlerinde"],"dogru_idx":1},
        ],
        "zon_genel_kaza_meslek": [
            {"soru":"İş kazası bildirimi kaç iş günü içinde SGK'ya yapılır?","secenekler":["3","7","15","30"],"dogru_idx":0},
            {"soru":"Meslek hastalığı bildirim süresi nedir?","secenekler":["3 iş günü","6 ay","Yıllık raporda","Gerek yok"],"dogru_idx":0},
            {"soru":"İş kazası tanımı hangisidir?","secenekler":["Evde kaza","İşyeri veya bağlantılı ortamda kaza","Yolda her kaza","Ölümlü kazalar"],"dogru_idx":1},
            {"soru":"Kaza kayıt formuna hangisi yazılmaz?","secenekler":["Kaza tarihi","Maaş","Yaralanan kısım","Kaza şekli"],"dogru_idx":1},
            {"soru":"İş kazasında ilk yapılması gereken nedir?","secenekler":["Form doldurmak","İlk yardım sağlamak","Yöneticiye bildirmek","Kameralara bakmak"],"dogru_idx":1},
            {"soru":"Kaza ağacı analizi ne amaçla yapılır?","secenekler":["Ceza vermek","Nedenleri bulmak ve önlemek","Tazminat hesaplamak","Sigorta başvurusu"],"dogru_idx":1},
            {"soru":"Ramak kala nedir?","secenekler":["Ölümlü kaza","Kaza olmaksızın tehlikeli durum","Küçük yaralanma","Meslek hastalığı"],"dogru_idx":1},
            {"soru":"Meslek hastalığı tespiti kim tarafından yapılır?","secenekler":["İşyeri hekimi tek başına","SGK yetkili tesisleri","İşveren","Sendika"],"dogru_idx":1},
            {"soru":"Kaza yerini bozmak ne zaman mümkündür?","secenekler":["Hiçbir zaman","Soruşturmadan önce","İlk yardım sonrası güvenli ortamda","Ölümlü kazalarda"],"dogru_idx":2},
            {"soru":"SGK bildirimi için hangi form kullanılır?","secenekler":["Form E-1","İş Kazası Bildirim Formu","Vergi Beyannamesi","İstirahat Raporu"],"dogru_idx":1},
        ],
        "zon_giris_oryantasyon": [
            {"soru":"İşe giriş oryantasyonu ne zaman verilmeli?","secenekler":["İlk 1 ayda","İşe başlarken","6 ay sonra","Talep halinde"],"dogru_idx":1},
            {"soru":"Toplanma noktası nedir?","secenekler":["Yemek yeri","Tahliyede toplanma alanı","Depo","Yönetim binası"],"dogru_idx":1},
            {"soru":"Acil çıkış kapılarını yeni çalışanın bilmesi zorunlu mu?","secenekler":["Hayır","Evet","Sadece güvenlik","Yalnızca fabrika"],"dogru_idx":1},
            {"soru":"Oryantasyonda mutlaka anlatılması gereken hangisidir?","secenekler":["Şirket tarihi","Acil durumda yapılacaklar","Yemek saatleri","Ücret politikası"],"dogru_idx":1},
            {"soru":"İşe giriş oryantasyonu en az ne kadar sürmeli?","secenekler":["15 dakika","120 dakika","Belge imzalanır","Yöneticiye bağlı"],"dogru_idx":1},
            {"soru":"KKD teslim belgesi ne işe yarar?","secenekler":["Sigorta","Teslim edildiğini kanıtlar","Vergi belgesi","Giriş formu"],"dogru_idx":1},
            {"soru":"Yangın söndürücünün yeri oryantasyonda gösterilir mi?","secenekler":["Çalışan bulur","Evet, gösterilir","Yangın sırasında","Öğretilmez"],"dogru_idx":1},
            {"soru":"Çalışan tehlikeli durum fark ederse ne yapmalı?","secenekler":["Görmezden gelmeli","Yetkili kişiye bildirmeli","Kendi düzeltmeli","Beklemeli"],"dogru_idx":1},
            {"soru":"İç yönetmelik çalışana ne zaman verilmeli?","secenekler":["1 yıl sonra","İşe başlarken","Sadece talep","Yönetim kararı"],"dogru_idx":1},
            {"soru":"Oryantasyonu aldığını hangi belge kanıtlar?","secenekler":["Sözlü beyan","İmzalı katılım tutanağı","E-posta","Sosyal medya"],"dogru_idx":1},
        ],
        "zon_acil_tahliye": [
            {"soru":"Yangın alarmında ilk yapılması gereken nedir?","secenekler":["Yangını söndürmek","Panik yapmadan tahliye","Değerli eşya toplamak","Asansör kullanmak"],"dogru_idx":1},
            {"soru":"Tahliyede asansör kullanılabilir mi?","secenekler":["Evet, hızlıdır","Hayır, yangında asansör tehlikelidir","Tercihe bağlı","Sadece bodrum katta"],"dogru_idx":1},
            {"soru":"Tahliye tatbikatı ne sıklıkla yapılmalı?","secenekler":["Her 10 yılda","Yılda en az bir kez","Hiç gerekmez","Yeni çalışan gelince"],"dogru_idx":1},
            {"soru":"Duman yoğunken nasıl ilerlenmeli?","secenekler":["Koşarak","Eğilerek ve ağzı kapatarak","Dik durarak","Pencereden atlayarak"],"dogru_idx":1},
            {"soru":"Toplanma noktasına varınca ne yapılır?","secenekler":["Hemen döner","Kalabalığa katılır","Sorumluya isim bildirir","Eve gider"],"dogru_idx":2},
            {"soru":"A sınıfı yangın söndürücü ne için kullanılır?","secenekler":["Yakıt yangınları","Metal yangınları","Katı madde yangınları","Elektrik"],"dogru_idx":2},
            {"soru":"Acil çıkış önü her zaman nasıl olmalı?","secenekler":["Kilitli","Boş ve erişilebilir","Depo alanı","Tercihle"],"dogru_idx":1},
            {"soru":"Acil durum planı kim hazırlar?","secenekler":["Sadece çalışanlar","İşveren, uzman ve çalışan","Belediye","Sadece uzman"],"dogru_idx":1},
            {"soru":"Bilinç kontrolü nasıl yapılır?","secenekler":["Omzuna vurur, seslenilir","Soğuk su dökülür","Hareket ettirilir","Bırakılır"],"dogru_idx":0},
            {"soru":"Yangın söndürücü sınıfları arasında B sınıfı ne için kullanılır?","secenekler":["Katı maddeler","Sıvı ve gaz yangınları","Metal","Elektrik"],"dogru_idx":1},
        ],
        "zon_kkd": [
            {"soru":"KKD ne anlama gelir?","secenekler":["Kaza Kontrol Defteri","Kişisel Koruyucu Donanım","Kimyasal Koruma Dep.","Küçük Kaza Defteri"],"dogru_idx":1},
            {"soru":"KKD kullanımı zorunlu mudur?","secenekler":["Gönüllülük","Zorunludur","İşveren kararı","Sadece tehlikeli"],"dogru_idx":1},
            {"soru":"Baret hangi tehlikeden korur?","secenekler":["Gürültü","Düşen nesneler","Kimyasal","Toz"],"dogru_idx":1},
            {"soru":"Kulak tıkacı nasıl takılır?","secenekler":["Dışarıdan","Yuvarlayıp kulak kanalına","Sadece tutulur","Uzman takar"],"dogru_idx":1},
            {"soru":"Kimyasal eldiven hasar görünce ne yapılmalı?","secenekler":["Bantla onarılır","Hemen değiştirilir","Tek elle devam","Raporlanır devam"],"dogru_idx":1},
            {"soru":"Güvenlik gözlüğü hangi tehlikeye karşı kullanılır?","secenekler":["Gürültü","Parça sıçraması ve kimyasal","Düşme","Titreşim"],"dogru_idx":1},
            {"soru":"Emniyet kemeri ne zaman takılmalı?","secenekler":["İşveren isterse","2 metre ve üzeri","Sadece dışarıda","Hiçbir zaman"],"dogru_idx":1},
            {"soru":"FFP2 maske sınıfı neyi belirtir?","secenekler":["Düşük filtre","Orta filtre, çimento için uygun","Soğuk hava","Gaz filtresi"],"dogru_idx":1},
            {"soru":"KKD kullanmayan çalışana ne yapılabilir?","secenekler":["Hiçbir şey","Disiplin işlemi","Sadece uyarı","Akdi feshedilemez"],"dogru_idx":1},
            {"soru":"KKD bakım sorumluluğu kime ait?","secenekler":["Yalnızca çalışan","İşveren sağlar, çalışan uygun kullanır","Yalnızca işveren","Uzman yapar"],"dogru_idx":1},
        ],
        "zon_cimento_toz": [
            {"soru":"Çimento tozu hangi hastalığa neden olabilir?","secenekler":["Diyabet","Silikoz/Pnömokonyoz","Hipertansiyon","Deri kanseri"],"dogru_idx":1},
            {"soru":"Akciğerleri korumak için hangi maske?","secenekler":["Cerrahi maske","FFP2/FFP3 toz maskesi","Bez maske","Kaplin maskesi"],"dogru_idx":1},
            {"soru":"Toz ölçümü ne sıklıkla yapılmalı?","secenekler":["Sadece kaza sonrası","Periyodik (en az yılda bir)","Hiç gerekmez","10 yılda bir"],"dogru_idx":1},
            {"soru":"GBF belgesi ne işe yarar?","secenekler":["Satış belgesi","Kimyasal tehlike ve korunma bilgisi","Kalite belgesi","Gümrük belgesi"],"dogru_idx":1},
            {"soru":"Solunum fonksiyon testi (SFT) neden yapılır?","secenekler":["Kan sayımı","Akciğer sağlığı takibi","Göz muayenesi","Diş muayenesi"],"dogru_idx":1},
            {"soru":"Toz kontrolünde öncelikli yöntem nedir?","secenekler":["KKD","Kaynak kontrolü (ıslak yöntem/havalandırma)","Pencere açmak","Koku giderici"],"dogru_idx":1},
            {"soru":"Toz patlaması riski nerede yüksektir?","secenekler":["Islak ortam","Kuru ince toz birikimi kapalı alan","Açık hava","Su bazlı ortam"],"dogru_idx":1},
            {"soru":"Silikoza karşı en etkin önlem nedir?","secenekler":["Vitamin takviyesi","Kristalize silika tozundan kaçınmak","Sıvı tüketimi","Egzersiz"],"dogru_idx":1},
            {"soru":"OEL sınır değeri aşılırsa ne yapılır?","secenekler":["Devam edilir","Çalışma durdurulur önlem alınır","Bildirim yok","Doz artırılır"],"dogru_idx":1},
            {"soru":"Çimento tozuna maruz kalma sınır değerini kim belirler?","secenekler":["İşveren","Mevzuat (yönetmelik)","Çalışan","Sigorta şirketi"],"dogru_idx":1},
        ],
        "zon_gurultu": [
            {"soru":"Yasal gürültü maruziyet sınır değeri (LEX,8h) nedir?","secenekler":["70 dB(A)","80 dB(A)","87 dB(A)","100 dB(A)"],"dogru_idx":2},
            {"soru":"Alt eylem değeri (ilk sınır) kaç dB(A)?","secenekler":["75","80","85","90"],"dogru_idx":1},
            {"soru":"Gürültüden korunmak için hangi KKD?","secenekler":["Baret","Kulak koruyucu","Yüz siperi","Eldiven"],"dogru_idx":1},
            {"soru":"Uzun süreli gürültü hangi hastalığa yol açar?","secenekler":["Görme kaybı","Gürültüye bağlı işitme kaybı","Cilt hastalığı","Bel fıtığı"],"dogru_idx":1},
            {"soru":"Gürültü ölçümü kim yapar?","secenekler":["Herhangi çalışan","Yetkili kuruluş veya uzman","Operatör","İK"],"dogru_idx":1},
            {"soru":"İdari kontrol yöntemi hangisidir?","secenekler":["Makineyi kapatmak","Maruz kalma süresini kısaltmak","KKD","Havalandırma"],"dogru_idx":1},
            {"soru":"85 dB üzerinde gürültüde işveren ne yapmalı?","secenekler":["Hiçbir şey","KKD sağlamak","Levha koymak","İşçiyi çıkarmak"],"dogru_idx":1},
            {"soru":"İşitme kaybı takibi için hangi test?","secenekler":["Göz testi","Odyometri","Kan testi","EKG"],"dogru_idx":1},
            {"soru":"Gürültü haritası neyi gösterir?","secenekler":["Fabrika planı","Gürültü dağılımı","Çalışan dağılımı","Ürün akışı"],"dogru_idx":1},
            {"soru":"Gürültü izolasyonu için ne kullanılır?","secenekler":["Hızlı çalışmak","Akustik panel ve bariyer","Camları açmak","Kısa mola"],"dogru_idx":1},
        ],
        "zon_ilk_yardim": [
            {"soru":"İlk yardımın amacı nedir?","secenekler":["Tedavi etmek","Hayat kurtarmak, kötüleşmeyi önlemek","Bildirim yapmak","İşe döndürmek"],"dogru_idx":1},
            {"soru":"KPR'de bası/solunum oranı nedir?","secenekler":["15/1","30/2","10/3","20/1"],"dogru_idx":1},
            {"soru":"Bilinç kaybında önce ne yapılır?","secenekler":["Su verilir","Havayolu açılır, solunum kontrol","Kaldırılır","Soğuk bez"],"dogru_idx":1},
            {"soru":"Kimyasal yanıkta ilk yapılacak nedir?","secenekler":["Yağ sürmek","Bol suyla yıkamak","Karbonat","Sarmak"],"dogru_idx":1},
            {"soru":"Elektrik çarpmasında ilk adım nedir?","secenekler":["Kişiye dokunmak","Elektriği kesmek","Su dökmek","İtmek"],"dogru_idx":1},
            {"soru":"Göze kimyasal sıçradığında ne yapılır?","secenekler":["Ovuşturmak","15-20 dk bol su","Göz damlası","Bırakmak"],"dogru_idx":1},
            {"soru":"Burun kanamasında doğru pozisyon hangisidir?","secenekler":["Başı geri","Hafif öne eğerek sıkıştırmak","Yatmak","Sola çevirmek"],"dogru_idx":1},
            {"soru":"Şok belirtisi hangisidir?","secenekler":["Kızarma","Solukluk, soğuk ter, hızlı nabız","Yüksek tansiyon","Ağrısızlık"],"dogru_idx":1},
            {"soru":"İlk yardım çantasında ne olmalı?","secenekler":["İlaç ve iğne","Yara örtüsü, sargı, makas, eldiven","Antibiyotik","Ateş ölçer"],"dogru_idx":1},
            {"soru":"İlk yardımcı sayısı (tehlikeli, 10-49 çalışan)?","secenekler":["Zorunlu değil","En az 1","En az 2","En az 3"],"dogru_idx":1},
        ],
        "zon_cimento_elektrik": [
            {"soru":"Elektrik güvenliğinin temel kuralı nedir?","secenekler":["Hızlı çalışmak","LOTO prosedürüne uymak","İzoleli eldiven yeterli","Sigorta atınca devam"],"dogru_idx":1},
            {"soru":"LOTO ne anlama gelir?","secenekler":["Liman Op. Takip Ofisi","Kilitleme-Etiketleme enerji izolasyonu","Lojistik Taşıma Org.","Lokal Takip Onayı"],"dogru_idx":1},
            {"soru":"Elektrik paneline müdahale öncesi ne yapılmalı?","secenekler":["Hemen girilir","Enerji kesilir LOTO uygulanır","Eldiven takılır devam","Amir bilgi devam"],"dogru_idx":1},
            {"soru":"Islak ortamda elektrikli alet tehlikeli mi?","secenekler":["Alet paslanır","Su iletken, çarpma riski artar","Verim düşer","Garanti bozulur"],"dogru_idx":1},
            {"soru":"Topraklama ne işe yarar?","secenekler":["Akım artırır","Kaçak akımı toprağa iletir","Gürültü azaltır","Hız düzenler"],"dogru_idx":1},
            {"soru":"Elektrik çarpmış kişiye elleriyle dokunulur mu?","secenekler":["Evet hemen","Hayır, önce kaynak kesilir","Eldiven varsa evet","Plastikle"],"dogru_idx":1},
            {"soru":"Hasar görmüş kablo izolasyonunda ne yapılır?","secenekler":["Bantlanır devam","Yetkili ekibe bildirilir, kullanımdan çıkarılır","Devam edilir","Topraklanır"],"dogru_idx":1},
            {"soru":"Kaçak akım rölesi ne işe yarar?","secenekler":["Akım artırır","Kaçak akım algılar devreyi keser","Voltaj ölçer","Enerji tasarrufu"],"dogru_idx":1},
            {"soru":"Ex-proof ekipman ne anlama gelir?","secenekler":["Pahalı","Patlayıcı ortamda kullanılabilir","Extra büyük","Tasarruflu"],"dogru_idx":1},
            {"soru":"Elektrikli ekipman bakımı ne zaman yapılır?","secenekler":["Çalışırken","LOTO sonrası","Sadece arıza sonrası","Vardiya bitiminde"],"dogru_idx":1},
        ],
        "zon_yuksekte_calisma": [
            {"soru":"Yüksekte çalışma sınırı kaç metre üzerinde başlar?","secenekler":["1","2","3","5"],"dogru_idx":1},
            {"soru":"Emniyet kemeri neye bağlanmalı?","secenekler":["Rastgele bir noktaya","Güvenilir ankraj noktasına","Yalnızca 5m üzeri","İsteğe bağlı"],"dogru_idx":1},
            {"soru":"İskele kurulumundan önce ne yapılmalı?","secenekler":["Hemen çıkılır","Yetkili onayı","Fotoğraf çekilir","Çalışan inisiyatifi"],"dogru_idx":1},
            {"soru":"Çatı çalışmalarında zorunlu KKD nedir?","secenekler":["Yalnızca baret","Tam vücut kemeri ve baret","Yalnızca eldiven","KKD gerekmez"],"dogru_idx":1},
            {"soru":"Fırtına ve buzda yüksekte çalışılır mı?","secenekler":["Evet","Hayır, durdurulur","Sadece yağmurda","Tercihe bağlı"],"dogru_idx":1},
            {"soru":"Düşmeyi önleme sistemi bileşenleri nelerdir?","secenekler":["Sadece kemer","Ankraj, bağlantı, tam vücut kemeri","Yalnızca ip","Baret ve gözlük"],"dogru_idx":1},
            {"soru":"İskele taşıma kapasitesi aşılırsa ne olur?","secenekler":["Maliyet artar","Çöküp düşme riski","Temizlik zorlaşır","Garanti bozulur"],"dogru_idx":1},
            {"soru":"Toplu koruma örneği nedir?","secenekler":["Kemer","Korkuluk ve güvenlik ağı","Baret","Ayakkabı"],"dogru_idx":1},
            {"soru":"Yüksekte ekipman kontrolü ne zaman yapılır?","secenekler":["Yıllık bakımda","Her kullanımdan önce","Sadece yeni ekipmanda","Hasar sonrası"],"dogru_idx":1},
            {"soru":"Merdivenden çalışırken en az kaç el merdivende olmalı?","secenekler":["Sıfır","En az bir el","İki el serbest","Tercihe bağlı"],"dogru_idx":1},
        ],
        "toolbox": [
            {"soru":"Toolbox toplantısının amacı nedir?","secenekler":["Üretim hedefleri","Günlük İSG risklerini paylaşmak","Maaş tartışmak","Şikâyetleri toplamak"],"dogru_idx":1},
            {"soru":"Toolbox ne sıklıkla yapılmalı?","secenekler":["Yılda bir","Aylık","Günlük/vardiya başında","Kaza sonrası"],"dogru_idx":2},
            {"soru":"Katılım zorunlu mudur?","secenekler":["İsteğe bağlı","Evet, beklenir","Sadece yöneticiler","Yalnızca yeni işçi"],"dogru_idx":1},
            {"soru":"Toplantıda hangi konu ele alınmaz?","secenekler":["Günün tehlikeleri","Kaza önleme","Siyasi tartışmalar","KKD kullanımı"],"dogru_idx":2},
            {"soru":"Tutanak tutulmalı mı?","secenekler":["Hayır","Evet, imzalı tutanak","Ölümlüden sonra","Tercihe bağlı"],"dogru_idx":1},
            {"soru":"Vardiya başı toolbox'ın faydası nedir?","secenekler":["Zaman kaybı","Riskleri önceden fark etmek","Sadece kayıt","Zorunlu değil"],"dogru_idx":1},
            {"soru":"Güvenli olmayan durum fark eden ne yapmalı?","secenekler":["Görmezden gelmeli","Bildirmeli","Kendi düzeltmeli","Beklemeli"],"dogru_idx":1},
            {"soru":"Çalışanlar toplantıda konuşabilir mi?","secenekler":["Hayır, dinlenir","Evet, teşvik edilir","Sadece kıdemliler","Yazılıyla"],"dogru_idx":1},
            {"soru":"Son olaylar toolbox'ta paylaşılmalı mı?","secenekler":["Hayır","Evet, benzer olayları önlemek için","Sadece kaza olursa","Sigorta halleder"],"dogru_idx":1},
            {"soru":"Toolbox süresi genellikle ne kadar?","secenekler":["2 saat","5-15 dakika","1 saat","Süre yok"],"dogru_idx":1},
        ],
    }

    # Eşleştirme
    sorular = BANKA.get(zon_id, [])
    if not sorular:
        for anahtar, liste in [
            ("hukuk", "zon_genel_isg_hukuk"), ("risk", "zon_genel_tehlike_risk"),
            ("tehlike", "zon_genel_tehlike_risk"), ("kaza", "zon_genel_kaza_meslek"),
            ("meslek", "zon_genel_kaza_meslek"), ("giris", "zon_giris_oryantasyon"),
            ("oryant", "zon_giris_oryantasyon"), ("acil", "zon_acil_tahliye"),
            ("tahliye", "zon_acil_tahliye"), ("yangin", "zon_acil_tahliye"),
            ("kkd", "zon_kkd"), ("kisisel", "zon_kkd"),
            ("toz", "zon_cimento_toz"), ("solum", "zon_cimento_toz"),
            ("gurult", "zon_gurultu"), ("ilk_yardim", "zon_ilk_yardim"),
            ("yardim", "zon_ilk_yardim"), ("elektrik", "zon_cimento_elektrik"),
            ("yuksek", "zon_yuksekte_calisma"), ("toolbox", "toolbox"),
        ]:
            if anahtar in zon_id.lower():
                sorular = BANKA.get(liste, [])
                break
    if not sorular:
        sorular = BANKA["zon_genel_isg_hukuk"]

    kopya = list(sorular)
    random.shuffle(kopya)
    return kopya[:10]
