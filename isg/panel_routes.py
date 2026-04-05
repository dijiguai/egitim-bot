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
      <div class="isg-alt-tab active" onclick="isgAltSekme('atamalar',this)" style="padding:10px 16px;font-size:13px;color:#666;cursor:pointer;border-bottom:2px solid transparent;white-space:nowrap;font-weight:500">🏭 Firma Atamaları</div>
      <div class="isg-alt-tab" onclick="isgAltSekme('firma-detay',this)" style="padding:10px 16px;font-size:13px;color:#666;cursor:pointer;border-bottom:2px solid transparent;white-space:nowrap;font-weight:500">📋 Firma ISG Detayı</div>
      <div class="isg-alt-tab" onclick="isgAltSekme('sure-hesap',this)" style="padding:10px 16px;font-size:13px;color:#666;cursor:pointer;border-bottom:2px solid transparent;white-space:nowrap;font-weight:500">⏱️ Süre Hesaplama</div>
      <div class="isg-alt-tab" onclick="isgAltSekme('personel-rapor',this)" style="padding:10px 16px;font-size:13px;color:#666;cursor:pointer;border-bottom:2px solid transparent;white-space:nowrap;font-weight:500">📊 Personel Raporu</div>
      <div class="isg-alt-tab" onclick="isgAltSekme('zorunlu-egitim',this)" style="padding:10px 16px;font-size:13px;color:#e85c2e;cursor:pointer;border-bottom:2px solid transparent;white-space:nowrap;font-weight:600">⚠️ Zorunlu Eğitimler</div>
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

    <!-- SÜRE HESAPLAMA -->
    <div id="isg-panel-sure-hesap" class="isg-alt-panel" style="display:none">
      <div style="font-family:Syne,sans-serif;font-weight:700;font-size:16px;margin-bottom:6px">⏱️ Zorunlu Eğitim & Uzman Süre Hesaplama</div>
      <div style="font-size:12px;color:var(--muted);margin-bottom:20px">6331 sayılı İSG Kanunu ve İSG Hizmetleri Yönetmeliği Ek-1'e göre otomatik hesaplama.</div>

      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:16px">
        <div>
          <div style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:6px">Çalışan Sayısı *</div>
          <input type="number" id="sh-calisan" class="form-input" placeholder="örn: 45" min="1" oninput="shHesapla()">
        </div>
        <div>
          <div style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:6px">Tehlike Sınıfı *</div>
          <select id="sh-tehlike" class="form-input" onchange="shHesapla()">
            <option value="">Seçin</option>
            <option value="Az Tehlikeli">🟢 Az Tehlikeli</option>
            <option value="Tehlikeli">🟡 Tehlikeli</option>
            <option value="Çok Tehlikeli">🔴 Çok Tehlikeli</option>
          </select>
        </div>
        <div>
          <div style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:6px">Atanmış Uzman Sınıfı</div>
          <select id="sh-uzman-sinif" class="form-input" onchange="shHesapla()">
            <option value="">Seçilmedi</option>
            <option value="A">A Sınıfı</option>
            <option value="B">B Sınıfı</option>
            <option value="C">C Sınıfı</option>
            <option value="—">Hekim / DSP</option>
          </select>
        </div>
      </div>

      <div id="sh-sonuc" style="display:none">
        <!-- Uzman sınıfı uyarısı -->
        <div id="sh-sinif-uyari" style="display:none;padding:12px 16px;border-radius:10px;font-size:13px;margin-bottom:12px"></div>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px">
          <!-- Zorunlu Eğitim Süresi -->
          <div style="background:var(--card);border:1px solid var(--border);border-radius:12px;padding:18px">
            <div style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:10px">📚 Zorunlu Eğitim Süresi / Yıl</div>
            <div style="display:flex;align-items:baseline;gap:8px;margin-bottom:4px">
              <span id="sh-toplam-saat" style="font-size:28px;font-weight:800;font-family:'Syne',sans-serif">—</span>
              <span style="font-size:14px;color:var(--muted)">saat</span>
            </div>
            <div id="sh-egitim-aciklama" style="font-size:12px;color:var(--muted)"></div>
            <div style="margin-top:10px;padding-top:10px;border-top:1px solid var(--border);font-size:12px;color:var(--muted)">
              Aylık: <strong id="sh-aylik-saat">—</strong> saat &nbsp;|&nbsp; Kişi başı: <strong id="sh-kisi-saat">—</strong> saat/yıl
            </div>
          </div>

          <!-- Uzman Çalışma Süresi -->
          <div style="background:var(--card);border:1px solid var(--border);border-radius:12px;padding:18px">
            <div style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:10px">🛡️ Uzman Zorunlu Çalışma Süresi</div>
            <div id="sh-tam-zamanli-badge" style="display:none;background:#fdecea;color:var(--red);border-radius:8px;padding:8px 12px;font-size:13px;font-weight:600;margin-bottom:8px">TAM ZAMANLI UZMAN ZORUNLU</div>
            <div style="display:flex;align-items:baseline;gap:8px;margin-bottom:4px">
              <span id="sh-uzman-dk" style="font-size:28px;font-weight:800;font-family:'Syne',sans-serif">—</span>
              <span id="sh-uzman-birim" style="font-size:14px;color:var(--muted)">dk/ay</span>
            </div>
            <div id="sh-uzman-aciklama" style="font-size:12px;color:var(--muted)"></div>
            <div id="sh-uzman-saat-row" style="margin-top:10px;padding-top:10px;border-top:1px solid var(--border);font-size:12px;color:var(--muted)">
              = <strong id="sh-uzman-saat">—</strong> saat/ay
            </div>
          </div>
        </div>

        <!-- Yasal Dayanak -->
        <div style="background:#e8f7f0;border:1px solid #b7e8d0;border-radius:10px;padding:12px 16px;font-size:12px;color:var(--green)">
          📋 <strong>Yasal Dayanak:</strong> 6331 sayılı İSG Kanunu Md.17 · İSG Hizmetleri Yönetmeliği Ek-1 ·
          İşyerlerinde İSG Eğitimlerinin Usul ve Esasları Hakkında Yönetmelik
        </div>

        <div style="margin-top:12px;text-align:right">
          <button class="btn btn-primary btn-sm" onclick="shKaydet()">Kaydet</button>
        </div>
      </div>

      <div id="sh-bos" style="padding:40px;text-align:center;color:var(--muted)">
        Çalışan sayısı ve tehlike sınıfını girin, süre otomatik hesaplanır.
      </div>
    </div>

    <!-- PERSONEL RAPORU -->
    <div id="isg-panel-personel-rapor" class="isg-alt-panel" style="display:none">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;margin-bottom:16px">
        <div>
          <div style="font-family:Syne,sans-serif;font-weight:700;font-size:16px">📊 Personel Eğitim Raporu</div>
          <div style="font-size:12px;color:var(--muted);margin-top:2px">Aylık bazda hangi çalışan hangi eğitimi kaç dakika/saat aldı</div>
        </div>
        <div style="display:flex;gap:8px;align-items:center">
          <select id="pr-yil" class="form-input" style="width:auto" onchange="prYukle()">
          </select>
          <button class="btn btn-dark btn-sm" onclick="prYukle()">Yenile</button>
        </div>
      </div>

      <div id="pr-yukleniyor" style="text-align:center;padding:40px;display:none">
        <div class="spinner" style="margin:0 auto 12px"></div>Yükleniyor...
      </div>

      <!-- Firma özeti bar chart -->
      <div id="pr-firma-ozet" style="display:none;margin-bottom:20px">
        <div style="font-size:12px;color:var(--muted);margin-bottom:8px;text-transform:uppercase;letter-spacing:1px">Aylık Toplam Eğitim (Tüm Firma)</div>
        <div id="pr-bar-chart" style="display:flex;gap:6px;align-items:flex-end;height:80px;padding-bottom:4px"></div>
        <div id="pr-bar-labels" style="display:flex;gap:6px;margin-top:4px"></div>
      </div>

      <!-- Personel tablosu -->
      <div id="pr-tablo-wrap" style="display:none">
        <div style="overflow-x:auto">
          <table id="pr-tablo" style="width:100%;border-collapse:collapse;font-size:13px">
            <thead id="pr-thead"></thead>
            <tbody id="pr-tbody"></tbody>
          </table>
        </div>
        <div style="font-size:11px;color:var(--muted);margin-top:8px">
          * Sadece geçilen/tamamlanan eğitimler sayılır. Süre, eğitim tanımındaki "süre" alanından alınır (varsayılan: 60 dk).
        </div>
      </div>

      <div id="pr-bos" style="padding:60px;text-align:center;color:var(--muted)">
        Rapor yüklenmedi.
      </div>
    </div>

    <!-- ZORUNLU EĞİTİMLER -->
    <div id="isg-panel-zorunlu-egitim" class="isg-alt-panel" style="display:none">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:10px;margin-bottom:16px">
        <div>
          <div style="font-family:Syne,sans-serif;font-weight:700;font-size:16px">⚠️ Zorunlu Eğitim Takibi</div>
          <div style="font-size:12px;color:var(--muted);margin-top:2px">6331 ve Yönetmelik Ek-1 kapsamında tüm çalışanların eğitim uyumu</div>
        </div>
        <button class="btn btn-dark btn-sm" onclick="zeYukle()">Yenile</button>
      </div>

      <!-- Özet kartlar -->
      <div id="ze-ozet" style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:20px"></div>

      <!-- Filtre -->
      <div style="display:flex;gap:8px;margin-bottom:14px;flex-wrap:wrap">
        <button class="btn btn-sm" id="ze-f-hepsi" onclick="zeFiltre('hepsi',this)" style="background:var(--accent);color:#fff;border-radius:8px;padding:5px 14px;font-size:12px;border:none;cursor:pointer">Tümü</button>
        <button class="btn btn-sm" id="ze-f-eksik" onclick="zeFiltre('eksik',this)" style="background:var(--bg);color:var(--muted);border-radius:8px;padding:5px 14px;font-size:12px;border:1px solid var(--border);cursor:pointer">Eksik Var</button>
        <button class="btn btn-sm" id="ze-f-hic" onclick="zeFiltre('hic',this)" style="background:var(--bg);color:var(--muted);border-radius:8px;padding:5px 14px;font-size:12px;border:1px solid var(--border);cursor:pointer">Hiç Almamış</button>
        <button class="btn btn-sm" id="ze-f-tamam" onclick="zeFiltre('tamam',this)" style="background:var(--bg);color:var(--muted);border-radius:8px;padding:5px 14px;font-size:12px;border:1px solid var(--border);cursor:pointer">Uyumlu</button>
        <div style="flex:1"></div>
        <button class="btn btn-primary btn-sm" onclick="zeTopluGonder()" id="ze-toplu-btn" style="display:none">📤 Seçililere Gönder</button>
      </div>

      <div id="ze-yukleniyor" style="text-align:center;padding:40px;display:none">
        <div class="spinner" style="margin:0 auto 12px"></div>Yükleniyor...
      </div>
      <div id="ze-liste"></div>
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


