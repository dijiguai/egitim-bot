"""
Yönetici Paneli — Flask web uygulaması
"""

from flask import Flask, render_template_string, jsonify, request, session, redirect
from datetime import date
import os, json, re
from sheets import tum_kayitlar_getir
from config import EGITIMLER, GECME_NOTU
from calisanlar import tum_calisanlar, calisan_ekle, calisan_guncelle, calisan_sil
from durum import izin_ekle, izin_kaldir, izinli_mi, eksik_egitimler

app = Flask(__name__)
app.secret_key = os.environ.get("PANEL_SECRET_KEY", "egitimbot2026")
PANEL_SIFRE = os.environ.get("PANEL_SIFRE", "admin123")

HTML = r"""
<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Eğitim Yönetici Paneli</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#f5f3ef;--card:#fff;--dark:#1a1a18;--accent:#e85c2e;--accent2:#2e7de8;--green:#27a86e;--red:#e83a2e;--yellow:#e8b82e;--border:#e2ddd6;--muted:#8c8780;--text:#2a2a28}
body{background:var(--bg);color:var(--text);font-family:'DM Sans',sans-serif;min-height:100vh}
.login-wrap{min-height:100vh;display:flex;align-items:center;justify-content:center;background:var(--dark)}
.login-box{background:#242420;border:1px solid #333;border-radius:16px;padding:40px;width:340px}
.login-title{font-family:'Syne',sans-serif;font-size:22px;font-weight:800;color:#fff;margin-bottom:6px}
.login-sub{font-size:13px;color:#666;margin-bottom:28px}
.login-box input{width:100%;background:#1a1a18;border:1px solid #333;border-radius:10px;padding:12px 16px;color:#fff;font-size:14px;margin-bottom:12px;outline:none;font-family:'DM Sans',sans-serif}
.login-box input:focus{border-color:var(--accent)}
.login-btn{width:100%;background:var(--accent);color:#fff;border:none;border-radius:10px;padding:13px;font-size:14px;font-weight:600;cursor:pointer;font-family:'Syne',sans-serif}
.login-err{color:var(--red);font-size:12px;margin-top:8px;text-align:center}
.header{background:var(--dark);padding:0 24px;height:56px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100}
.header-logo{font-family:'Syne',sans-serif;font-weight:800;font-size:16px;color:#fff;display:flex;align-items:center;gap:10px}
.logo-dot{width:8px;height:8px;background:var(--accent);border-radius:50%;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.5;transform:scale(1.3)}}
.logout-btn{background:#333;color:#aaa;border:none;border-radius:8px;padding:6px 14px;font-size:12px;cursor:pointer}
.tabs{background:var(--dark);display:flex;gap:4px;padding:0 24px;border-bottom:1px solid #333;overflow-x:auto}
.tab{padding:12px 16px;font-size:13px;color:#666;cursor:pointer;border-bottom:2px solid transparent;transition:all .15s;font-weight:500;white-space:nowrap}
.tab:hover{color:#aaa}.tab.active{color:#fff;border-bottom-color:var(--accent)}
.main{padding:24px;max-width:1100px;margin:0 auto}
.tab-content{display:none}.tab-content.active{display:block}
.filters{display:flex;gap:10px;margin-bottom:24px;flex-wrap:wrap;align-items:flex-end}
.filter-group{display:flex;flex-direction:column;gap:4px}
.filter-label{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:1px}
select,input[type=date],input[type=text],input[type=password]{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:8px 12px;font-size:13px;color:var(--text);outline:none;font-family:'DM Sans',sans-serif}
select:focus,input:focus{border-color:var(--accent)}
.btn{border:none;border-radius:8px;padding:9px 20px;font-size:13px;font-weight:600;cursor:pointer;font-family:'Syne',sans-serif;transition:all .15s}
.btn-primary{background:var(--accent);color:#fff}.btn-primary:hover{background:#d44f24}
.btn-dark{background:#333;color:#fff}.btn-dark:hover{background:#444}
.btn-green{background:var(--green);color:#fff}
.btn-red{background:var(--red);color:#fff}
.btn-ai{background:linear-gradient(135deg,#2e7de8,#7c3aed);color:#fff}
.btn-sm{padding:5px 12px;font-size:12px}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:24px}
@media(max-width:640px){.stats{grid-template-columns:repeat(2,1fr)}}
.stat{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:20px;position:relative;overflow:hidden}
.stat::after{content:'';position:absolute;bottom:0;left:0;right:0;height:3px;background:var(--accent)}
.stat.green::after{background:var(--green)}.stat.red::after{background:var(--red)}.stat.blue::after{background:var(--accent2)}
.stat-label{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:10px}
.stat-val{font-family:'Syne',sans-serif;font-size:36px;font-weight:800;line-height:1}
.stat-val.green{color:var(--green)}.stat-val.red{color:var(--red)}.stat-val.blue{color:var(--accent2)}.stat-val.orange{color:var(--accent)}
.stat-sub{font-size:12px;color:var(--muted);margin-top:6px}
.section-title{font-family:'Syne',sans-serif;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;color:var(--muted);margin-bottom:14px;margin-top:28px}
.table-wrap{background:var(--card);border:1px solid var(--border);border-radius:14px;overflow:hidden;overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:13px;min-width:500px}
th{background:#f9f7f4;padding:11px 16px;text-align:left;font-size:10px;text-transform:uppercase;letter-spacing:1px;color:var(--muted);font-weight:600;border-bottom:1px solid var(--border);white-space:nowrap}
td{padding:11px 16px;border-bottom:1px solid var(--border);color:var(--text)}
tr:last-child td{border-bottom:none}tr:hover td{background:#faf8f5}
.pill{display:inline-block;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600}
.pill-gecti{background:#e8f7f0;color:var(--green)}.pill-kaldi{background:#fdecea;color:var(--red)}
.pill-izin{background:#fff8e6;color:var(--yellow)}.pill-aktif{background:#e8f7f0;color:var(--green)}
.puan-y{color:var(--green);font-weight:700}.puan-d{color:var(--red);font-weight:700}
/* CALISAN KARTI */
.calisan-kart{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:20px;margin-bottom:12px}
.calisan-kart-header{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;flex-wrap:wrap}
.calisan-ad{font-family:'Syne',sans-serif;font-weight:700;font-size:16px}
.calisan-gorev{font-size:12px;color:var(--muted);margin-top:2px}
.calisan-id{font-size:11px;color:var(--muted);margin-top:4px;font-family:monospace;background:#f5f3ef;padding:2px 8px;border-radius:4px;display:inline-block}
.calisan-aksiyonlar{display:flex;gap:8px;flex-wrap:wrap}
.calisan-ilerleme{margin-top:14px;padding-top:14px;border-top:1px solid var(--border)}
.ilerleme-bar{background:#f0ede8;border-radius:4px;height:8px;overflow:hidden;margin-top:6px}
.ilerleme-dolu{height:100%;border-radius:4px;background:var(--green);transition:width .5s}
/* EGITIM KARTI */
.egitim-kart{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:20px;margin-bottom:12px}
.egitim-kart-header{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;margin-bottom:10px;flex-wrap:wrap}
.egitim-kart-baslik{font-family:'Syne',sans-serif;font-weight:700;font-size:16px}
.egitim-tur{display:inline-block;background:#f0ede8;border-radius:20px;padding:3px 10px;font-size:11px;color:var(--muted);font-weight:600}
.egitim-kart-body{font-size:13px;color:var(--muted);line-height:1.5;margin-bottom:12px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.egitim-kart-footer{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px}
.egitim-kod{font-size:11px;color:var(--muted);background:#f5f3ef;padding:4px 10px;border-radius:6px;font-family:monospace}
.eg-satir{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:16px 20px;margin-bottom:10px;display:flex;align-items:center;gap:16px;flex-wrap:wrap}
.eg-baslik{font-weight:600;font-size:14px;flex:1;min-width:180px}
.eg-meta{font-size:12px;color:var(--muted)}
.bar-wrap{flex:1;min-width:100px;background:#f0ede8;border-radius:4px;height:8px;overflow:hidden}
.bar-fill{height:100%;border-radius:4px;background:var(--green);transition:width .5s}
.bar-fill.dusuk{background:var(--red)}.bar-fill.orta{background:var(--yellow)}
.bar-pct{font-family:'Syne',sans-serif;font-size:14px;font-weight:700;min-width:45px;text-align:right}
/* MODAL */
.modal-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:1000;align-items:center;justify-content:center;padding:16px}
.modal-overlay.open{display:flex}
.modal{background:var(--card);border-radius:20px;padding:32px;width:100%;max-width:480px;max-height:90vh;overflow-y:auto}
.modal-title{font-family:'Syne',sans-serif;font-size:20px;font-weight:800;margin-bottom:6px}
.modal-sub{font-size:13px;color:var(--muted);margin-bottom:24px}
.form-group{margin-bottom:16px}
.form-label{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;display:block}
.form-input{width:100%;background:var(--bg);border:1px solid var(--border);border-radius:10px;padding:10px 14px;font-size:14px;color:var(--text);outline:none;font-family:'DM Sans',sans-serif}
.form-input:focus{border-color:var(--accent)}
textarea.form-input{min-height:80px;resize:vertical}
.modal-footer{display:flex;gap:10px;margin-top:24px}
.ai-progress{display:none;text-align:center;padding:20px}
.ai-spinner{width:40px;height:40px;border:3px solid var(--border);border-top-color:var(--accent2);border-radius:50%;animation:spin .8s linear infinite;margin:0 auto 12px}
@keyframes spin{to{transform:rotate(360deg)}}
.ai-status{font-size:13px;color:var(--muted)}
.ai-success{display:none;text-align:center;padding:20px}
.success-icon{font-size:48px;margin-bottom:12px}
.success-text{font-size:15px;font-weight:600;margin-bottom:6px}
.success-sub{font-size:13px;color:var(--muted)}
.loading{text-align:center;padding:60px;color:var(--muted);font-size:14px}
.spinner{width:32px;height:32px;border:3px solid var(--border);border-top-color:var(--accent);border-radius:50%;animation:spin .8s linear infinite;margin:0 auto 16px}
.empty{text-align:center;padding:48px;color:var(--muted)}
.empty-icon{font-size:40px;margin-bottom:12px}
.alert{padding:12px 16px;border-radius:10px;font-size:13px;margin-bottom:16px}
.alert-green{background:#e8f7f0;color:var(--green);border:1px solid #b7e8d0}
.alert-red{background:#fdecea;color:var(--red);border:1px solid #f5bcb8}
@media(max-width:480px){.main{padding:16px}.header{padding:0 16px}.tabs{padding:0 16px}}
</style>
</head>
<body>

{% if not logged_in %}
<div class="login-wrap">
  <div class="login-box">
    <div class="login-title">Yönetici Girişi</div>
    <div class="login-sub">İş Başı Eğitim Paneli</div>
    <form method="POST" action="/panel/login">
      <div style="position:relative">
        <input type="password" name="sifre" id="si" placeholder="Şifre" autofocus style="padding-right:44px">
        <button type="button" onclick="var i=document.getElementById('si');i.type=i.type==='password'?'text':'password'" style="position:absolute;right:12px;top:14px;background:none;border:none;cursor:pointer;color:#666;font-size:18px">👁</button>
      </div>
      {% if hata %}<div class="login-err">⚠️ Yanlış şifre</div>{% endif %}
      <button class="login-btn" type="submit" style="margin-top:4px">Giriş Yap</button>
    </form>
  </div>
</div>

{% else %}
<div class="header">
  <div class="header-logo"><div class="logo-dot"></div>Eğitim Paneli</div>
  <a href="/panel/cikis"><button class="logout-btn">Çıkış</button></a>
</div>
<div class="tabs">
  <div class="tab active" onclick="sekme('kayitlar',this)">📊 Kayıtlar</div>
  <div class="tab" onclick="sekme('calisanlar',this)">👥 Çalışanlar</div>
  <div class="tab" onclick="sekme('istatistik',this)">📈 İstatistik</div>
  <div class="tab" onclick="sekme('egitimler',this)">📚 Eğitimler</div>
</div>

<div class="main">

  <!-- FİLTRELER -->
  <div id="filtre-bar" class="filters">
    <div class="filter-group"><span class="filter-label">Başlangıç</span><input type="date" id="tarih-bas"></div>
    <div class="filter-group"><span class="filter-label">Bitiş</span><input type="date" id="tarih-bitis"></div>
    <div class="filter-group"><span class="filter-label">Durum</span>
      <select id="durum-f"><option value="">Tümü</option><option value="GEÇTİ">Geçti</option><option value="KALDI">Kaldı</option></select>
    </div>
    <button class="btn btn-primary" onclick="verileriYukle()">Filtrele</button>
    <button class="btn btn-dark" onclick="bugunSec()">Bugün</button>
  </div>

  <!-- KAYITLAR -->
  <div class="tab-content active" id="tab-kayitlar">
    <div class="stats">
      <div class="stat orange"><div class="stat-label">Toplam</div><div class="stat-val orange" id="st-t">—</div><div class="stat-sub">Kayıt</div></div>
      <div class="stat green"><div class="stat-label">Geçti</div><div class="stat-val green" id="st-g">—</div><div class="stat-sub" id="st-o">—</div></div>
      <div class="stat red"><div class="stat-label">Kaldı</div><div class="stat-val red" id="st-k">—</div><div class="stat-sub">Yeniden eğitim</div></div>
      <div class="stat blue"><div class="stat-label">Ort. Puan</div><div class="stat-val blue" id="st-p">—</div><div class="stat-sub">100 üzerinden</div></div>
    </div>
    <div class="section-title">Eğitim Kayıtları</div>
    <div class="table-wrap">
      <table>
        <thead><tr><th>Tarih</th><th>Saat</th><th>Çalışan</th><th>Görev</th><th>Eğitim</th><th>Puan</th><th>Durum</th><th>Kimlik</th></tr></thead>
        <tbody id="kayit-tb"><tr><td colspan="8"><div class="loading"><div class="spinner"></div>Yükleniyor...</div></td></tr></tbody>
      </table>
    </div>
  </div>

  <!-- ÇALIŞANLAR -->
  <div class="tab-content" id="tab-calisanlar">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;flex-wrap:wrap;gap:12px">
      <div class="section-title" style="margin:0">Çalışan Listesi</div>
      <button class="btn btn-primary" onclick="calisanModalAc()">+ Çalışan Ekle</button>
    </div>
    <div id="calisan-liste"><div class="loading"><div class="spinner"></div></div></div>
  </div>

  <!-- İSTATİSTİK -->
  <div class="tab-content" id="tab-istatistik">
    <div class="section-title">Eğitim Bazında Başarı Oranı</div>
    <div id="egitim-stats"><div class="loading"><div class="spinner"></div></div></div>
  </div>

  <!-- EĞİTİMLER -->
  <div class="tab-content" id="tab-egitimler">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;flex-wrap:wrap;gap:12px">
      <div>
        <div class="section-title" style="margin:0">Mevcut Eğitimler</div>
        <div style="font-size:12px;color:var(--muted);margin-top:4px">Telegram'da: <code style="background:#f0ede8;padding:2px 6px;border-radius:4px">/egitim_gonder [kod]</code></div>
      </div>
      <button class="btn btn-ai" onclick="aiModalAc()">✨ Yapay Zeka ile Üret</button>
    </div>
    <div id="egitim-liste"><div class="loading"><div class="spinner"></div></div></div>
  </div>

</div>

<!-- ÇALIŞAN EKLE/DÜZENLE MODAL -->
<div class="modal-overlay" id="calisan-modal">
  <div class="modal">
    <div class="modal-title" id="calisan-modal-baslik">Çalışan Ekle</div>
    <div class="modal-sub">Telegram ID'yi öğrenmek için çalışan @userinfobot'a /start yazsın.</div>
    <input type="hidden" id="calisan-edit-id">
    <div class="form-group">
      <label class="form-label">Telegram ID *</label>
      <input type="text" class="form-input" id="c-tid" placeholder="örn: 123456789">
    </div>
    <div class="form-group">
      <label class="form-label">Ad Soyad *</label>
      <input type="text" class="form-input" id="c-ad" placeholder="Ahmet Yılmaz">
    </div>
    <div class="form-group">
      <label class="form-label">Görev *</label>
      <input type="text" class="form-input" id="c-gorev" placeholder="Operatör, Tekniker, vb.">
    </div>
    <div class="form-group">
      <label class="form-label">Doğum Tarihi * (GG.AA.YYYY)</label>
      <input type="text" class="form-input" id="c-dogum" placeholder="15.06.1990">
    </div>
    <div id="calisan-hata" class="alert alert-red" style="display:none"></div>
    <div class="modal-footer">
      <button class="btn btn-primary" style="flex:1" onclick="calisanKaydet()">Kaydet</button>
      <button class="btn btn-dark" onclick="modalKapat('calisan-modal')">İptal</button>
    </div>
  </div>
</div>

<!-- İZİN MODAL -->
<div class="modal-overlay" id="izin-modal">
  <div class="modal">
    <div class="modal-title">İzin Ekle</div>
    <div class="modal-sub" id="izin-calisan-adi"></div>
    <input type="hidden" id="izin-tid">
    <div class="form-group">
      <label class="form-label">İzin Tarihleri</label>
      <input type="date" class="form-input" id="izin-tarih1" style="margin-bottom:8px">
      <input type="date" class="form-input" id="izin-tarih2" style="margin-bottom:8px">
      <input type="date" class="form-input" id="izin-tarih3">
      <div style="font-size:11px;color:var(--muted);margin-top:6px">Birden fazla gün için birden fazla tarih girin.</div>
    </div>
    <div class="modal-footer">
      <button class="btn btn-primary" style="flex:1" onclick="izinKaydet()">İzin Ekle</button>
      <button class="btn btn-dark" onclick="modalKapat('izin-modal')">İptal</button>
    </div>
  </div>
</div>

<!-- SİL ONAY MODAL -->
<div class="modal-overlay" id="sil-modal">
  <div class="modal" style="max-width:380px">
    <div class="modal-title">Çalışanı Sil</div>
    <div class="modal-sub" id="sil-adi-text"></div>
    <p style="font-size:14px;margin-bottom:20px">Bu çalışan sistemden kalıcı olarak silinecek. Eğitim kayıtları korunacak.</p>
    <input type="hidden" id="sil-tid">
    <div class="modal-footer">
      <button class="btn btn-red" style="flex:1" onclick="calisanSilOnayla()">Sil</button>
      <button class="btn btn-dark" onclick="modalKapat('sil-modal')">İptal</button>
    </div>
  </div>
</div>

<!-- AI MODAL -->
<div class="modal-overlay" id="ai-modal">
  <div class="modal">
    <div id="ai-form">
      <div class="modal-title">✨ Yapay Zeka ile Eğitim Üret</div>
      <div class="modal-sub">Konu girin, yapay zeka eğitim metnini ve soruları hazırlasın.</div>
      <div class="form-group"><label class="form-label">Eğitim Konusu *</label><input type="text" class="form-input" id="ai-konu" placeholder="örn: Vinç Güvenliği"></div>
      <div class="form-group"><label class="form-label">Sektör</label><input type="text" class="form-input" id="ai-sektor" value="Çimento fabrikası"></div>
      <div class="form-group"><label class="form-label">Ek Notlar</label><textarea class="form-input" id="ai-notlar" placeholder="Özellikle vurgulanmasını istediğin noktalar..."></textarea></div>
      <div class="modal-footer">
        <button class="btn btn-ai" style="flex:1" onclick="egitimUret()">✨ Üret</button>
        <button class="btn btn-dark" onclick="modalKapat('ai-modal')">İptal</button>
      </div>
    </div>
    <div class="ai-progress" id="ai-progress"><div class="ai-spinner"></div><div class="ai-status">Yapay zeka hazırlıyor... (~15 sn)</div></div>
    <div class="ai-success" id="ai-success">
      <div class="success-icon">🎉</div>
      <div class="success-text">Eğitim oluşturuldu!</div>
      <div class="success-sub" id="ai-success-detail"></div>
      <div class="modal-footer" style="justify-content:center;margin-top:20px">
        <button class="btn btn-primary" onclick="modalKapat('ai-modal');egitimListesiYukle()">Eğitimlere Dön</button>
      </div>
    </div>
  </div>
</div>

<script>
const bugun = new Date().toISOString().split('T')[0];
document.getElementById('tarih-bas').value = bugun;
document.getElementById('tarih-bitis').value = bugun;

function bugunSec(){ document.getElementById('tarih-bas').value=bugun; document.getElementById('tarih-bitis').value=bugun; verileriYukle(); }
function modalKapat(id){ document.getElementById(id).classList.remove('open'); }

function sekme(ad, el) {
  document.querySelectorAll('.tab-content').forEach(t=>t.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  document.getElementById('tab-'+ad).classList.add('active');
  el.classList.add('active');
  document.getElementById('filtre-bar').style.display = (ad==='calisanlar'||ad==='egitimler') ? 'none' : 'flex';
  if(ad==='calisanlar') calisanListesiYukle();
  if(ad==='egitimler') egitimListesiYukle();
}

// ── KAYITLAR ──────────────────────────────
async function verileriYukle() {
  const bas = document.getElementById('tarih-bas').value.split('-').reverse().join('.');
  const bitis = document.getElementById('tarih-bitis').value.split('-').reverse().join('.');
  const durum = document.getElementById('durum-f').value;
  document.getElementById('kayit-tb').innerHTML='<tr><td colspan="8"><div class="loading"><div class="spinner"></div>Yükleniyor...</div></td></tr>';
  document.getElementById('egitim-stats').innerHTML='<div class="loading"><div class="spinner"></div></div>';
  try {
    const r = await fetch(`/panel/api/kayitlar?bas=${bas}&bitis=${bitis}&durum=${encodeURIComponent(durum)}`);
    const d = await r.json();
    renderKayitlar(d.kayitlar);
    renderIstatistik(d.egitim_ozet);
  } catch(e) {
    document.getElementById('kayit-tb').innerHTML='<tr><td colspan="8"><div class="empty"><div class="empty-icon">⚠️</div>Yüklenemedi</div></td></tr>';
  }
}

function renderKayitlar(kayitlar) {
  const t=kayitlar.length, g=kayitlar.filter(k=>k.durum==='GEÇTİ').length, k=t-g;
  const p=kayitlar.filter(k=>k.puan).map(k=>parseInt(k.puan)||0);
  const ort=p.length?Math.round(p.reduce((a,b)=>a+b,0)/p.length):0;
  document.getElementById('st-t').textContent=t;
  document.getElementById('st-g').textContent=g;
  document.getElementById('st-o').textContent='%'+(t?Math.round(g/t*100):0)+' başarı';
  document.getElementById('st-k').textContent=k;
  document.getElementById('st-p').textContent=ort;
  if(!kayitlar.length){document.getElementById('kayit-tb').innerHTML='<tr><td colspan="8"><div class="empty"><div class="empty-icon">📋</div>Kayıt yok</div></td></tr>';return;}
  document.getElementById('kayit-tb').innerHTML=kayitlar.map(k=>`
    <tr>
      <td>${k.tarih||'—'}</td><td>${k.saat||'—'}</td>
      <td><strong>${k.ad_soyad||'—'}</strong></td>
      <td style="color:var(--muted);font-size:12px">${k.gorev||'—'}</td>
      <td>${k.egitim_konusu||'—'}</td>
      <td class="${parseInt(k.puan)>=70?'puan-y':'puan-d'}">${k.puan||'—'}</td>
      <td><span class="pill ${k.durum==='GEÇTİ'?'pill-gecti':'pill-kaldi'}">${k.durum||'—'}</span></td>
      <td>${k.kimlik_dogrulandi==='EVET'?'✅':'—'}</td>
    </tr>`).join('');
}

function renderIstatistik(ozet) {
  if(!Object.keys(ozet).length){document.getElementById('egitim-stats').innerHTML='<div class="empty"><div class="empty-icon">📊</div>Veri yok</div>';return;}
  document.getElementById('egitim-stats').innerHTML=Object.entries(ozet).map(([konu,e])=>{
    const pct=e.toplam?Math.round(e.gecti/e.toplam*100):0;
    const cls=pct>=70?'':pct>=50?'orta':'dusuk';
    return `<div class="eg-satir">
      <div><div class="eg-baslik">${konu}</div><div class="eg-meta">${e.toplam} katılım · ${e.gecti} geçti · ${e.kaldi} kaldı</div></div>
      <div class="bar-wrap"><div class="bar-fill ${cls}" style="width:${pct}%"></div></div>
      <div class="bar-pct" style="color:${pct>=70?'var(--green)':pct>=50?'var(--yellow)':'var(--red)'}">${pct}%</div>
    </div>`;}).join('');
}

// ── ÇALIŞANLAR ────────────────────────────
async function calisanListesiYukle() {
  document.getElementById('calisan-liste').innerHTML='<div class="loading"><div class="spinner"></div></div>';
  try {
    const r = await fetch('/panel/api/calisanlar');
    const d = await r.json();
    renderCalisanlar(d);
  } catch(e) {
    document.getElementById('calisan-liste').innerHTML='<div class="empty"><div class="empty-icon">⚠️</div>Yüklenemedi</div>';
  }
}

function renderCalisanlar(calisanlar) {
  if(!calisanlar.length){
    document.getElementById('calisan-liste').innerHTML='<div class="empty"><div class="empty-icon">👥</div>Henüz çalışan eklenmemiş<br><br><button class="btn btn-primary" onclick="calisanModalAc()">+ İlk Çalışanı Ekle</button></div>';
    return;
  }
  document.getElementById('calisan-liste').innerHTML = calisanlar.map(c=>`
    <div class="calisan-kart">
      <div class="calisan-kart-header">
        <div>
          <div class="calisan-ad">${c.ad_soyad} ${c.bugun_izinli ? '<span class="pill pill-izin">🏖 Bugün İzinli</span>' : ''}</div>
          <div class="calisan-gorev">${c.gorev}</div>
          <div class="calisan-id">ID: ${c.telegram_id}</div>
        </div>
        <div class="calisan-aksiyonlar">
          <button class="btn btn-dark btn-sm" onclick="calisanDuzenle(${c.telegram_id},'${c.ad_soyad}','${c.gorev}','${c.dogum_tarihi}')">Düzenle</button>
          <button class="btn btn-green btn-sm" onclick="izinModalAc(${c.telegram_id},'${c.ad_soyad}')">İzin Ver</button>
          <button class="btn btn-red btn-sm" onclick="silModalAc(${c.telegram_id},'${c.ad_soyad}')">Sil</button>
        </div>
      </div>
      <div class="calisan-ilerleme">
        <div style="display:flex;justify-content:space-between;font-size:12px;color:var(--muted)">
          <span>Eğitim İlerlemesi</span>
          <span>${c.tamamlanan}/${c.toplam_egitim} tamamlandı</span>
        </div>
        <div class="ilerleme-bar"><div class="ilerleme-dolu" style="width:${c.toplam_egitim?Math.round(c.tamamlanan/c.toplam_egitim*100):0}%"></div></div>
      </div>
    </div>`).join('');
}

function calisanModalAc() {
  document.getElementById('calisan-modal-baslik').textContent='Çalışan Ekle';
  document.getElementById('calisan-edit-id').value='';
  document.getElementById('c-tid').value=''; document.getElementById('c-tid').disabled=false;
  document.getElementById('c-ad').value='';
  document.getElementById('c-gorev').value='';
  document.getElementById('c-dogum').value='';
  document.getElementById('calisan-hata').style.display='none';
  document.getElementById('calisan-modal').classList.add('open');
}

function calisanDuzenle(tid, ad, gorev, dogum) {
  document.getElementById('calisan-modal-baslik').textContent='Çalışanı Düzenle';
  document.getElementById('calisan-edit-id').value=tid;
  document.getElementById('c-tid').value=tid; document.getElementById('c-tid').disabled=true;
  document.getElementById('c-ad').value=ad;
  document.getElementById('c-gorev').value=gorev;
  document.getElementById('c-dogum').value=dogum;
  document.getElementById('calisan-hata').style.display='none';
  document.getElementById('calisan-modal').classList.add('open');
}

async function calisanKaydet() {
  const editId = document.getElementById('calisan-edit-id').value;
  const tid = document.getElementById('c-tid').value.trim();
  const ad = document.getElementById('c-ad').value.trim();
  const gorev = document.getElementById('c-gorev').value.trim();
  const dogum = document.getElementById('c-dogum').value.trim();
  const hataEl = document.getElementById('calisan-hata');

  if(!tid||!ad||!gorev||!dogum){hataEl.textContent='Tüm alanları doldurun.';hataEl.style.display='block';return;}
  if(!/^\d{2}\.\d{2}\.\d{4}$/.test(dogum)){hataEl.textContent='Doğum tarihi GG.AA.YYYY formatında olmalı.';hataEl.style.display='block';return;}

  const endpoint = editId ? '/panel/api/calisan-guncelle' : '/panel/api/calisan-ekle';
  try {
    const r = await fetch(endpoint, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({telegram_id:parseInt(tid),ad_soyad:ad,gorev,dogum_tarihi:dogum})});
    const d = await r.json();
    if(d.basarili){modalKapat('calisan-modal');calisanListesiYukle();}
    else{hataEl.textContent=d.hata||'Hata oluştu.';hataEl.style.display='block';}
  } catch(e){hataEl.textContent='Bağlantı hatası.';hataEl.style.display='block';}
}

function silModalAc(tid, ad) {
  document.getElementById('sil-tid').value=tid;
  document.getElementById('sil-adi-text').textContent=`"${ad}" silinecek. Emin misiniz?`;
  document.getElementById('sil-modal').classList.add('open');
}

async function calisanSilOnayla() {
  const tid = document.getElementById('sil-tid').value;
  try {
    await fetch('/panel/api/calisan-sil', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({telegram_id:parseInt(tid)})});
    modalKapat('sil-modal'); calisanListesiYukle();
  } catch(e){}
}

function izinModalAc(tid, ad) {
  document.getElementById('izin-tid').value=tid;
  document.getElementById('izin-calisan-adi').textContent=`${ad} için izin tarihi ekleyin`;
  document.getElementById('izin-tarih1').value=bugun;
  document.getElementById('izin-tarih2').value='';
  document.getElementById('izin-tarih3').value='';
  document.getElementById('izin-modal').classList.add('open');
}

async function izinKaydet() {
  const tid = parseInt(document.getElementById('izin-tid').value);
  const tarihler = [
    document.getElementById('izin-tarih1').value,
    document.getElementById('izin-tarih2').value,
    document.getElementById('izin-tarih3').value
  ].filter(t=>t).map(t=>t.split('-').reverse().join('.'));

  if(!tarihler.length){modalKapat('izin-modal');return;}
  try {
    await fetch('/panel/api/izin-ekle', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({telegram_id:tid, tarihler})});
    modalKapat('izin-modal'); calisanListesiYukle();
  } catch(e){}
}

// ── EĞİTİMLER ────────────────────────────
async function egitimListesiYukle() {
  document.getElementById('egitim-liste').innerHTML='<div class="loading"><div class="spinner"></div></div>';
  try {
    const r = await fetch('/panel/api/egitimler');
    renderEgitimler(await r.json());
  } catch(e) { document.getElementById('egitim-liste').innerHTML='<div class="empty"><div class="empty-icon">⚠️</div>Yüklenemedi</div>'; }
}

function renderEgitimler(egitimler) {
  if(!egitimler.length){document.getElementById('egitim-liste').innerHTML='<div class="empty"><div class="empty-icon">📚</div>Eğitim yok</div>';return;}
  document.getElementById('egitim-liste').innerHTML=egitimler.map(e=>`
    <div class="egitim-kart">
      <div class="egitim-kart-header">
        <div><div class="egitim-kart-baslik">${e.baslik}</div><span class="egitim-tur">${e.tur}</span></div>
        <div style="font-size:12px;color:var(--muted);white-space:nowrap">${e.sure} · ${e.soru_sayisi} soru</div>
      </div>
      <div class="egitim-kart-body">${e.metin_onizleme}</div>
      <div class="egitim-kart-footer">
        <code class="egitim-kod">/egitim_gonder ${e.id}</code>
        <div style="display:flex;gap:8px">
          <button class="btn btn-primary btn-sm" onclick="egitimGonder('${e.id}', this)">▶️ Şimdi Gönder</button>
          <button class="btn btn-dark btn-sm" onclick="navigator.clipboard.writeText('/egitim_gonder ${e.id}');this.textContent='✓';setTimeout(()=>this.textContent='Kopyala',2000)">Kopyala</button>
        </div>
      </div>
    </div>`).join('');
}

// ── EĞİTİM GÖNDER ────────────────────────
async function egitimGonder(egitimId, btn) {
  const orijinal = btn.textContent;
  btn.textContent = '⏳';
  btn.disabled = true;
  try {
    const r = await fetch('/panel/api/egitim-gonder', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({egitim_id: egitimId})
    });
    const d = await r.json();
    if (d.basarili) {
      btn.textContent = '✅ Gönderildi';
      btn.style.background = 'var(--green)';
      setTimeout(() => { btn.textContent = orijinal; btn.style.background = ''; btn.disabled = false; }, 3000);
    } else {
      alert('Hata: ' + (d.hata || 'Bilinmeyen hata'));
      btn.textContent = orijinal;
      btn.disabled = false;
    }
  } catch(e) {
    alert('Bağlantı hatası');
    btn.textContent = orijinal;
    btn.disabled = false;
  }
}

// ── AI ────────────────────────────────────
function aiModalAc(){
  document.getElementById('ai-form').style.display='block';
  document.getElementById('ai-progress').style.display='none';
  document.getElementById('ai-success').style.display='none';
  document.getElementById('ai-modal').classList.add('open');
}

async function egitimUret() {
  const konu=document.getElementById('ai-konu').value.trim();
  if(!konu){alert('Konu girin.');return;}
  document.getElementById('ai-form').style.display='none';
  document.getElementById('ai-progress').style.display='block';
  try {
    const r=await fetch('/panel/api/egitim-uret',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({konu,sektor:document.getElementById('ai-sektor').value,notlar:document.getElementById('ai-notlar').value})});
    const d=await r.json();
    if(d.basarili){
      document.getElementById('ai-progress').style.display='none';
      document.getElementById('ai-success').style.display='block';
      document.getElementById('ai-success-detail').textContent=`"${d.baslik}" eklendi. /egitim_gonder ${d.id}`;
    } else {alert('Hata: '+(d.hata||'Bilinmeyen'));document.getElementById('ai-form').style.display='block';document.getElementById('ai-progress').style.display='none';}
  } catch(e){alert('Bağlantı hatası');document.getElementById('ai-form').style.display='block';document.getElementById('ai-progress').style.display='none';}
}

verileriYukle();
</script>
{% endif %}
</body>
</html>
"""

