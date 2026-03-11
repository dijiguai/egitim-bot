"""
Yönetici Paneli — Flask web uygulaması
"""

from flask import Flask, render_template_string, jsonify, request, session, redirect
from datetime import date
import os, json, re
from sheets import kayitlari_getir, tum_kayitlar_getir
from config import EGITIMLER, GECME_NOTU

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

/* LOGIN */
.login-wrap{min-height:100vh;display:flex;align-items:center;justify-content:center;background:var(--dark)}
.login-box{background:#242420;border:1px solid #333;border-radius:16px;padding:40px;width:340px}
.login-title{font-family:'Syne',sans-serif;font-size:22px;font-weight:800;color:#fff;margin-bottom:6px}
.login-sub{font-size:13px;color:#666;margin-bottom:28px}
.login-box input{width:100%;background:#1a1a18;border:1px solid #333;border-radius:10px;padding:12px 16px;color:#fff;font-size:14px;margin-bottom:12px;outline:none;font-family:'DM Sans',sans-serif}
.login-box input:focus{border-color:var(--accent)}
.login-btn{width:100%;background:var(--accent);color:#fff;border:none;border-radius:10px;padding:13px;font-size:14px;font-weight:600;cursor:pointer;font-family:'Syne',sans-serif}
.login-err{color:var(--red);font-size:12px;margin-top:8px;text-align:center}

/* HEADER */
.header{background:var(--dark);padding:0 24px;height:56px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100}
.header-logo{font-family:'Syne',sans-serif;font-weight:800;font-size:16px;color:#fff;display:flex;align-items:center;gap:10px}
.logo-dot{width:8px;height:8px;background:var(--accent);border-radius:50%;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.5;transform:scale(1.3)}}
.header-right{display:flex;align-items:center;gap:12px}
.logout-btn{background:#333;color:#aaa;border:none;border-radius:8px;padding:6px 14px;font-size:12px;cursor:pointer}

/* TABS */
.tabs{background:var(--dark);display:flex;gap:4px;padding:0 24px 0;border-bottom:1px solid #333}
.tab{padding:12px 20px;font-size:13px;color:#666;cursor:pointer;border-bottom:2px solid transparent;transition:all .15s;font-weight:500}
.tab:hover{color:#aaa}
.tab.active{color:#fff;border-bottom-color:var(--accent)}

/* MAIN */
.main{padding:24px;max-width:1100px;margin:0 auto}
.tab-content{display:none}.tab-content.active{display:block}

/* FILTERS */
.filters{display:flex;gap:10px;margin-bottom:24px;flex-wrap:wrap;align-items:flex-end}
.filter-group{display:flex;flex-direction:column;gap:4px}
.filter-label{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:1px}
select,input[type=date]{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:8px 12px;font-size:13px;color:var(--text);outline:none;font-family:'DM Sans',sans-serif;cursor:pointer}
select:focus,input[type=date]:focus{border-color:var(--accent)}
.btn{border:none;border-radius:8px;padding:9px 20px;font-size:13px;font-weight:600;cursor:pointer;font-family:'Syne',sans-serif;transition:all .15s}
.btn-primary{background:var(--accent);color:#fff}
.btn-primary:hover{background:#d44f24}
.btn-dark{background:#333;color:#fff}
.btn-dark:hover{background:#444}
.btn-ai{background:linear-gradient(135deg,#2e7de8,#7c3aed);color:#fff}
.btn-ai:hover{opacity:.9}
.btn-sm{padding:5px 12px;font-size:12px}

/* STATS */
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:24px}
@media(max-width:640px){.stats{grid-template-columns:repeat(2,1fr)}}
.stat{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:20px;position:relative;overflow:hidden}
.stat::after{content:'';position:absolute;bottom:0;left:0;right:0;height:3px;background:var(--accent)}
.stat.green::after{background:var(--green)}.stat.red::after{background:var(--red)}.stat.blue::after{background:var(--accent2)}
.stat-label{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:10px}
.stat-val{font-family:'Syne',sans-serif;font-size:36px;font-weight:800;line-height:1}
.stat-val.green{color:var(--green)}.stat-val.red{color:var(--red)}.stat-val.blue{color:var(--accent2)}.stat-val.orange{color:var(--accent)}
.stat-sub{font-size:12px;color:var(--muted);margin-top:6px}

/* SECTION */
.section-title{font-family:'Syne',sans-serif;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;color:var(--muted);margin-bottom:14px;margin-top:28px}

/* TABLE */
.table-wrap{background:var(--card);border:1px solid var(--border);border-radius:14px;overflow:hidden;overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:13px;min-width:600px}
th{background:#f9f7f4;padding:11px 16px;text-align:left;font-size:10px;text-transform:uppercase;letter-spacing:1px;color:var(--muted);font-weight:600;border-bottom:1px solid var(--border);white-space:nowrap}
td{padding:12px 16px;border-bottom:1px solid var(--border);color:var(--text)}
tr:last-child td{border-bottom:none}
tr:hover td{background:#faf8f5}
.pill{display:inline-block;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600}
.pill-gecti{background:#e8f7f0;color:var(--green)}.pill-kaldi{background:#fdecea;color:var(--red)}
.puan-y{color:var(--green);font-weight:700}.puan-d{color:var(--red);font-weight:700}

/* CALISAN */
.calisan-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:14px}
.calisan-kart{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:20px;transition:all .15s}
.calisan-kart:hover{border-color:var(--accent);transform:translateY(-1px)}
.calisan-ad{font-family:'Syne',sans-serif;font-weight:700;font-size:15px;margin-bottom:4px}
.calisan-gorev{font-size:12px;color:var(--muted);margin-bottom:14px}
.calisan-stats{display:flex;gap:16px}
.cs-item{text-align:center}
.cs-val{font-family:'Syne',sans-serif;font-size:20px;font-weight:800}
.cs-lbl{font-size:10px;color:var(--muted);margin-top:2px}

/* EGİTİM SATIRI */
.eg-satir{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:16px 20px;margin-bottom:10px;display:flex;align-items:center;gap:16px;flex-wrap:wrap}
.eg-baslik{font-weight:600;font-size:14px;flex:1;min-width:180px}
.eg-meta{font-size:12px;color:var(--muted)}
.bar-wrap{flex:1;min-width:100px;background:#f0ede8;border-radius:4px;height:8px;overflow:hidden}
.bar-fill{height:100%;border-radius:4px;background:var(--green);transition:width .5s}
.bar-fill.dusuk{background:var(--red)}.bar-fill.orta{background:var(--yellow)}
.bar-pct{font-family:'Syne',sans-serif;font-size:14px;font-weight:700;min-width:45px;text-align:right}

/* EĞİTİM LİSTESİ */
.egitim-kart{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:20px;margin-bottom:12px}
.egitim-kart-header{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;margin-bottom:10px}
.egitim-kart-baslik{font-family:'Syne',sans-serif;font-weight:700;font-size:16px}
.egitim-tur{display:inline-block;background:#f0ede8;border-radius:20px;padding:3px 10px;font-size:11px;color:var(--muted);font-weight:600}
.egitim-kart-body{font-size:13px;color:var(--muted);line-height:1.5;margin-bottom:12px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.egitim-kart-footer{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px}
.egitim-kod{font-size:11px;color:var(--muted);background:#f5f3ef;padding:4px 10px;border-radius:6px;font-family:monospace}
.egitim-aksiyonlar{display:flex;gap:8px}

/* AI MODAL */
.modal-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:1000;align-items:center;justify-content:center}
.modal-overlay.open{display:flex}
.modal{background:var(--card);border-radius:20px;padding:32px;width:100%;max-width:540px;max-height:90vh;overflow-y:auto}
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

/* LOADING/EMPTY */
.loading{text-align:center;padding:60px;color:var(--muted);font-size:14px}
.spinner{width:32px;height:32px;border:3px solid var(--border);border-top-color:var(--accent);border-radius:50%;animation:spin .8s linear infinite;margin:0 auto 16px}
.empty{text-align:center;padding:48px;color:var(--muted)}
.empty-icon{font-size:40px;margin-bottom:12px}

@media(max-width:480px){.main{padding:16px}.header{padding:0 16px}.tabs{padding:0 16px}.filters{flex-direction:column}}
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
        <input type="password" name="sifre" id="sifre-input" placeholder="Şifre" autofocus style="padding-right:44px">
        <button type="button" onclick="toggleSifre()" style="position:absolute;right:12px;top:14px;background:none;border:none;cursor:pointer;color:#666;font-size:18px" id="goz-btn">👁</button>
      </div>
      {% if hata %}<div class="login-err">⚠️ Yanlış şifre</div>{% endif %}
      <button class="login-btn" type="submit" style="margin-top:4px">Giriş Yap</button>
    </form>
    <script>
    function toggleSifre(){
      const i=document.getElementById('sifre-input'),b=document.getElementById('goz-btn');
      if(i.type==='password'){i.type='text';b.textContent='🙈';}else{i.type='password';b.textContent='👁';}
    }
    </script>
  </div>
</div>

{% else %}
<!-- HEADER -->
<div class="header">
  <div class="header-logo"><div class="logo-dot"></div>Eğitim Paneli</div>
  <div class="header-right">
    <a href="/panel/cikis"><button class="logout-btn">Çıkış</button></a>
  </div>
</div>

<!-- TABS -->
<div class="tabs">
  <div class="tab active" onclick="sekmeAc('kayitlar',this)">📊 Kayıtlar</div>
  <div class="tab" onclick="sekmeAc('calisanlar',this)">👥 Çalışanlar</div>
  <div class="tab" onclick="sekmeAc('istatistik',this)">📈 İstatistik</div>
  <div class="tab" onclick="sekmeAc('egitimler',this)">📚 Eğitimler</div>
</div>

<div class="main">

  <!-- FİLTRELER (kayıtlar/çalışanlar/istatistik için) -->
  <div id="filtre-bar" class="filters">
    <div class="filter-group">
      <span class="filter-label">Başlangıç</span>
      <input type="date" id="tarih-bas">
    </div>
    <div class="filter-group">
      <span class="filter-label">Bitiş</span>
      <input type="date" id="tarih-bitis">
    </div>
    <div class="filter-group">
      <span class="filter-label">Durum</span>
      <select id="durum-filtre"><option value="">Tümü</option><option value="GEÇTİ">Geçti</option><option value="KALDI">Kaldı</option></select>
    </div>
    <button class="btn btn-primary" onclick="verileriYukle()">Filtrele</button>
    <button class="btn btn-dark" onclick="bugunSec()">Bugün</button>
  </div>

  <!-- KAYITLAR -->
  <div class="tab-content active" id="tab-kayitlar">
    <div class="stats">
      <div class="stat orange"><div class="stat-label">Toplam</div><div class="stat-val orange" id="st-toplam">—</div><div class="stat-sub">Kayıt</div></div>
      <div class="stat green"><div class="stat-label">Geçti</div><div class="stat-val green" id="st-gecti">—</div><div class="stat-sub" id="st-oran">—</div></div>
      <div class="stat red"><div class="stat-label">Kaldı</div><div class="stat-val red" id="st-kaldi">—</div><div class="stat-sub">Yeniden eğitim</div></div>
      <div class="stat blue"><div class="stat-label">Ort. Puan</div><div class="stat-val blue" id="st-puan">—</div><div class="stat-sub">100 üzerinden</div></div>
    </div>
    <div class="section-title">Eğitim Kayıtları</div>
    <div class="table-wrap">
      <table>
        <thead><tr><th>Tarih</th><th>Saat</th><th>Çalışan</th><th>Görev</th><th>Eğitim</th><th>Puan</th><th>Durum</th><th>Kimlik</th></tr></thead>
        <tbody id="kayit-tbody"><tr><td colspan="8"><div class="loading"><div class="spinner"></div>Yükleniyor...</div></td></tr></tbody>
      </table>
    </div>
  </div>

  <!-- ÇALIŞANLAR -->
  <div class="tab-content" id="tab-calisanlar">
    <div class="section-title">Çalışan Bazında Özet</div>
    <div class="calisan-grid" id="calisan-grid"><div class="loading"><div class="spinner"></div></div></div>
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
        <div style="font-size:12px;color:var(--muted);margin-top:4px">Sabah eğitim göndermek için Telegram'da: <code style="background:#f0ede8;padding:2px 6px;border-radius:4px">/egitim_gonder [kod]</code></div>
      </div>
      <button class="btn btn-ai" onclick="aiModalAc()">✨ Yapay Zeka ile Eğitim Üret</button>
    </div>
    <div id="egitim-liste"></div>
  </div>

</div>

<!-- AI MODAL -->
<div class="modal-overlay" id="ai-modal">
  <div class="modal">
    <div id="ai-form-bolum">
      <div class="modal-title">✨ Yapay Zeka ile Eğitim Üret</div>
      <div class="modal-sub">Konu girin, yapay zeka eğitim metnini ve soruları otomatik hazırlasın.</div>
      <div class="form-group">
        <label class="form-label">Eğitim Konusu *</label>
        <input type="text" class="form-input" id="ai-konu" placeholder="örn: Vinç Operasyonu Güvenliği">
      </div>
      <div class="form-group">
        <label class="form-label">Sektör / Bağlam</label>
        <input type="text" class="form-input" id="ai-sektor" placeholder="örn: Çimento fabrikası, ağır sanayi" value="Çimento fabrikası">
      </div>
      <div class="form-group">
        <label class="form-label">Ek Notlar (isteğe bağlı)</label>
        <textarea class="form-input" id="ai-notlar" placeholder="Özellikle vurgulanmasını istediğin noktalar..."></textarea>
      </div>
      <div class="modal-footer">
        <button class="btn btn-ai" style="flex:1" onclick="egitimUret()">✨ Üret</button>
        <button class="btn btn-dark" onclick="aiModalKapat()">İptal</button>
      </div>
    </div>
    <div class="ai-progress" id="ai-progress">
      <div class="ai-spinner"></div>
      <div class="ai-status" id="ai-status-text">Yapay zeka eğitim hazırlıyor...</div>
    </div>
    <div class="ai-success" id="ai-success">
      <div class="success-icon">🎉</div>
      <div class="success-text">Eğitim başarıyla oluşturuldu!</div>
      <div class="success-sub" id="ai-success-detail"></div>
      <div class="modal-footer" style="justify-content:center;margin-top:20px">
        <button class="btn btn-primary" onclick="aiModalKapat();egitimListesiYukle()">Eğitimlere Dön</button>
      </div>
    </div>
  </div>
</div>

<script>
const bugun = new Date().toISOString().split('T')[0];
document.getElementById('tarih-bas').value = bugun;
document.getElementById('tarih-bitis').value = bugun;

let tumVeri = {kayitlar:[], calisan_ozet:{}, egitim_ozet:{}};

function bugunSec(){
  document.getElementById('tarih-bas').value = bugun;
  document.getElementById('tarih-bitis').value = bugun;
  verileriYukle();
}

function sekmeAc(sekme, el) {
  document.querySelectorAll('.tab-content').forEach(t=>t.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  document.getElementById('tab-'+sekme).classList.add('active');
  el.classList.add('active');
  document.getElementById('filtre-bar').style.display = sekme==='egitimler' ? 'none' : 'flex';
  if(sekme==='egitimler') egitimListesiYukle();
}

async function verileriYukle() {
  const bas = document.getElementById('tarih-bas').value.split('-').reverse().join('.');
  const bitis = document.getElementById('tarih-bitis').value.split('-').reverse().join('.');
  const durum = document.getElementById('durum-filtre').value;
  document.getElementById('kayit-tbody').innerHTML = '<tr><td colspan="8"><div class="loading"><div class="spinner"></div>Yükleniyor...</div></td></tr>';
  document.getElementById('calisan-grid').innerHTML = '<div class="loading"><div class="spinner"></div></div>';
  document.getElementById('egitim-stats').innerHTML = '<div class="loading"><div class="spinner"></div></div>';
  try {
    const res = await fetch(`/panel/api/kayitlar?bas=${bas}&bitis=${bitis}&durum=${encodeURIComponent(durum)}`);
    tumVeri = await res.json();
    renderKayitlar(tumVeri.kayitlar);
    renderCalisanlar(tumVeri.calisan_ozet);
    renderIstatistik(tumVeri.egitim_ozet);
  } catch(e) {
    document.getElementById('kayit-tbody').innerHTML = '<tr><td colspan="8"><div class="empty"><div class="empty-icon">⚠️</div>Veri yüklenemedi</div></td></tr>';
  }
}

function renderKayitlar(kayitlar) {
  const t=kayitlar.length, g=kayitlar.filter(k=>k.durum==='GEÇTİ').length;
  const k=kayitlar.filter(k=>k.durum==='KALDI').length;
  const p=kayitlar.filter(k=>k.puan).map(k=>parseInt(k.puan)||0);
  const ort=p.length?Math.round(p.reduce((a,b)=>a+b,0)/p.length):0;
  document.getElementById('st-toplam').textContent=t;
  document.getElementById('st-gecti').textContent=g;
  document.getElementById('st-oran').textContent='%'+( t?Math.round(g/t*100):0)+' başarı';
  document.getElementById('st-kaldi').textContent=k;
  document.getElementById('st-puan').textContent=ort;
  if(!kayitlar.length){document.getElementById('kayit-tbody').innerHTML='<tr><td colspan="8"><div class="empty"><div class="empty-icon">📋</div>Bu dönemde kayıt yok</div></td></tr>';return;}
  document.getElementById('kayit-tbody').innerHTML=kayitlar.map(k=>`
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

function renderCalisanlar(ozet) {
  if(!Object.keys(ozet).length){document.getElementById('calisan-grid').innerHTML='<div class="empty"><div class="empty-icon">👥</div>Veri yok</div>';return;}
  document.getElementById('calisan-grid').innerHTML=Object.entries(ozet).map(([ad,c])=>`
    <div class="calisan-kart">
      <div class="calisan-ad">${ad}</div>
      <div class="calisan-gorev">${c.gorev}</div>
      <div class="calisan-stats">
        <div class="cs-item"><div class="cs-val" style="color:var(--accent)">${c.toplam}</div><div class="cs-lbl">Eğitim</div></div>
        <div class="cs-item"><div class="cs-val" style="color:var(--green)">${c.gecti}</div><div class="cs-lbl">Geçti</div></div>
        <div class="cs-item"><div class="cs-val" style="color:var(--red)">${c.kaldi}</div><div class="cs-lbl">Kaldı</div></div>
        <div class="cs-item"><div class="cs-val" style="color:var(--accent2)">${c.ort_puan}</div><div class="cs-lbl">Ort.</div></div>
      </div>
    </div>`).join('');
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

async function egitimListesiYukle() {
  document.getElementById('egitim-liste').innerHTML = '<div class="loading"><div class="spinner"></div>Yükleniyor...</div>';
  try {
    const res = await fetch('/panel/api/egitimler');
    const data = await res.json();
    renderEgitimler(data);
  } catch(e) {
    document.getElementById('egitim-liste').innerHTML = '<div class="empty"><div class="empty-icon">⚠️</div>Yüklenemedi</div>';
  }
}

function renderEgitimler(egitimler) {
  if(!egitimler.length){document.getElementById('egitim-liste').innerHTML='<div class="empty"><div class="empty-icon">📚</div>Eğitim yok</div>';return;}
  document.getElementById('egitim-liste').innerHTML = egitimler.map(e=>`
    <div class="egitim-kart">
      <div class="egitim-kart-header">
        <div>
          <div class="egitim-kart-baslik">${e.baslik}</div>
          <span class="egitim-tur">${e.tur}</span>
        </div>
        <div style="font-size:12px;color:var(--muted);white-space:nowrap">${e.sure} · ${e.soru_sayisi} soru</div>
      </div>
      <div class="egitim-kart-body">${e.metin_onizleme}</div>
      <div class="egitim-kart-footer">
        <code class="egitim-kod">/egitim_gonder ${e.id}</code>
        <div class="egitim-aksiyonlar">
          <button class="btn btn-dark btn-sm" onclick="navigator.clipboard.writeText('/egitim_gonder ${e.id}');this.textContent='✓ Kopyalandı';setTimeout(()=>this.textContent='Kodu Kopyala',2000)">Kodu Kopyala</button>
        </div>
      </div>
    </div>`).join('');
}

// AI MODAL
function aiModalAc(){document.getElementById('ai-modal').classList.add('open');}
function aiModalKapat(){
  document.getElementById('ai-modal').classList.remove('open');
  document.getElementById('ai-form-bolum').style.display='block';
  document.getElementById('ai-progress').style.display='none';
  document.getElementById('ai-success').style.display='none';
}

async function egitimUret() {
  const konu = document.getElementById('ai-konu').value.trim();
  const sektor = document.getElementById('ai-sektor').value.trim();
  const notlar = document.getElementById('ai-notlar').value.trim();
  if(!konu){alert('Lütfen eğitim konusunu girin.');return;}
  document.getElementById('ai-form-bolum').style.display='none';
  document.getElementById('ai-progress').style.display='block';
  document.getElementById('ai-status-text').textContent='Yapay zeka eğitim hazırlıyor... (~15 saniye)';
  try {
    const res = await fetch('/panel/api/egitim-uret', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({konu, sektor, notlar})
    });
    const data = await res.json();
    if(data.basarili) {
      document.getElementById('ai-progress').style.display='none';
      document.getElementById('ai-success').style.display='block';
      document.getElementById('ai-success-detail').textContent = `"${data.baslik}" eğitimi sisteme eklendi. Telegram'da /egitim_gonder ${data.id} ile gönderin.`;
    } else {
      alert('Hata: ' + (data.hata || 'Bilinmeyen hata'));
      document.getElementById('ai-form-bolum').style.display='block';
      document.getElementById('ai-progress').style.display='none';
    }
  } catch(e) {
    alert('Bağlantı hatası: ' + e.message);
    document.getElementById('ai-form-bolum').style.display='block';
    document.getElementById('ai-progress').style.display='none';
  }
}

// Başlangıçta yükle
verileriYukle();
</script>
{% endif %}
</body>
</html>
"""


@app.route("/panel", methods=["GET"])
def panel():
    return render_template_string(HTML, logged_in=session.get("panel_giris", False), hata=False)

@app.route("/panel/login", methods=["POST"])
def login():
    if request.form.get("sifre", "") == PANEL_SIFRE:
        session["panel_giris"] = True
        return redirect("/panel")
    return render_template_string(HTML, logged_in=False, hata=True)

@app.route("/panel/cikis")
def cikis():
    session.clear()
    return redirect("/panel")


@app.route("/panel/api/kayitlar")
def api_kayitlar():
    if not session.get("panel_giris"):
        return jsonify({"hata": "Yetkisiz"}), 401
    bas = request.args.get("bas", "")
    bitis = request.args.get("bitis", "")
    durum_filtre = request.args.get("durum", "")
    try:
        kayitlar = tum_kayitlar_getir()
    except Exception as e:
        return jsonify({"hata": str(e), "kayitlar": [], "calisan_ozet": {}, "egitim_ozet": {}})

    def araliginda(t):
        try:
            from datetime import datetime
            td = datetime.strptime(t, "%d.%m.%Y")
            if bas and td < datetime.strptime(bas, "%d.%m.%Y"): return False
            if bitis and td > datetime.strptime(bitis, "%d.%m.%Y"): return False
            return True
        except: return True

    filtrelenmis = [k for k in kayitlar if araliginda(k.get("tarih",""))]
    if durum_filtre:
        filtrelenmis = [k for k in filtrelenmis if k.get("durum") == durum_filtre]

    calisan_ozet = {}
    for k in filtrelenmis:
        ad = k.get("ad_soyad","Bilinmiyor")
        if ad not in calisan_ozet:
            calisan_ozet[ad] = {"toplam":0,"gecti":0,"kaldi":0,"puanlar":[],"gorev":k.get("gorev","—")}
        calisan_ozet[ad]["toplam"] += 1
        if k.get("durum") == "GEÇTİ": calisan_ozet[ad]["gecti"] += 1
        else: calisan_ozet[ad]["kaldi"] += 1
        try: calisan_ozet[ad]["puanlar"].append(int(k.get("puan",0)))
        except: pass
    for ad in calisan_ozet:
        p = calisan_ozet[ad]["puanlar"]
        calisan_ozet[ad]["ort_puan"] = round(sum(p)/len(p)) if p else 0
        del calisan_ozet[ad]["puanlar"]

    egitim_ozet = {}
    for k in filtrelenmis:
        konu = k.get("egitim_konusu","Bilinmiyor")
        if konu not in egitim_ozet:
            egitim_ozet[konu] = {"toplam":0,"gecti":0,"kaldi":0}
        egitim_ozet[konu]["toplam"] += 1
        if k.get("durum") == "GEÇTİ": egitim_ozet[konu]["gecti"] += 1
        else: egitim_ozet[konu]["kaldi"] += 1

    return jsonify({"kayitlar": filtrelenmis, "calisan_ozet": calisan_ozet, "egitim_ozet": egitim_ozet})


@app.route("/panel/api/egitimler")
def api_egitimler():
    if not session.get("panel_giris"):
        return jsonify({"hata": "Yetkisiz"}), 401
    liste = []
    for egitim_id, e in EGITIMLER.items():
        metin_temiz = e["metin"].replace("*","").replace("_","").strip()
        onizleme = metin_temiz[:180] + "..." if len(metin_temiz) > 180 else metin_temiz
        liste.append({
            "id": egitim_id,
            "baslik": e["baslik"],
            "tur": e["tur"],
            "sure": e["sure"],
            "soru_sayisi": len(e["sorular"]),
            "metin_onizleme": onizleme
        })
    return jsonify(liste)


@app.route("/panel/api/egitim-uret", methods=["POST"])
def api_egitim_uret():
    if not session.get("panel_giris"):
        return jsonify({"hata": "Yetkisiz"}), 401

    veri = request.get_json()
    konu = veri.get("konu","").strip()
    sektor = veri.get("sektor","Çimento fabrikası")
    notlar = veri.get("notlar","")

    if not konu:
        return jsonify({"basarili": False, "hata": "Konu boş"})

    # Anthropic API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return jsonify({"basarili": False, "hata": "ANTHROPIC_API_KEY ayarlanmamış"})

    prompt = f"""Aşağıdaki bilgilere göre bir iş başı eğitimi hazırla.

Konu: {konu}
Sektör: {sektor}
Ek notlar: {notlar if notlar else "Yok"}

ÇIKTI FORMATI — Sadece JSON döndür, başka hiçbir şey yazma:
{{
  "id": "konuyu_temsil_eden_kisa_ingilizce_anahtar_kelime_alt_cizgi_ile",
  "baslik": "Emoji + Türkçe başlık",
  "tur": "İş Güvenliği veya Çimento/Üretim veya Acil Durum veya İş Sağlığı",
  "sure": "~XX dakika",
  "metin": "Telegram Markdown formatında eğitim metni. *kalın* için yıldız kullan. En az 5 başlık bölümü olsun. Gerçekçi ve detaylı olsun.",
  "sorular": [
    {{"soru": "?", "secenekler": ["A", "B", "C", "D"], "dogru": 0}},
    {{"soru": "?", "secenekler": ["A", "B", "C", "D"], "dogru": 1}},
    {{"soru": "?", "secenekler": ["A", "B", "C", "D"], "dogru": 2}},
    {{"soru": "?", "secenekler": ["A", "B", "C", "D"], "dogru": 0}},
    {{"soru": "?", "secenekler": ["A", "B", "C", "D"], "dogru": 3}}
  ]
}}

Kurallar:
- "dogru" değeri 0-3 arası index (A=0, B=1, C=2, D=3)
- Her soruda tam 4 seçenek olsun
- Sorular eğitim metninden üretilsin
- Türkçe yaz"""

    try:
        import urllib.request
        import urllib.error

        payload = json.dumps({
            "model": "claude-opus-4-6",
            "max_tokens": 2000,
            "messages": [{"role": "user", "content": prompt}]
        }).encode("utf-8")

        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01"
            },
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=60) as resp:
            yanit = json.loads(resp.read().decode("utf-8"))

        icerik = yanit["content"][0]["text"].strip()
        # JSON temizle
        icerik = re.sub(r"^```json\s*", "", icerik)
        icerik = re.sub(r"^```\s*", "", icerik)
        icerik = re.sub(r"\s*```$", "", icerik).strip()

        egitim = json.loads(icerik)

        # Config'e dinamik olarak ekle
        EGITIMLER[egitim["id"]] = {
            "baslik": egitim["baslik"],
            "tur": egitim["tur"],
            "sure": egitim["sure"],
            "metin": egitim["metin"],
            "sorular": egitim["sorular"]
        }

        # config.py dosyasına da yaz (kalıcı olsun)
        _config_guncelle(egitim["id"], egitim)

        return jsonify({"basarili": True, "id": egitim["id"], "baslik": egitim["baslik"]})

    except Exception as e:
        return jsonify({"basarili": False, "hata": str(e)})


def _config_guncelle(egitim_id: str, egitim: dict):
    """Yeni eğitimi config.py dosyasına yazar."""
    try:
        config_yolu = os.path.join(os.path.dirname(__file__), "config.py")
        with open(config_yolu, "r", encoding="utf-8") as f:
            icerik = f.read()

        yeni_blok = f"""
    "{egitim_id}": {{
        "baslik": {json.dumps(egitim['baslik'], ensure_ascii=False)},
        "tur": {json.dumps(egitim['tur'], ensure_ascii=False)},
        "sure": {json.dumps(egitim['sure'], ensure_ascii=False)},
        "metin": {json.dumps(egitim['metin'], ensure_ascii=False)},
        "sorular": {json.dumps(egitim['sorular'], ensure_ascii=False, indent=8)}
    }},
"""
        icerik = icerik.replace("\n}\n", f"\n{yeni_blok}\n}}\n", 1)
        with open(config_yolu, "w", encoding="utf-8") as f:
            f.write(icerik)
    except Exception as e:
        pass  # Dinamik olarak zaten eklendi, dosya yazma isteğe bağlı


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