@isg_blueprint.route("/sure-hesap", methods=["POST"])
def sure_hesap():
    """
    Çalışan sayısı + tehlike sınıfı + uzman sınıfı → süre özeti.
    Body: {firma_id, calisan_sayisi, tehlike_sinifi, uzman_sinifi?}
    """
    k = _giris_kontrol()
    if k: return k
    veri = request.get_json()
    firma_id = veri.get("firma_id", "")
    try:
        calisan_sayisi = int(veri.get("calisan_sayisi", 0))
    except:
        return jsonify({"hata": "Geçersiz çalışan sayısı"}), 400
    tehlike_sinifi = veri.get("tehlike_sinifi", "")
    uzman_sinifi = veri.get("uzman_sinifi", "")
    if not tehlike_sinifi:
        return jsonify({"hata": "Tehlike sınıfı zorunlu"}), 400
    try:
        from isg.sure_hesap import firma_sure_ozeti, sure_kaydet
        ozet = firma_sure_ozeti(firma_id, tehlike_sinifi, calisan_sayisi, uzman_sinifi)
        # Sheets'e kaydet
        u = ozet["uzman"]
        sure_kaydet(firma_id, calisan_sayisi,
                    ozet["egitim"]["yillik_sure_saat"],
                    u.get("aylik_sure_dk"), u.get("tam_zamanli", False))
        return jsonify(ozet)
    except Exception as e:
        logger.error(f"Süre hesap hatası: {e}")
        return jsonify({"hata": str(e)}), 500


