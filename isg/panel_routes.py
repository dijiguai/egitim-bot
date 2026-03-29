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
<div class="tab-content" id="tab-isg">
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

<script>
// ── ISG Panel JavaScript ───────────────────────────────────────

function isgAltSekme(ad, el) {
  document.querySelectorAll('.isg-alt-panel').forEach(p => p.style.display = 'none');
  document.querySelectorAll('.isg-alt-tab').forEach(t => {
    t.classList.remove('active');
    t.style.borderBottomColor = 'transparent';
    t.style.color = '#666';
  });
  document.getElementById('isg-panel-' + ad).style.display = 'block';
  el.classList.add('active');
  el.style.color = 'var(--text)';
  el.style.borderBottomColor = 'var(--accent)';
  if (ad === 'uzmanlar') isgUzmanlariYukle();
  if (ad === 'atamalar') { isgAtamalariYukle(); isgFirmalariYukle('isg-atama-firma-filtre'); }
  if (ad === 'firma-detay') isgFirmalariYukle('isg-detay-firma-sec');
  if (ad === 'audit') isgAuditYukle();
}

// ── UZMANLAR ──────────────────────────────────────────────────

async function isgUzmanlariYukle() {
  const el = document.getElementById('isg-uzman-liste');
  el.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
  try {
    const r = await fetch('/panel/isg/uzmanlar');
    const uzmanlar = await r.json();
    if (!uzmanlar.length) {
      el.innerHTML = '<div class="empty"><div class="empty-icon">👤</div>Henüz uzman eklenmemiş.</div>';
      return;
    }
    el.innerHTML = uzmanlar.map(u => {
      const sinifBadge = u.sinif === 'A' ? 'isg-badge-a' : u.sinif === 'B' ? 'isg-badge-b' : u.sinif === 'C' ? 'isg-badge-c' : 'isg-badge-h';
      const unvanEtiket = {
        'is_guvenligi_uzmani': 'İş Güvenliği Uzmanı',
        'isyeri_hekimi': 'İşyeri Hekimi',
        'diger_saglik': 'Diğer Sağlık Personeli',
        'usta_ogretici': 'Usta Öğretici',
        'isveren': 'İşveren / Vekili'
      }[u.unvan] || u.unvan;
      return `<div class="isg-kart">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px">
          <div>
            <div style="font-weight:700;font-size:15px">${u.ad_soyad}</div>
            <div style="font-size:13px;color:var(--muted);margin-top:2px">${unvanEtiket}</div>
            <div style="margin-top:6px;display:flex;gap:6px;flex-wrap:wrap">
              ${u.sinif && u.sinif !== '—' ? `<span class="isg-badge ${sinifBadge}">${u.sinif} Sınıfı</span>` : ''}
              ${u.sertifika_no ? `<span class="isg-badge" style="background:var(--bg);color:var(--muted)">Sert: ${u.sertifika_no}</span>` : ''}
              ${u.diploma_no ? `<span class="isg-badge" style="background:var(--bg);color:var(--muted)">Dipl: ${u.diploma_no}</span>` : ''}
            </div>
            <div style="font-size:11px;color:var(--muted);margin-top:6px">Kayıt: ${u.kayit_tarihi}</div>
          </div>
          <div style="display:flex;gap:6px">
            <button class="btn btn-dark btn-sm" onclick="isgUzmanDuzenle('${u.uzman_id}')">✏️</button>
            <button class="btn btn-green btn-sm" onclick="isgAtamaModalAcUzman('${u.uzman_id}')">🏭 Ata</button>
            <button class="btn btn-red btn-sm" onclick="isgUzmanPasif('${u.uzman_id}','${u.ad_soyad}')">Pasife Al</button>
          </div>
        </div>
      </div>`;
    }).join('');
  } catch(e) {
    el.innerHTML = '<div class="empty"><div class="empty-icon">⚠️</div>Yüklenemedi: ' + e.message + '</div>';
  }
}

function isgUzmanModalAc() {
  document.getElementById('isg-uzman-id').value = '';
  document.getElementById('isg-u-ad').value = '';
  document.getElementById('isg-u-unvan').value = '';
  document.getElementById('isg-u-sinif').value = '—';
  document.getElementById('isg-u-sertifika').value = '';
  document.getElementById('isg-u-diploma').value = '';
  document.getElementById('isg-uzman-hata').style.display = 'none';
  document.getElementById('isg-uzman-modal-baslik').textContent = 'Uzman / Hekim Ekle';
  document.getElementById('isg-uzman-modal').classList.add('open');
}