@app.route("/panel")
def panel():
    return render_template_string(HTML, logged_in=session.get("panel_giris",False), hata=False)

@app.route("/panel/login", methods=["POST"])
def login():
    if request.form.get("sifre","") == PANEL_SIFRE:
        session["panel_giris"] = True
        return redirect("/panel")
    return render_template_string(HTML, logged_in=False, hata=True)

@app.route("/panel/cikis")
def cikis():
    session.clear()
    return redirect("/panel")

@app.route("/panel/api/kayitlar")
def api_kayitlar():
    if not session.get("panel_giris"): return jsonify({"hata":"Yetkisiz"}),401
    bas=request.args.get("bas",""); bitis=request.args.get("bitis",""); df=request.args.get("durum","")
    try: kayitlar=tum_kayitlar_getir()
    except Exception as e: return jsonify({"hata":str(e),"kayitlar":[],"egitim_ozet":{}})
    def aralik(t):
        try:
            from datetime import datetime
            td=datetime.strptime(t,"%d.%m.%Y")
            if bas and td<datetime.strptime(bas,"%d.%m.%Y"): return False
            if bitis and td>datetime.strptime(bitis,"%d.%m.%Y"): return False
            return True
        except: return True
    f=[k for k in kayitlar if aralik(k.get("tarih",""))]
    if df: f=[k for k in f if k.get("durum")==df]
    ozet={}
    for k in f:
        konu=k.get("egitim_konusu","?")
        ozet.setdefault(konu,{"toplam":0,"gecti":0,"kaldi":0})
        ozet[konu]["toplam"]+=1
        if k.get("durum")=="GEÇTİ": ozet[konu]["gecti"]+=1
        else: ozet[konu]["kaldi"]+=1
    return jsonify({"kayitlar":f,"egitim_ozet":ozet})