@isg_blueprint.route("/sure-hesap", methods=["GET"])
def sure_hesap_get():
    """Kaydedilmiş süre bilgisini döner."""
    k = _giris_kontrol()
    if k: return k
    firma_id = request.args.get("firma_id", "")
    if not firma_id:
        return jsonify({})
    try:
        from isg.sure_hesap import SEKME, BASLIKLAR
        from isg.sheets_base import tum_satirlar
        for s in tum_satirlar(SEKME):
            if s and s[0] == firma_id:
                while len(s) < len(BASLIKLAR):
                    s.append("")
                return jsonify(dict(zip(BASLIKLAR, s)))
        return jsonify({})
    except Exception as e:
        return jsonify({})


@isg_blueprint.route("/personel-rapor", methods=["GET"])
def personel_rapor():
    """
    Firmaya ait çalışanların aylık eğitim özeti.
    Query: firma_id, yil (opsiyonel, default=cari yıl)
    """
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
        # Kayıt almamış ama aktif çalışanları da ekle
        personel = firma_personel_listesi(firma_id)
        for p in personel:
            tid = p["telegram_id"]
            if tid not in ozet["calisanlar"]:
                ozet["calisanlar"][tid] = {
                    "ad_soyad": p["ad_soyad"],
                    "gorev": p["gorev"],
                    "aylar": {},
                    "yillik_toplam_dk": 0,
                    "yillik_toplam_saat": 0,
                    "egitim_sayisi": 0,
                }
        return jsonify(ozet)
    except Exception as e:
        logger.error(f"Personel rapor hatası: {e}")
        return jsonify({"hata": str(e)}), 500