async function isgUzmanDuzenle(uzmanId) {
  try {
    const r = await fetch('/panel/isg/uzmanlar/' + uzmanId);
    const u = await r.json();
    document.getElementById('isg-uzman-id').value = u.uzman_id;
    document.getElementById('isg-u-ad').value = u.ad_soyad;
    document.getElementById('isg-u-unvan').value = u.unvan;
    document.getElementById('isg-u-sinif').value = u.sinif || '—';
    document.getElementById('isg-u-sertifika').value = u.sertifika_no;
    document.getElementById('isg-u-diploma').value = u.diploma_no;
    document.getElementById('isg-uzman-hata').style.display = 'none';
    document.getElementById('isg-uzman-modal-baslik').textContent = 'Uzmanı Düzenle';
    document.getElementById('isg-uzman-modal').classList.add('open');
  } catch(e) { alert('Yüklenemedi: ' + e.message); }
}

function isgUnvanDegisti() {
  const unvan = document.getElementById('isg-u-unvan').value;
  const sinifGrup = document.getElementById('isg-sinif-grup');
  sinifGrup.style.display = (unvan === 'is_guvenligi_uzmani') ? 'block' : 'none';
  if (unvan !== 'is_guvenligi_uzmani') {
    document.getElementById('isg-u-sinif').value = '—';
  }
}

async function isgUzmanKaydet() {
  const uzmanId = document.getElementById('isg-uzman-id').value;
  const hataEl = document.getElementById('isg-uzman-hata');
  const veri = {
    ad_soyad: document.getElementById('isg-u-ad').value.trim(),
    unvan: document.getElementById('isg-u-unvan').value,
    sinif: document.getElementById('isg-u-sinif').value,
    sertifika_no: document.getElementById('isg-u-sertifika').value.trim(),
    diploma_no: document.getElementById('isg-u-diploma').value.trim(),
  };
  if (!veri.ad_soyad || !veri.unvan || !veri.sertifika_no) {
    hataEl.textContent = 'Ad, unvan ve sertifika no zorunludur.';
    hataEl.style.display = 'block'; return;
  }
  try {
    const url = uzmanId ? `/panel/isg/uzmanlar/${uzmanId}` : '/panel/isg/uzmanlar';
    const method = uzmanId ? 'PUT' : 'POST';
    const r = await fetch(url, { method, headers: {'Content-Type':'application/json'}, body: JSON.stringify(veri) });
    const d = await r.json();
    if (d.basarili) { modalKapat('isg-uzman-modal'); isgUzmanlariYukle(); }
    else { hataEl.textContent = d.hata || 'Hata'; hataEl.style.display = 'block'; }
  } catch(e) { hataEl.textContent = 'Bağlantı hatası'; hataEl.style.display = 'block'; }
}

async function isgUzmanPasif(uzmanId, ad) {
  if (!confirm(`"${ad}" pasife alınacak. Geçmiş kayıtlar korunur. Devam?`)) return;
  const r = await fetch(`/panel/isg/uzmanlar/${uzmanId}/pasif`, { method: 'POST' });
  const d = await r.json();
  if (d.basarili) isgUzmanlariYukle();
  else alert('Hata: ' + (d.hata || ''));
}

// ── ATAMALAR ──────────────────────────────────────────────────

async function isgFirmalariYukle(selectId) {
  const sel = document.getElementById(selectId);
  if (!sel) return;
  try {
    const r = await fetch('/panel/api/firmalar-detay');
    const firmalar = await r.json();
    const oplar = firmalar.map(f => `<option value="${f.firma_id}">${f.ad}</option>`).join('');
    sel.innerHTML = (sel.options[0]?.value === '' ? '<option value="">Tüm Firmalar</option>' : '') + oplar;
  } catch(e) {}
}