@app.route("/panel/api/calisanlar")
def api_calisanlar():
    if not session.get("panel_giris"): return jsonify([]),401
    from config import EGITIMLER
    from durum import eksik_egitimler, izinli_mi
    calisanlar=tum_calisanlar()
    bugun=date.today().strftime("%d.%m.%Y")
    sonuc=[]
    for tid, c in calisanlar.items():
        eksik=eksik_egitimler(tid)
        sonuc.append({
            "telegram_id": tid,
            "ad_soyad": c["ad_soyad"],
            "gorev": c["gorev"],
            "dogum_tarihi": c["dogum_tarihi"],
            "bugun_izinli": izinli_mi(tid, bugun),
            "tamamlanan": len(EGITIMLER)-len(eksik),
            "toplam_egitim": len(EGITIMLER)
        })
    return jsonify(sonuc)

@app.route("/panel/api/calisan-ekle", methods=["POST"])
def api_calisan_ekle():
    if not session.get("panel_giris"): return jsonify({"basarili":False}),401
    d=request.get_json()
    try:
        calisan_ekle(int(d["telegram_id"]), d["ad_soyad"], d["dogum_tarihi"], d["gorev"])
        return jsonify({"basarili":True})
    except Exception as e:
        return jsonify({"basarili":False,"hata":str(e)})