@isg_blueprint.route("/zorunlu-egitimler", methods=["GET"])
def zorunlu_egitimler():
    """
    Firmadaki tüm çalışanların zorunlu eğitim durumu.
    Query: firma_id, tehlike_sinifi (opsiyonel — firma_detay'dan alınır)
    """
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

        from isg.zorunlu_egitim import (
            tehlike_icin_zorunlu_egitimler,
            calisan_eksik_egitimler,
            firma_ozet_istatistik
        )
        from isg.personel_rapor import firma_personel_listesi

        calisanlar = firma_personel_listesi(firma_id)
        zorunlu_liste = tehlike_icin_zorunlu_egitimler(tehlike)
        ozet = firma_ozet_istatistik(firma_id, tehlike)

        calisan_durumlar = []
        for c in calisanlar:
            tid = c.get("telegram_id", "")
            eksikler = calisan_eksik_egitimler(tid, firma_id, tehlike) if tid else zorunlu_liste
            calisan_durumlar.append({
                "telegram_id": tid,
                "ad_soyad":    c.get("ad_soyad", ""),
                "gorev":       c.get("gorev", ""),
                "egitimler":   eksikler,
                "eksik_sayisi": len([e for e in eksikler if e["durum"] in ("hic_alinmadi", "suresi_dolmus")]),
                "yaklasan_sayisi": len([e for e in eksikler if e["durum"] == "suresi_yaklashyor"]),
            })

        # Eksik olana göre sırala
        calisan_durumlar.sort(key=lambda x: x["eksik_sayisi"], reverse=True)

        return jsonify({
            "firma_id":     firma_id,
            "tehlike":      tehlike,
            "zorunlu_liste": zorunlu_liste,
            "calisanlar":   calisan_durumlar,
            "ozet":         ozet,
        })
    except Exception as e:
        logger.error(f"Zorunlu eğitim hatası: {e}")
        return jsonify({"hata": str(e)}), 500