async function isgAtamalariYukle() {
  const el = document.getElementById('isg-atama-liste');
  const firmaId = document.getElementById('isg-atama-firma-filtre')?.value || '';
  el.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
  try {
    const r = await fetch('/panel/isg/atamalar?firma_id=' + firmaId);
    const atamalar = await r.json();
    if (!atamalar.length) {
      el.innerHTML = '<div class="empty"><div class="empty-icon">🏭</div>Atama bulunamadı.</div>';
      return;
    }
    const tipEtiket = { 'is_guvenligi_uzmani': 'İSG Uzmanı', 'isyeri_hekimi': 'İşyeri Hekimi', 'diger_saglik': 'Diğer Sağlık' };
    el.innerHTML = atamalar.map(a => `
      <div class="isg-kart" style="opacity:${a.aktif==='1'?1:0.6}">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px">
          <div>
            <div style="font-weight:700;font-size:14px">${a.uzman_ad_soyad || a.uzman_id}</div>
            <div style="font-size:12px;color:var(--muted)">${tipEtiket[a.unvan_tipi]||a.unvan_tipi} · ${a.firma_ad||a.firma_id}</div>
            <div style="font-size:12px;margin-top:4px">
              📅 <b>${a.baslangic_tarihi}</b>
              ${a.bitis_tarihi ? ` → <b>${a.bitis_tarihi}</b>` : ' → <span style="color:var(--green)">Devam ediyor</span>'}
            </div>
          </div>
          ${a.aktif==='1' ? `<button class="btn btn-red btn-sm" onclick="isgAyrilmaModalAc('${a.atama_id}','${a.uzman_ad_soyad||a.uzman_id}','${a.firma_ad||a.firma_id}')">Sonlandır</button>` : '<span style="font-size:11px;color:var(--muted)">Sona erdi</span>'}
        </div>
      </div>`).join('');
  } catch(e) {
    el.innerHTML = '<div class="empty"><div class="empty-icon">⚠️</div>Yüklenemedi</div>';
  }
}

async function isgAtamaModalAc() {
  await _isgAtamaModalDoldur(null);
  document.getElementById('isg-atama-modal').classList.add('open');
}

async function isgAtamaModalAcUzman(uzmanId) {
  await _isgAtamaModalDoldur(uzmanId);
  document.getElementById('isg-atama-modal').classList.add('open');
}

async function _isgAtamaModalDoldur(seciliUzmanId) {
  try {
    const r = await fetch('/panel/isg/uzmanlar');
    const uzmanlar = await r.json();
    document.getElementById('isg-atama-uzman').innerHTML =
      uzmanlar.map(u => `<option value="${u.uzman_id}" ${u.uzman_id===seciliUzmanId?'selected':''}>${u.ad_soyad} (${u.sinif||'—'})</option>`).join('');
  } catch(e) {}
  await isgFirmalariYukle('isg-atama-firma');
  document.getElementById('isg-atama-bas').value = '';
  document.getElementById('isg-atama-hata').style.display = 'none';
}

async function isgAtamaKaydet() {
  const hataEl = document.getElementById('isg-atama-hata');
  const veri = {
    uzman_id: document.getElementById('isg-atama-uzman').value,
    firma_id: document.getElementById('isg-atama-firma').value,
    unvan_tipi: document.getElementById('isg-atama-tip').value,
    baslangic_tarihi: document.getElementById('isg-atama-bas').value.trim(),
  };
  if (!veri.uzman_id || !veri.firma_id || !veri.baslangic_tarihi) {
    hataEl.textContent = 'Tüm alanları doldurun.';
    hataEl.style.display = 'block'; return;
  }
  try {
    const r = await fetch('/panel/isg/atamalar', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(veri) });
    const d = await r.json();
    if (d.basarili) { modalKapat('isg-atama-modal'); isgAtamalariYukle(); }
    else { hataEl.textContent = d.hata || 'Hata'; hataEl.style.display = 'block'; }
  } catch(e) { hataEl.textContent = 'Bağlantı hatası'; hataEl.style.display = 'block'; }
}

function isgAyrilmaModalAc(atamaId, uzmanAd, firmaAd) {
  document.getElementById('isg-ayrilma-atama-id').value = atamaId;
  document.getElementById('isg-ayrilma-ozet').textContent = `${uzmanAd} · ${firmaAd}`;
  document.getElementById('isg-ayrilma-tarih').value = '';
  document.getElementById('isg-ayrilma-modal').classList.add('open');
}

async function isgAyrılmaKaydet() {
  const atamaId = document.getElementById('isg-ayrilma-atama-id').value;
  const bitis = document.getElementById('isg-ayrilma-tarih').value.trim();
  if (!bitis) { alert('Ayrılış tarihi zorunludur.'); return; }
  const r = await fetch(`/panel/isg/atamalar/${atamaId}/bitir`, {
    method: 'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({bitis_tarihi: bitis})
  });
  const d = await r.json();
  if (d.basarili) { modalKapat('isg-ayrilma-modal'); isgAtamalariYukle(); }
  else alert('Hata: ' + (d.hata || ''));
}

// ── FİRMA ISG DETAY ───────────────────────────────────────────