@app.route("/panel/api/calisan-guncelle", methods=["POST"])
def api_calisan_guncelle():
    if not session.get("panel_giris"): return jsonify({"basarili":False}),401
    d=request.get_json()
    try:
        calisan_guncelle(int(d["telegram_id"]), d["ad_soyad"], d["dogum_tarihi"], d["gorev"])
        return jsonify({"basarili":True})
    except Exception as e:
        return jsonify({"basarili":False,"hata":str(e)})

@app.route("/panel/api/calisan-sil", methods=["POST"])
def api_calisan_sil():
    if not session.get("panel_giris"): return jsonify({"basarili":False}),401
    d=request.get_json()
    calisan_sil(int(d["telegram_id"]))
    return jsonify({"basarili":True})

@app.route("/panel/api/izin-ekle", methods=["POST"])
def api_izin_ekle():
    if not session.get("panel_giris"): return jsonify({"basarili":False}),401
    d=request.get_json()
    for t in d.get("tarihler",[]):
        izin_ekle(int(d["telegram_id"]), t)
    return jsonify({"basarili":True})

@app.route("/panel/api/egitimler")
def api_egitimler():
    if not session.get("panel_giris"): return jsonify([]),401
    liste=[]
    for eid,e in EGITIMLER.items():
        temiz=e["metin"].replace("*","").replace("_","").strip()
        liste.append({"id":eid,"baslik":e["baslik"],"tur":e["tur"],"sure":e["sure"],"soru_sayisi":len(e["sorular"]),"metin_onizleme":(temiz[:180]+"...") if len(temiz)>180 else temiz})
    return jsonify(liste)