@isg_blueprint.route("/zorunlu-egitim-gonder", methods=["POST"])
def zorunlu_egitim_gonder():
    """
    Belirli çalışana veya tüm eksik çalışanlara zorunlu eğitim gönder.
    Body: {firma_id, egitim_id?, telegram_idler: [], konu, tur}
    egitim_id varsa o eğitimi, yoksa konu+tur ile sistemdeki eğitimi bulur.
    """
    k = _giris_kontrol()
    if k: return k
    veri = request.get_json()
    firma_id      = veri.get("firma_id", "")
    egitim_id     = veri.get("egitim_id", "")
    konu          = veri.get("konu", "")
    telegram_idler = veri.get("telegram_idler", [])

    if not firma_id or not telegram_idler:
        return jsonify({"basarili": False, "hata": "firma_id ve en az bir telegram_id zorunlu"})

    try:
        import os, requests as req_lib, time
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        base  = f"https://api.telegram.org/bot{token}"

        # Eğitim mesajı
        if egitim_id:
            from egitimler_sheets import tum_egitimler
            egitimler = tum_egitimler()
            egitim = egitimler.get(egitim_id)
            mesaj_baslik = egitim["baslik"] if egitim else konu
        else:
            mesaj_baslik = konu or "Zorunlu İSG Eğitimi"

        keyboard = None
        if egitim_id:
            keyboard = {"inline_keyboard": [[{
                "text": "▶️ Eğitime Başla",
                "callback_data": f"egitim_baslat:{egitim_id}"
            }]]}
            # Ekstra hak ver
            try:
                from durum import ekstra_hak_ver, aktif_egitim_set
                aktif_egitim_set(egitim_id)
                for tid in telegram_idler:
                    try:
                        ekstra_hak_ver(int(tid))
                    except:
                        pass
            except:
                pass

        basarili = gonderilemeyen = 0
        for tid in telegram_idler:
            try:
                payload = {
                    "chat_id": int(tid),
                    "text": (
                        "🛡️ *Zorunlu İSG Eğitimi*\n\n"
                        f"*{mesaj_baslik}*\n\n"
                        "Bu eğitim, işyerinizde yasal zorunluluk kapsamındadır. "
                        "Lütfen tamamlayın."
                    ),
                    "parse_mode": "Markdown",
                }
                if keyboard:
                    payload["reply_markup"] = keyboard
                r = req_lib.post(f"{base}/sendMessage", json=payload, timeout=10)
                if r.json().get("ok"):
                    basarili += 1
                else:
                    gonderilemeyen += 1
                time.sleep(0.05)
            except:
                gonderilemeyen += 1

        return jsonify({
            "basarili": True,
            "gonderilen": basarili,
            "gonderilemeyen": gonderilemeyen,
        })
    except Exception as e:
        logger.error(f"Zorunlu eğitim gönderme hatası: {e}")
        return jsonify({"basarili": False, "hata": str(e)})


@isg_blueprint.route("/html", methods=["GET"])
def isg_html():
    """Panel'e gömülecek HTML bloğunu döner."""
    return ISG_SEKME_HTML, 200, {"Content-Type": "text/html"}