async function isgFirmaDetayYukle() {
  const firmaId = document.getElementById('isg-detay-firma-sec').value;
  const form = document.getElementById('isg-firma-detay-form');
  const ozet = document.getElementById('isg-firma-detay-ozet');
  if (!firmaId) { form.style.display = 'none'; ozet.innerHTML = ''; return; }
  form.style.display = 'block';
  try {
    const r = await fetch('/panel/isg/firma-detay?firma_id=' + firmaId);
    const d = await r.json();
    document.getElementById('isg-sgk-no').value = d.sgk_sicil_no || '';
    document.getElementById('isg-nace-kodu').value = d.nace_kodu || '';
    document.getElementById('isg-tehlike-sinifi').value = d.tehlike_sinifi || '';
    document.getElementById('isg-calisan-sayisi').value = d.calisan_sayisi || '';
    document.getElementById('isg-nace-tahmin-uyari').style.display = 'none';
    // Atama özeti
    const r2 = await fetch('/panel/isg/atamalar?firma_id=' + firmaId);
    const atamalar = await r2.json();
    const aktifler = atamalar.filter(a => a.aktif === '1');
    ozet.innerHTML = aktifler.length ? `
      <div style="margin-top:8px;font-size:12px;color:var(--muted)">Aktif görevlendirmeler:</div>
      ${aktifler.map(a => `<div style="font-size:13px;margin-top:4px">• ${a.uzman_ad_soyad||a.uzman_id} (${a.unvan_tipi==='is_guvenligi_uzmani'?'İSG Uzmanı':'İşyeri Hekimi'}) — ${a.baslangic_tarihi}'dan itibaren</div>`).join('')}` : '';
  } catch(e) {}
}

async function isgSgkDenNace() {
  const sgk = document.getElementById('isg-sgk-no').value.trim();
  if (!sgk) return;
  try {
    const r = await fetch('/panel/isg/sgk-nace?sgk=' + encodeURIComponent(sgk));
    const d = await r.json();
    if (d.nace_kodu) {
      document.getElementById('isg-nace-kodu').value = d.nace_kodu;
      const uyari = document.getElementById('isg-nace-tahmin-uyari');
      uyari.style.display = 'block';
      uyari.innerHTML = `NACE tahmini: <b>${d.nace_kodu}</b> · Tehlike sınıfı tahmini: <b>${d.tehlike_sinifi||'Bilinmiyor'}</b> · Lütfen onaylayın.`;
      if (d.tehlike_sinifi) document.getElementById('isg-tehlike-sinifi').value = d.tehlike_sinifi;
    }
  } catch(e) {}
}

async function isgFirmaDetayKaydet() {
  const firmaId = document.getElementById('isg-detay-firma-sec').value;
  const veri = {
    firma_id: firmaId,
    sgk_sicil_no: document.getElementById('isg-sgk-no').value.trim(),
    nace_kodu: document.getElementById('isg-nace-kodu').value.trim(),
    tehlike_sinifi: document.getElementById('isg-tehlike-sinifi').value,
    calisan_sayisi: document.getElementById('isg-calisan-sayisi').value.trim(),
  };
  const r = await fetch('/panel/isg/firma-detay', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(veri) });
  const d = await r.json();
  if (d.basarili) alert('✅ Kaydedildi!');
  else alert('Hata: ' + (d.hata || ''));
}

// ── DENETİM KAYDI ─────────────────────────────────────────────

async function isgAuditYukle() {
  const el = document.getElementById('isg-audit-liste');
  el.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
  try {
    const r = await fetch('/panel/isg/audit');
    const kayitlar = await r.json();
    if (!kayitlar.length) {
      el.innerHTML = '<div class="empty"><div class="empty-icon">📜</div>Henüz kayıt yok.</div>';
      return;
    }
    const islemRenk = { 'EKLE':'var(--green)', 'GUNCELLE':'var(--accent2)', 'PASIF_YAP':'var(--muted)', 'ATAMA':'var(--accent)', 'AYRILMA':'var(--red)' };
    el.innerHTML = `<div class="table-wrap"><table><thead><tr><th>Zaman</th><th>İşlem</th><th>Tablo</th><th>Özet</th><th>Yapan</th></tr></thead><tbody>` +
      kayitlar.map(k => `<tr>
        <td style="font-size:12px;color:var(--muted)">${k.zaman}</td>
        <td><span style="font-weight:600;font-size:12px;color:${islemRenk[k.islem]||'var(--text)'}">${k.islem}</span></td>
        <td style="font-size:12px">${k.tablo}</td>
        <td style="font-size:13px">${k.ozet}</td>
        <td style="font-size:12px;color:var(--muted)">${k.yapan_ad}</td>
      </tr>`).join('') + '</tbody></table></div>';
  } catch(e) {
    el.innerHTML = '<div class="empty"><div class="empty-icon">⚠️</div>Yüklenemedi</div>';
  }
}
</script>
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