@app.route("/panel/api/egitim-uret", methods=["POST"])
def api_egitim_uret():
    if not session.get("panel_giris"): return jsonify({"basarili":False}),401
    veri=request.get_json()
    konu=veri.get("konu","").strip()
    sektor=veri.get("sektor","Çimento fabrikası")
    notlar=veri.get("notlar","")
    if not konu: return jsonify({"basarili":False,"hata":"Konu boş"})
    api_key=os.environ.get("ANTHROPIC_API_KEY")
    if not api_key: return jsonify({"basarili":False,"hata":"ANTHROPIC_API_KEY ayarlanmamış"})
    prompt=f"""Aşağıdaki bilgilere göre bir iş başı eğitimi hazırla.
Konu: {konu}
Sektör: {sektor}
Ek notlar: {notlar if notlar else "Yok"}

SADECE JSON döndür:
{{"id":"ingilizce_kisa_anahtar","baslik":"Emoji + Türkçe başlık","tur":"İş Güvenliği","sure":"~XX dakika","metin":"Telegram Markdown eğitim metni, *kalın* kullan, 5 bölüm olsun","sorular":[{{"soru":"?","secenekler":["A","B","C","D"],"dogru":0}},{{"soru":"?","secenekler":["A","B","C","D"],"dogru":1}},{{"soru":"?","secenekler":["A","B","C","D"],"dogru":2}},{{"soru":"?","secenekler":["A","B","C","D"],"dogru":0}},{{"soru":"?","secenekler":["A","B","C","D"],"dogru":3}}]}}"""
    try:
        import urllib.request
        payload=json.dumps({"model":"claude-sonnet-4-6","max_tokens":2000,"messages":[{"role":"user","content":prompt}]}).encode()
        req=urllib.request.Request("https://api.anthropic.com/v1/messages",data=payload,
            headers={"Content-Type":"application/json","x-api-key":api_key,"anthropic-version":"2023-06-01"},method="POST")
        with urllib.request.urlopen(req,timeout=60) as resp:
            yanit=json.loads(resp.read().decode())
        icerik=yanit["content"][0]["text"].strip()
        icerik=re.sub(r"^```json\s*","",icerik); icerik=re.sub(r"^```\s*","",icerik); icerik=re.sub(r"\s*```$","",icerik).strip()
        egitim=json.loads(icerik)
        EGITIMLER[egitim["id"]]={"baslik":egitim["baslik"],"tur":egitim["tur"],"sure":egitim["sure"],"metin":egitim["metin"],"sorular":egitim["sorular"]}
        return jsonify({"basarili":True,"id":egitim["id"],"baslik":egitim["baslik"]})
    except Exception as e:
        return jsonify({"basarili":False,"hata":str(e)})

@app.route("/panel/api/egitim-gonder", methods=["POST"])
def api_egitim_gonder():
    if not session.get("panel_giris"): return jsonify({"basarili":False,"hata":"Yetkisiz"}),401
    from config import EGITIMLER, GRUP_ID
    from calisanlar import tum_calisanlar
    from durum import aktif_egitim_set

    veri = request.get_json()
    egitim_id = veri.get("egitim_id","").strip()
    egitim = EGITIMLER.get(egitim_id)
    if not egitim:
        return jsonify({"basarili":False,"hata":"Eğitim bulunamadı"})

    try:
        import requests as req_lib
        token = os.environ.get("TELEGRAM_BOT_TOKEN","")
        base = f"https://api.telegram.org/bot{token}"
        keyboard = {"inline_keyboard":[[{"text":"▶️ Eğitime Başla","callback_data":f"egitim_baslat:{egitim_id}"}]]}

        # Gruba gönder
        if GRUP_ID and GRUP_ID != 0:
            req_lib.post(f"{base}/sendMessage", json={
                "chat_id": GRUP_ID,
                "text": f"📋 *{egitim['baslik']}* eğitimi başladı\!\n\nKatılmak için 👇",
                "parse_mode": "Markdown",
                "reply_markup": keyboard
            }, timeout=10)

        # Aktif eğitim olarak işaretle
        aktif_egitim_set(egitim_id)

        # Kişisel bildirim
        calisanlar = tum_calisanlar()
        import time
        for uid, c in calisanlar.items():
            try:
                req_lib.post(f"{base}/sendMessage", json={
                    "chat_id": uid,
                    "text": f"📋 Yeni eğitim: *{egitim['baslik']}*\n\nBaşlamak için 👇",
                    "parse_mode": "Markdown",
                    "reply_markup": keyboard
                }, timeout=10)
                time.sleep(0.1)
            except Exception as e:
                pass

        return jsonify({"basarili":True})
    except Exception as e:
        return jsonify({"basarili":False,"hata":str(e)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",8080)))
