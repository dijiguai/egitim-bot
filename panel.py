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
.calisan-aksiyonlar{display:flex;gap:6px;flex-wrap:wrap}
.btn-orange{background:#e67e22;color:#fff}.btn-orange:hover{background:#d35400}
.pill{font-size:11px;padding:2px 8px;border-radius:20px;margin-left:6px;font-weight:600}
.pill-izin{background:#fff3cd;color:#856404}
.pill-gecti{background:#d1f5d3;color:#1a7431}
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
  <div style="display:flex;align-items:center;gap:12px">
    <div class="header-logo" style="cursor:pointer" onclick="anaSeyfayaDon()"><div class="logo-dot"></div>Eğitim Paneli</div>
    <span id="aktif-firma-adi" style="font-size:13px;color:var(--muted);display:none"></span>
  </div>
  <div style="display:flex;gap:8px;align-items:center">
    <button id="geri-btn" class="btn btn-dark btn-sm" onclick="anaSeyfayaDon()" style="display:none">← Firmalar</button>
    <a href="/panel/cikis"><button class="logout-btn">Çıkış</button></a>
  </div>
</div>
<div class="tabs" id="ana-tabs" style="display:none">
  <div class="tab active" onclick="sekme('kayitlar',this)">📊 Kayıtlar</div>
  <div class="tab" onclick="sekme('calisanlar',this)">👥 Çalışanlar</div>
  <div class="tab" onclick="sekme('istatistik',this)">📈 İstatistik</div>
  <div class="tab" onclick="sekme('mesajlar',this)">💬 Grup Mesajları</div>
  <div class="tab" onclick="sekme('egitimler',this)">📚 Eğitimler</div>
  <div class="tab" onclick="sekme('davetler',this)">📱 Davetler</div>
</div>

<div class="main">

  <!-- FİLTRELER -->
  <div id="filtre-bar" class="filters" style="display:none">
    <div class="filter-group"><span class="filter-label">Başlangıç</span><input type="date" id="tarih-bas"></div>
    <div class="filter-group"><span class="filter-label">Bitiş</span><input type="date" id="tarih-bitis"></div>
    <div class="filter-group"><span class="filter-label">Durum</span>
      <select id="durum-f"><option value="">Tümü</option><option value="GEÇTİ">Geçti</option><option value="KALDI">Kaldı</option></select>
    </div>
    <button class="btn btn-primary" onclick="verileriYukle()">Filtrele</button>
    <button class="btn btn-dark" onclick="bugunSec()">Bugün</button>
  </div>

  <!-- KAYITLAR -->
  <!-- ANA SAYFA — Firma Kartları -->
  <div id="ana-sayfa" style="padding:32px 24px">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:24px">
      <div>
        <div style="font-family:'Syne',sans-serif;font-size:22px;font-weight:700">Firmalar</div>
        <div style="font-size:13px;color:var(--muted);margin-top:4px">Yönetmek istediğiniz firmayı seçin</div>
      </div>
      <button class="btn btn-primary" onclick="firmaEkleModalAc()">+ Yeni Firma Ekle</button>
    </div>
    <div id="firma-kartlari" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px"></div>
  </div>

  <div class="tab-content" id="tab-kayitlar">
    <div class="stats">
      <div class="stat orange"><div class="stat-label">Toplam</div><div class="stat-val orange" id="st-t">—</div><div class="stat-sub">Kayıt</div></div>
      <div class="stat green"><div class="stat-label">Geçti</div><div class="stat-val green" id="st-g">—</div><div class="stat-sub" id="st-o">—</div></div>
      <div class="stat red"><div class="stat-label">Kaldı</div><div class="stat-val red" id="st-k">—</div><div class="stat-sub">Yeniden eğitim</div></div>
      <div class="stat blue"><div class="stat-label">Ort. Puan</div><div class="stat-val blue" id="st-p">—</div><div class="stat-sub">100 üzerinden</div></div>
    </div>
    <div style="display:flex;justify-content:space-between;align-items:center">
      <div class="section-title" style="margin-bottom:0">Eğitim Kayıtları</div>
      <button class="btn btn-dark btn-sm" onclick="verileriYukle();this.textContent='✓ Yenilendi';setTimeout(()=>this.textContent='🔄 Yenile',1500)">🔄 Yenile</button>
    </div>
    <div class="table-wrap" style="margin-top:14px">
      <table>
        <thead><tr><th>Tarih</th><th>Saat</th><th>Çalışan</th><th>Görev</th><th>Eğitim</th><th>Puan</th><th>Durum</th><th>Kimlik</th></tr></thead>
        <tbody id="kayit-tb"><tr><td colspan="8"><div class="loading"><div class="spinner"></div>Yükleniyor...</div></td></tr></tbody>
      </table>
    </div>
  </div>

  <!-- ÇALIŞANLAR -->
  <div class="tab-content" id="tab-calisanlar">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;flex-wrap:wrap;gap:12px">
      <div style="display:flex;align-items:center;gap:12px">
        <div class="section-title" style="margin:0">Çalışan Listesi</div>
        <div style="display:flex;background:var(--bg);border:1px solid var(--border);border-radius:8px;overflow:hidden">
          <button id="btn-aktif" class="btn btn-dark btn-sm" style="border-radius:0;border:none" onclick="calisanModGec('aktif')">👥 Aktif</button>
          <button id="btn-arsiv" class="btn btn-sm" style="border-radius:0;border:none;background:transparent;color:var(--muted)" onclick="calisanModGec('arsiv')">📦 Arşiv</button>
        </div>
      </div>
      <div style="display:flex;gap:8px" id="aktif-butonlar">
        <button class="btn btn-dark btn-sm" onclick="kayitButonuGonder(this)">📌 Kayıt Butonu Gönder</button>
        <button class="btn btn-primary" onclick="calisanModalAc()">+ Çalışan Ekle</button>
      </div>
    </div>
    <div id="calisan-liste"><div class="loading"><div class="spinner"></div></div></div>
  </div>

  <!-- İSTATİSTİK -->
  <div class="tab-content" id="tab-mesajlar">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <div class="section-title" style="margin:0">Grup Mesaj Logları</div>
      <div style="display:flex;gap:8px;align-items:center">
        <input type="text" id="mesaj-filtre" class="form-input" style="width:200px;padding:6px 10px" placeholder="İsim veya mesaj ara..." oninput="mesajFiltrele()">
        <button class="btn btn-dark btn-sm" onclick="mesajLogYukle()">🔄 Yenile</button>
      </div>
    </div>
    <div id="mesaj-log-liste"><div class="empty"><div class="empty-icon">💬</div>Yükleniyor...</div></div>
  </div>

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
      <button class="btn btn-dark btn-sm" onclick="manuelEgitimModalAc()">📝 Manuel Ekle</button>
      <button class="btn btn-ai" onclick="aiModalAc()">✨ Yapay Zeka ile Üret</button>
    </div>
    <div id="egitim-liste"><div class="loading"><div class="spinner"></div></div></div>
  </div>

  <!-- DAVETLER -->
  <div class="tab-content" id="tab-davetler">
    <!-- Ayarlar bolumu -->
    <div style="background:var(--card);border:1px solid var(--border);border-radius:14px;padding:20px;margin-bottom:20px">
      <div class="section-title" style="margin-bottom:12px">⚙️ Davet Ayarları</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
        <div class="form-group" style="margin:0">
          <label class="form-label">Telegram Grup Davet Linki</label>
          <div style="display:flex;gap:8px">
            <input type="text" class="form-input" id="ayar-grup-link" placeholder="https://t.me/+xxxxxxxx" style="flex:1">
            <button class="btn btn-dark btn-sm" onclick="ayarKaydet('grup_link','ayar-grup-link')">💾</button>
          </div>
          <div id="ayar-grup-link-info" style="font-size:11px;color:var(--accent);margin-top:4px;font-weight:600"></div>
      <div style="font-size:11px;color:var(--muted);margin-top:2px">Telegram grubu → Davet Linki Oluştur</div>
        </div>
        <div class="form-group" style="margin:0">
          <label class="form-label">Admin WhatsApp Numarası</label>
          <div style="display:flex;gap:8px">
            <input type="text" class="form-input" id="ayar-admin-tel" placeholder="+905321234567" style="flex:1">
            <button class="btn btn-dark btn-sm" onclick="ayarKaydet('admin_tel','ayar-admin-tel')">💾</button>
          </div>
          <div id="ayar-admin-tel-info" style="font-size:11px;color:var(--accent);margin-top:4px;font-weight:600"></div>
      <div style="font-size:11px;color:var(--muted);margin-top:2px">Mesajlar bu numara üzerinden gönderilir</div>
        </div>
      </div>
    </div>
    <!-- Liste -->
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;flex-wrap:wrap;gap:12px">
      <div>
        <div class="section-title" style="margin:0">WhatsApp Davet Listesi</div>
        <div style="font-size:12px;color:var(--muted);margin-top:4px">Kişi ekle → 📨 Gönder butonuna bas → WhatsApp açılır → Gönder</div>
      </div>
      <button class="btn btn-primary" onclick="davetEkleModalAc()">+ Kişi Ekle</button>
    </div>
    <div id="davet-liste"><div class="loading"><div class="spinner"></div></div></div>
  </div>

</div>

<!-- ÇALIŞAN EKLE/DÜZENLE MODAL -->
<div class="modal-overlay" id="calisan-modal">
  <div class="modal">
    <div class="modal-title" id="calisan-modal-baslik">Çalışan Ekle</div>
    <div class="modal-sub">Telegram ID'yi öğrenmek için çalışan @userinfobot'a /start yazsın.</div>
    <input type="hidden" id="calisan-edit-id">
    <div class="form-group">
      <label class="form-label">Telegram ID <span style="color:var(--muted);font-weight:400">(opsiyonel)</span></label>
      <input type="text" class="form-input" id="c-tid" placeholder="Boş bırakabilirsiniz — sistem doğum tarihiyle eşleştirir">
      <div style="font-size:11px;color:var(--muted);margin-top:4px">Değiştirirseniz eski eğitim kayıtları bu kişiyle ilişkilendirilemez.</div>
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
<div class="modal-overlay" id="egitim-duzenle-modal">
  <div class="modal" style="max-width:600px;width:95vw">
    <div class="modal-title">Eğitimi Düzenle</div>
    <input type="hidden" id="ed-id">
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
      <div class="form-group" style="margin:0">
        <label class="form-label">Başlık *</label>
        <input type="text" class="form-input" id="ed-baslik" placeholder="Eğitim başlığı">
      </div>
      <div class="form-group" style="margin:0">
        <label class="form-label">Tür</label>
        <input type="text" class="form-input" id="ed-tur" placeholder="örn: İş Güvenliği">
      </div>
    </div>
    <div class="form-group" style="margin-top:12px">
      <label class="form-label">Süre</label>
      <input type="text" class="form-input" id="ed-sure" placeholder="örn: ~15 dakika">
    </div>
    <div class="form-group">
      <label class="form-label">Eğitim Metni <span style="color:var(--muted);font-weight:400">(Telegram Markdown destekler, *kalın* gibi)</span></label>
      <textarea class="form-input" id="ed-metin" rows="8" style="resize:vertical;font-family:monospace;font-size:12px" placeholder="Eğitim içeriğini buraya yazın..."></textarea>
    </div>
    <div class="form-group">
      <label class="form-label">Sorular <span style="color:var(--muted);font-weight:400">(JSON formatı)</span></label>
      <textarea class="form-input" id="ed-sorular" rows="6" style="resize:vertical;font-family:monospace;font-size:11px" placeholder='[{"soru":"?","secenekler":["A","B","C","D"],"dogru":0}]'></textarea>
      <div style="font-size:11px;color:var(--muted);margin-top:4px">dogru: 0=A, 1=B, 2=C, 3=D</div>
    </div>
    <div id="ed-hata" class="alert alert-red" style="display:none"></div>
    <div style="display:flex;gap:8px;margin-top:8px">
      <button class="btn btn-primary" style="flex:1" onclick="egitimDuzenleKaydet()">Kaydet</button>
      <button class="btn btn-dark" onclick="modalKapat('egitim-duzenle-modal')">İptal</button>
    </div>
  </div>
</div>

<div class="modal-overlay" id="egitim-sec-modal">
  <div class="modal" style="max-width:520px;width:95vw">
    <div class="modal-title">Eğitim Seç</div>
    <div class="modal-sub" id="egitim-sec-calisan-adi"></div>
    <input type="hidden" id="egitim-sec-tid">
    <div style="margin:12px 0;font-size:13px;color:var(--muted)">Tamamlanmamış eğitimler:</div>
    <div id="egitim-sec-liste" style="max-height:350px;overflow-y:auto;display:flex;flex-direction:column;gap:8px"></div>
    <div id="egitim-sec-bos" style="display:none;text-align:center;padding:20px;color:var(--muted)">
      🎉 Bu çalışan tüm eğitimleri tamamlamış!
    </div>
    <div style="margin-top:16px">
      <button class="btn btn-dark" style="width:100%" onclick="modalKapat('egitim-sec-modal')">Kapat</button>
    </div>
  </div>
</div>

<div class="modal-overlay" id="firma-ekle-modal">
  <div class="modal">
    <div class="modal-title">Yeni Firma Ekle</div>
    <div class="modal-sub">Bot bu gruba eklenmiş olmalı ve grup ID'sini bilmeniz gerekiyor.</div>
    <div class="form-group">
      <label class="form-label">Firma Adı *</label>
      <input type="text" class="form-input" id="f-ad" placeholder="örn: Baştaş Avcılar">
    </div>
    <div class="form-group">
      <label class="form-label">Telegram Grup ID *</label>
      <input type="text" class="form-input" id="f-grupid" placeholder="örn: -1001234567890">
      <div style="font-size:11px;color:var(--muted);margin-top:4px">
        Grup ID'sini bulmak için gruba <code>@userinfobot</code>'u ekleyin veya Railway loglarından öğrenin.
      </div>
    </div>
    <div id="f-hata" class="alert alert-red" style="display:none"></div>
    <div style="display:flex;gap:8px;margin-top:8px">
      <button class="btn btn-primary" style="flex:1" onclick="firmaKaydet()">Kaydet</button>
      <button class="btn btn-dark" onclick="modalKapat('firma-ekle-modal')">İptal</button>
    </div>
  </div>
</div>

<div class="modal-overlay" id="manuel-egitim-modal">
  <div class="modal" style="max-width:600px;width:95vw">
    <div class="modal-title">📝 Manuel Eğitim Ekle</div>
    <div class="form-group">
      <label class="form-label">Firmalar <span style="color:var(--muted);font-weight:400">(seçilmezse tüm firmalarda görünür)</span></label>
      <div id="me-firma-secim" style="display:flex;flex-wrap:wrap;gap:8px;padding:8px;background:var(--bg);border-radius:8px;border:1px solid var(--border)">
        <div style="font-size:12px;color:var(--muted)">Yükleniyor...</div>
      </div>
    </div>
    <div class="form-group">
      <label class="form-label">Başlık *</label>
      <input type="text" class="form-input" id="me-baslik" placeholder="örn: 🔥 Yangın Güvenliği">
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
      <div class="form-group" style="margin:0">
        <label class="form-label">Tür</label>
        <input type="text" class="form-input" id="me-tur" placeholder="örn: İş Güvenliği">
      </div>
      <div class="form-group" style="margin:0">
        <label class="form-label">Süre</label>
        <input type="text" class="form-input" id="me-sure" placeholder="örn: ~10 dakika">
      </div>
    </div>
    <div class="form-group">
      <label class="form-label">Eğitim Metni * <span style="color:var(--muted);font-weight:400">(*kalın* için yıldız kullanın)</span></label>
      <textarea class="form-input" id="me-metin" rows="6" style="resize:vertical;font-size:13px" placeholder="Eğitim içeriğini buraya yazın..."></textarea>
    </div>
    <div class="form-group">
      <label class="form-label">Sorular * <span style="color:var(--muted);font-weight:400">(her satıra bir soru)</span></label>
      <div id="me-sorular-konteyner"></div>
      <button class="btn btn-dark btn-sm" style="margin-top:8px" onclick="meYeniSoruEkle()">+ Soru Ekle</button>
    </div>
    <div id="me-hata" class="alert alert-red" style="display:none"></div>
    <div style="display:flex;gap:8px;margin-top:8px">
      <button class="btn btn-primary" style="flex:1" onclick="manuelEgitimKaydet()">Kaydet</button>
      <button class="btn btn-dark" onclick="modalKapat('manuel-egitim-modal')">İptal</button>
    </div>
  </div>
</div>

<div class="modal-overlay" id="toplu-islem-modal">
  <div class="modal" style="max-width:520px;width:95vw">
    <div class="modal-title">👥 Toplu İşlem</div>
    <div class="modal-sub" id="toplu-egitim-adi"></div>
    <input type="hidden" id="toplu-egitim-id">

    <div style="margin-bottom:16px">
      <div style="font-size:12px;font-weight:700;color:var(--muted);margin-bottom:8px">KİMLER İÇİN</div>
      <div style="display:flex;flex-direction:column;gap:6px" id="toplu-calisan-liste">
        <label style="display:flex;align-items:center;gap:8px;cursor:pointer">
          <input type="radio" name="toplu-kapsam" value="hepsi" checked> <strong>Tüm çalışanlar</strong>
        </label>
        <label style="display:flex;align-items:center;gap:8px;cursor:pointer">
          <input type="radio" name="toplu-kapsam" value="secili"> Belirli çalışanlar seç
        </label>
        <div id="toplu-calisan-secim" style="display:none;padding:10px;background:var(--bg);border-radius:8px;max-height:200px;overflow-y:auto;margin-top:4px">
          Yükleniyor...
        </div>
      </div>
    </div>

    <div style="margin-bottom:16px">
      <div style="font-size:12px;font-weight:700;color:var(--muted);margin-bottom:8px">İŞLEM</div>
      <div style="display:flex;gap:10px">
        <label style="flex:1;display:flex;align-items:center;gap:8px;cursor:pointer;padding:12px;background:#e8f7f0;border:1px solid #c3e6cb;border-radius:8px">
          <input type="radio" name="toplu-islem" value="tamamlandi" checked>
          <div><div style="font-weight:700;color:var(--green)">✅ Tamamlandı</div><div style="font-size:11px;color:var(--muted)">Bu eğitimi geçmiş say</div></div>
        </label>
        <label style="flex:1;display:flex;align-items:center;gap:8px;cursor:pointer;padding:12px;background:#fdecea;border:1px solid #f5bcb8;border-radius:8px">
          <input type="radio" name="toplu-islem" value="sifirla">
          <div><div style="font-weight:700;color:var(--red)">🔄 Sıfırla</div><div style="font-size:11px;color:var(--muted)">Tekrar alması gereksin</div></div>
        </label>
      </div>
    </div>

    <div id="toplu-hata" class="alert alert-red" style="display:none"></div>
    <div style="display:flex;gap:8px;margin-top:8px">
      <button class="btn btn-primary" style="flex:1" onclick="topluIslemUygula()">Uygula</button>
      <button class="btn btn-dark" onclick="modalKapat('toplu-islem-modal')">İptal</button>
    </div>
  </div>
</div>

<div class="modal-overlay" id="davet-ekle-modal">
  <div class="modal" style="max-width:420px">
    <div class="modal-title">📱 Kişi Ekle</div>
    <div class="modal-sub">WhatsApp davet listesine kişi ekleyin.</div>
    <div class="form-group">
      <label class="form-label">Ad Soyad *</label>
      <input type="text" class="form-input" id="dv-ad" placeholder="Ahmet Yılmaz">
    </div>
    <div class="form-group">
      <label class="form-label">Telefon * <span style="color:var(--muted);font-weight:400">(05xxxxxxxxx)</span></label>
      <input type="text" class="form-input" id="dv-tel" placeholder="05321234567">
    </div>
    <div id="dv-hata" class="alert alert-red" style="display:none"></div>
    <div style="display:flex;gap:8px;margin-top:8px">
      <button class="btn btn-primary" style="flex:1" onclick="davetKaydet()">Ekle</button>
      <button class="btn btn-dark" onclick="modalKapat('davet-ekle-modal')">İptal</button>
    </div>
  </div>
</div>

<div class="modal-overlay" id="arsivle-modal">
  <div class="modal" style="max-width:380px">
    <div class="modal-title">📦 Çalışanı Arşivle</div>
    <div class="modal-sub" id="arsivle-adi-text"></div>
    <p style="font-size:14px;margin-bottom:20px">Bu çalışan arşive taşınacak. Eğitim bildirimleri duracak, tüm kayıtlar korunacak. İstediğinizde geri alabilirsiniz.</p>
    <input type="hidden" id="arsivle-tid">
    <div class="modal-footer">
      <button class="btn btn-primary" style="flex:1" onclick="calisanArsivleOnayla()">📦 Arşivle</button>
      <button class="btn btn-dark" onclick="modalKapat('arsivle-modal')">İptal</button>
    </div>
  </div>
</div>

<div class="modal-overlay" id="sil-modal">
  <div class="modal" style="max-width:380px">
    <div class="modal-title">⚠️ Kalıcı Sil</div>
    <div class="modal-sub" id="sil-adi-text"></div>
    <p style="font-size:14px;margin-bottom:20px">Bu çalışan <strong>kalıcı olarak silinecek</strong>. Eğitim kayıtları korunacak ama çalışan listeden tamamen kalkacak.<br><br>İşten ayrılan çalışanlar için <strong>📦 Arşivle</strong> butonunu kullanın.</p>
    <input type="hidden" id="sil-tid">
    <div class="modal-footer">
      <button class="btn btn-red" style="flex:1" onclick="calisanSilOnayla()">Kalıcı Sil</button>
      <button class="btn btn-dark" onclick="modalKapat('sil-modal')">İptal</button>
    </div>
  </div>
</div>

<!-- AI MODAL -->
<div class="modal-overlay" id="ai-modal">
  <div class="modal">
    <div id="ai-form">
      <div class="modal-title">✨ Yapay Zeka ile Eğitim Üret</div>
      <div class="form-group">
        <label class="form-label">Firmalar <span style="color:var(--muted);font-weight:400">(seçilmezse tüm firmalarda görünür)</span></label>
        <div id="ai-firma-secim" style="display:flex;flex-wrap:wrap;gap:8px;padding:8px;background:var(--bg);border-radius:8px;border:1px solid var(--border)">
          <div style="font-size:12px;color:var(--muted)">Yükleniyor...</div>
        </div>
      </div>
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

async function ayarKaydet(anahtar, inputId) {
  const input = document.getElementById(inputId);
  const deger = input ? input.value.trim() : '';
  if(!deger) { alert('Deger bos olamaz'); return; }
  try {
    const r = await fetch('/panel/api/ayar-kaydet', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({anahtar:anahtar, deger:deger})
    });
    const d = await r.json();
    if(d.basarili) {
      alert('Kaydedildi!');
      davetAyarlariYukle();
    } else { alert('Hata: ' + (d.hata||'Bilinmeyen')); }
  } catch(e) { alert('Baglanti hatasi: ' + e.message); }
}

async function davetAyarlariYukle() {
  try {
    const r = await fetch('/panel/api/davet-ayarlari');
    const d = await r.json();
    console.log('Ayarlar API yanit:', d);

    const gl = document.getElementById('ayar-grup-link');
    const at = document.getElementById('ayar-admin-tel');
    const glInfo = document.getElementById('ayar-grup-link-info');
    const atInfo = document.getElementById('ayar-admin-tel-info');

    if(gl && d.grup_link) { gl.value = d.grup_link; console.log('grup_link set edildi:', d.grup_link); }
    if(at && d.admin_tel) { at.value = d.admin_tel; console.log('admin_tel set edildi:', d.admin_tel); }

    if(glInfo) glInfo.textContent = d.grup_link
      ? 'Kayıtlı: ' + d.grup_link.substring(0,50) + (d.grup_link.length>50?'...':'')
      : 'Henüz kaydedilmedi';
    if(atInfo) atInfo.textContent = d.admin_tel
      ? 'Kayıtlı: ' + d.admin_tel
      : 'Henüz kaydedilmedi';
  } catch(e) {
    console.error('Ayarlar yuklenemedi:', e);
  }
}
document.getElementById('tarih-bas').value = bugun;
document.getElementById('tarih-bitis').value = bugun;

function bugunSec(){ document.getElementById('tarih-bas').value=bugun; document.getElementById('tarih-bitis').value=bugun; verileriYukle(); }
function modalKapat(id){ document.getElementById(id).classList.remove('open'); }

function sekme(ad, el) {
  document.querySelectorAll('.tab-content').forEach(t=>{
    t.classList.remove('active');
    t.style.display = '';  // inline style'i temizle
  });
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  document.getElementById('tab-'+ad).classList.add('active');
  el.classList.add('active');
  document.getElementById('filtre-bar').style.display = (ad==='calisanlar'||ad==='egitimler') ? 'none' : 'flex';
  if(ad==='calisanlar') calisanListesiYukle();
  if(ad==='egitimler') egitimListesiYukle();
  if(ad==='mesajlar') mesajLogYukle();
  if(ad==='davetler') davetListesiYukle();
}

// ── KAYITLAR ──────────────────────────────
// Aktif firma
let aktifFirma = "varsayilan";

async function firmaKartlariniYukle() {
  const konteyner = document.getElementById('firma-kartlari');
  konteyner.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
  try {
    const r = await fetch('/panel/api/firmalar-detay');
    const firmalar = await r.json();
    if(!firmalar.length) {
      konteyner.innerHTML = `<div class="egitim-kart" style="text-align:center;padding:40px;cursor:pointer" onclick="firmaEkleModalAc()">
        <div style="font-size:40px;margin-bottom:12px">➕</div>
        <div style="font-weight:700">İlk Firmayı Ekle</div>
        <div style="color:var(--muted);font-size:13px;margin-top:6px">Başlamak için bir firma ekleyin</div>
      </div>`;
      return;
    }
    konteyner.innerHTML = firmalar.map(f => `
      <div class="egitim-kart" style="cursor:pointer;transition:transform 0.15s" 
           onmouseover="this.style.transform='translateY(-2px)'" 
           onmouseout="this.style.transform=''"
           onclick="firmaAc('${f.firma_id}','${f.ad}')">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:16px">
          <div>
            <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:18px">${f.ad}</div>
            <div style="font-size:12px;color:var(--muted);margin-top:4px">Grup ID: ${f.grup_id || '—'}</div>
          </div>
          <div style="width:44px;height:44px;background:var(--accent);border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:20px">🏭</div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:16px">
          <div style="background:var(--bg);border-radius:8px;padding:10px;text-align:center">
            <div style="font-size:20px;font-weight:800;font-family:'Syne',sans-serif">${f.calisan_sayisi}</div>
            <div style="font-size:11px;color:var(--muted)">Çalışan</div>
          </div>
          <div style="background:var(--bg);border-radius:8px;padding:10px;text-align:center">
            <div style="font-size:20px;font-weight:800;font-family:'Syne',sans-serif;color:var(--green)">${f.bugun_tamamlayan}</div>
            <div style="font-size:11px;color:var(--muted)">Bugün Geçti</div>
          </div>
          <div style="background:var(--bg);border-radius:8px;padding:10px;text-align:center">
            <div style="font-size:20px;font-weight:800;font-family:'Syne',sans-serif;color:var(--accent)">${f.toplam_kayit}</div>
            <div style="font-size:11px;color:var(--muted)">Toplam Kayıt</div>
          </div>
        </div>
        <div style="display:flex;gap:8px">
          <button class="btn btn-dark btn-sm" style="flex:0 0 auto" onclick="event.stopPropagation();firmaDuzenle('${f.firma_id}','${f.ad}','${f.grup_id}')">✏️</button>
          <button class="btn btn-red btn-sm" style="flex:0 0 auto" onclick="event.stopPropagation();firmaSil('${f.firma_id}','${f.ad}')">🗑</button>
          <button class="btn btn-primary" style="flex:1" onclick="event.stopPropagation();firmaAc('${f.firma_id}','${f.ad}')">
            Yönet →
          </button>
        </div>
      </div>`).join('') + `
      <div class="egitim-kart" style="cursor:pointer;border:2px dashed var(--border);background:transparent;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:200px;transition:border-color 0.15s"
           onmouseover="this.style.borderColor='var(--accent)'" 
           onmouseout="this.style.borderColor='var(--border)'"
           onclick="firmaEkleModalAc()">
        <div style="font-size:32px;margin-bottom:8px">➕</div>
        <div style="font-weight:600;color:var(--muted)">Yeni Firma Ekle</div>
      </div>`;
  } catch(e) {
    konteyner.innerHTML = '<div class="empty"><div class="empty-icon">⚠️</div>Yüklenemedi: ' + e.message + '</div>';
  }
}

async function firmaSil(firma_id, ad) {
  if(!confirm(`"${ad}" firmasını silmek istediğinizden emin misiniz?

Not: Sheets'teki veriler silinmez, sadece listeden çıkarılır.`)) return;
  try {
    const r = await fetch('/panel/api/firma-sil', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({firma_id})
    });
    const d = await r.json();
    if(d.basarili) { anaSeyfayaDon(); }
    else { alert('Hata: ' + (d.hata||'')); }
  } catch(e) { alert('Bağlantı hatası'); }
}

function firmaDuzenle(firma_id, ad, grup_id) {
  document.getElementById('f-ad').value = ad;
  document.getElementById('f-grupid').value = grup_id || '';
  document.getElementById('f-hata').style.display = 'none';
  // Modal basligini degistir
  document.querySelector('#firma-ekle-modal .modal-title').textContent = 'Firmayı Düzenle';
  // Kaydet butonunu guncelle
  const btn = document.querySelector('#firma-ekle-modal .btn-primary');
  btn.onclick = () => firmaGuncelle(firma_id);
  document.getElementById('firma-ekle-modal').classList.add('open');
}

async function firmaGuncelle(firma_id) {
  const ad = document.getElementById('f-ad').value.trim();
  const grup_id = document.getElementById('f-grupid').value.trim();
  const hataEl = document.getElementById('f-hata');
  if(!ad) { hataEl.textContent='Firma adı zorunlu'; hataEl.style.display='block'; return; }

  try {
    const r = await fetch('/panel/api/firma-guncelle', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({firma_id, ad, grup_id})
    });
    const d = await r.json();
    if(d.basarili) {
      modalKapat('firma-ekle-modal');
      document.querySelector('#firma-ekle-modal .modal-title').textContent = 'Yeni Firma Ekle';
      document.querySelector('#firma-ekle-modal .btn-primary').onclick = firmaKaydet;
      anaSeyfayaDon();
    } else {
      hataEl.textContent = 'Hata: ' + (d.hata||'');
      hataEl.style.display = 'block';
    }
  } catch(e) {
    hataEl.textContent = 'Bağlantı hatası';
    hataEl.style.display = 'block';
  }
}

function firmaAc(firma_id, firma_adi) {
  // 1. Aktif firmay set et
  aktifFirma = firma_id;
  try {
    sessionStorage.setItem('aktifFirma', firma_id);
    sessionStorage.setItem('aktifFirmaAdi', firma_adi);
  } catch(e) {}

  // 2. Ana sayfayi gizle, panel sekmelerini goster
  document.getElementById('ana-sayfa').style.display = 'none';
  document.getElementById('filtre-bar').style.display = 'none';
  document.getElementById('ana-tabs').style.display = 'flex';
  document.getElementById('geri-btn').style.display = 'inline-flex';
  document.getElementById('aktif-firma-adi').textContent = firma_adi;
  document.getElementById('aktif-firma-adi').style.display = 'inline';

  // 3. Tum tab iceriklerini gizle, style temizle
  document.querySelectorAll('.tab-content').forEach(t => {
    t.classList.remove('active');
    t.style.display = '';
  });
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));

  // 4. Kayitlar sekmesini aktif yap
  const ilkTab = document.querySelector('.tab');
  const kayitlarTab = document.getElementById('tab-kayitlar');
  if(ilkTab) ilkTab.classList.add('active');
  if(kayitlarTab) kayitlarTab.classList.add('active');
  document.getElementById('filtre-bar').style.display = 'flex';

  // 5. Veriyi yukle
  verileriYukle();
}

function anaSeyfayaDon() {
  try {
    sessionStorage.removeItem('aktifFirma');
    sessionStorage.removeItem('aktifFirmaAdi');
  } catch(e) {}
  aktifFirma = null;

  document.getElementById('ana-tabs').style.display = 'none';
  document.getElementById('filtre-bar').style.display = 'none';
  document.getElementById('ana-sayfa').style.display = 'block';
  if(document.getElementById('geri-btn')) document.getElementById('geri-btn').style.display = 'none';
  if(document.getElementById('aktif-firma-adi')) document.getElementById('aktif-firma-adi').style.display = 'none';
  document.querySelectorAll('.tab-content').forEach(t => {
    t.classList.remove('active');
    t.style.display = '';
  });
  // Firma kartlarini yukle
  fetch('/panel/api/firmalar-detay')
    .then(r => r.json())
    .then(firmalar => {
      const k = document.getElementById('firma-kartlari');
      if(!k) return;
      if(!firmalar.length) {
        k.innerHTML = `<div class="egitim-kart" style="text-align:center;padding:40px;cursor:pointer;grid-column:1/-1" onclick="firmaEkleModalAc()">
          <div style="font-size:40px;margin-bottom:12px">➕</div>
          <div style="font-weight:700">İlk Firmayı Ekle</div>
        </div>`;
        return;
      }
      k.innerHTML = firmalar.map(f => `
        <div class="egitim-kart" style="cursor:pointer" onclick="firmaAc('${f.firma_id}','${f.ad}')">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:16px">
            <div>
              <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:18px">${f.ad}</div>
              <div style="font-size:12px;color:var(--muted);margin-top:4px">Grup ID: ${f.grup_id||'—'}</div>
            </div>
            <div style="width:44px;height:44px;background:var(--accent);border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:20px">🏭</div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:16px">
            <div style="background:var(--bg);border-radius:8px;padding:10px;text-align:center">
              <div style="font-size:20px;font-weight:800;font-family:'Syne',sans-serif">${f.calisan_sayisi}</div>
              <div style="font-size:11px;color:var(--muted)">Çalışan</div>
            </div>
            <div style="background:var(--bg);border-radius:8px;padding:10px;text-align:center">
              <div style="font-size:20px;font-weight:800;font-family:'Syne',sans-serif;color:var(--green)">${f.bugun_tamamlayan}</div>
              <div style="font-size:11px;color:var(--muted)">Bugün Geçti</div>
            </div>
            <div style="background:var(--bg);border-radius:8px;padding:10px;text-align:center">
              <div style="font-size:20px;font-weight:800;font-family:'Syne',sans-serif;color:var(--accent)">${f.toplam_kayit}</div>
              <div style="font-size:11px;color:var(--muted)">Toplam Kayıt</div>
            </div>
          </div>
          <div style="display:flex;gap:8px">
            <button class="btn btn-dark btn-sm" onclick="event.stopPropagation();firmaDuzenle('${f.firma_id}','${f.ad}','${f.grup_id}')">✏️</button>
            <button class="btn btn-red btn-sm" onclick="event.stopPropagation();firmaSil('${f.firma_id}','${f.ad}')">🗑</button>
            <button class="btn btn-primary" style="flex:1" onclick="event.stopPropagation();firmaAc('${f.firma_id}','${f.ad}')">Yönet →</button>
          </div>
        </div>`).join('') +
        `<div class="egitim-kart" style="cursor:pointer;border:2px dashed var(--border);background:transparent;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:200px"
             onclick="firmaEkleModalAc()">
          <div style="font-size:32px;margin-bottom:8px">➕</div>
          <div style="font-weight:600;color:var(--muted)">Yeni Firma Ekle</div>
        </div>`;
    })
    .catch(e => {
      const k = document.getElementById('firma-kartlari');
      if(k) k.innerHTML = '<div class="empty"><div class="empty-icon">⚠️</div>Yüklenemedi: '+e.message+'</div>';
    });
}

function firmaEkleModalAc() {
  document.getElementById('f-ad').value = '';
  document.getElementById('f-grupid').value = '';
  document.getElementById('f-hata').style.display = 'none';
  // Baslik ve butonu sifirla (duzenle modundan geliyorsa)
  document.querySelector('#firma-ekle-modal .modal-title').textContent = 'Yeni Firma Ekle';
  const btn = document.querySelector('#firma-ekle-modal .btn.btn-primary');
  btn.onclick = firmaKaydet;
  document.getElementById('firma-ekle-modal').classList.add('open');
}

async function firmaKaydet() {
  const ad = document.getElementById('f-ad').value.trim();
  const grupid = document.getElementById('f-grupid').value.trim();
  const hataEl = document.getElementById('f-hata');
  if(!ad || !grupid) {
    hataEl.textContent = 'Tüm alanları doldurun.';
    hataEl.style.display = 'block';
    return;
  }
  try {
    const r = await fetch('/panel/api/firma-ekle', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ad, grup_id: grupid})
    });
    const d = await r.json();
    if(d.basarili) {
      modalKapat('firma-ekle-modal');
      anaSeyfayaDon();
      alert(`"${ad}" firması eklendi! Sheets'te sekmeler otomatik oluşturuldu.`);
    } else {
      hataEl.textContent = 'Hata: ' + (d.hata || 'Bilinmeyen');
      hataEl.style.display = 'block';
    }
  } catch(e) {
    hataEl.textContent = 'Bağlantı hatası';
    hataEl.style.display = 'block';
  }
}

async function verileriYukle() {
  const bas = document.getElementById('tarih-bas').value.split('-').reverse().join('.');
  const bitis = document.getElementById('tarih-bitis').value.split('-').reverse().join('.');
  const durum = document.getElementById('durum-f').value;
  document.getElementById('kayit-tb').innerHTML='<tr><td colspan="8"><div class="loading"><div class="spinner"></div>Yükleniyor...</div></td></tr>';
  document.getElementById('egitim-stats').innerHTML='<div class="loading"><div class="spinner"></div></div>';
  try {
    const r = await fetch(`/panel/api/kayitlar?bas=${bas}&bitis=${bitis}&durum=${encodeURIComponent(durum)}&firma_id=${aktifFirma}`);
    const d = await r.json();
    renderKayitlar(d.kayitlar);
    renderIstatistik(d.egitim_ozet);
  } catch(e) {
    document.getElementById('kayit-tb').innerHTML='<tr><td colspan="8"><div class="empty"><div class="empty-icon">⚠️</div>Yüklenemedi</div></td></tr>';
  }
}

function renderKayitlar(kayitlarHam) {
  // En yeni ustte
  const kayitlar = [...kayitlarHam].reverse();
  const t=kayitlar.length, g=kayitlar.filter(k=>k.durum==='GEÇTİ'||k.durum==='GECTI').length, k=t-g;
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
let tumMesajlar = [];

async function mesajLogYukle() {
  document.getElementById('mesaj-log-liste').innerHTML = '<div class="loading"><div class="spinner"></div>Yükleniyor...</div>';
  try {
    const r = await fetch('/panel/api/mesaj-loglari');
    tumMesajlar = await r.json();
    mesajFiltrele();
  } catch(e) {
    document.getElementById('mesaj-log-liste').innerHTML = '<div class="empty"><div class="empty-icon">⚠️</div>Yüklenemedi</div>';
  }
}

function mesajFiltrele() {
  const filtre = (document.getElementById('mesaj-filtre')?.value || '').toLowerCase();
  const liste = filtre
    ? tumMesajlar.filter(m => m.ad.toLowerCase().includes(filtre) || m.mesaj.toLowerCase().includes(filtre))
    : tumMesajlar;

  if(!liste.length) {
    document.getElementById('mesaj-log-liste').innerHTML = '<div class="empty"><div class="empty-icon">💬</div>Mesaj yok</div>';
    return;
  }

  document.getElementById('mesaj-log-liste').innerHTML = `
    <table style="width:100%;border-collapse:collapse">
      <thead>
        <tr style="border-bottom:2px solid var(--border);text-align:left">
          <th style="padding:10px 12px;font-size:12px;color:var(--muted)">Saat</th>
          <th style="padding:10px 12px;font-size:12px;color:var(--muted)">Kişi</th>
          <th style="padding:10px 12px;font-size:12px;color:var(--muted)">Telegram ID</th>
          <th style="padding:10px 12px;font-size:12px;color:var(--muted)">Mesaj</th>
          <th style="padding:10px 12px;font-size:12px;color:var(--muted)">Durum</th>
        </tr>
      </thead>
      <tbody>
        ${liste.slice().reverse().map(m => `
          <tr style="border-bottom:1px solid var(--border)">
            <td style="padding:8px 12px;font-size:12px;color:var(--muted);white-space:nowrap">${m.zaman}</td>
            <td style="padding:8px 12px;font-size:13px;font-weight:600">${m.ad}<br><span style="font-size:11px;color:var(--muted);font-weight:400">${m.username||''}</span></td>
            <td style="padding:8px 12px;font-size:11px;font-family:monospace;color:var(--muted)">${m.user_id}</td>
            <td style="padding:8px 12px;font-size:13px;max-width:300px;overflow:hidden;text-overflow:ellipsis">${m.mesaj}</td>
            <td style="padding:8px 12px">
              ${m.kayitli
                ? '<span style="color:var(--green);font-size:12px">✅ Kayıtlı</span>'
                : '<span style="color:#e67e22;font-size:12px">⚠ Kayıtsız</span>'}
            </td>
          </tr>`).join('')}
      </tbody>
    </table>`;
}

async function manuelUyeEkle() {
  const uid = parseInt(document.getElementById('manuel-uid').value);
  if(!uid || isNaN(uid)) { alert('Gecerli bir Telegram ID girin'); return; }
  try {
    const r = await fetch('/panel/api/bekleyen-manuel-ekle', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({user_id: uid})
    });
    const d = await r.json();
    if(d.basarili) {
      document.getElementById('manuel-uid').value = '';
      bekleyenleriYukle();
    } else {
      alert(d.mesaj || d.hata || 'Hata olustu');
    }
  } catch(e) {
    alert('Baglanti hatasi: ' + e.message);
  }
}

async function bekleyenleriYukle() {
  document.getElementById('bekleyen-liste').innerHTML = '<div class="loading"><div class="spinner"></div>Yükleniyor...</div>';
  try {
    const r = await fetch('/panel/api/bekleyenler');
    const d = await r.json();
    const sayi = document.getElementById('bekleyen-sayi');
    if(d.length > 0) {
      sayi.textContent = d.length;
      sayi.style.display = 'inline';
    } else {
      sayi.style.display = 'none';
    }
    if(!d.length) {
      document.getElementById('bekleyen-liste').innerHTML = '<div class="empty"><div class="empty-icon">✅</div>Tüm grup üyeleri sisteme kayıtlı.</div>';
      return;
    }
    document.getElementById('bekleyen-liste').innerHTML = d.map(u => `
      <div class="calisan-kart">
        <div class="calisan-kart-header">
          <div>
            <div class="calisan-ad">${u.ad}</div>
            <div class="calisan-gorev" style="color:var(--muted)">${u.username || '—'}</div>
            <div class="calisan-id">ID: ${u.user_id}</div>
          </div>
          <div class="calisan-aksiyonlar">
            <button class="btn btn-primary btn-sm" onclick="bekleyenEkleModalAc(${u.user_id},'${u.ad.replace(/'/g,"\'")}')">✅ Sisteme Ekle</button>
            <button class="btn btn-dark btn-sm" onclick="bekleyenBildir(${u.user_id},'${u.ad.replace(/'/g,"\'")}',this)">📨 Eğitim Daveti Gönder</button>
          </div>
        </div>
      </div>`).join('');
  } catch(e) {
    document.getElementById('bekleyen-liste').innerHTML = '<div class="empty"><div class="empty-icon">⚠️</div>Yüklenemedi: ' + e.message + '</div>';
  }
}

function bekleyenEkleModalAc(userId, ad) {
  // Calisan ekleme modalini ac, ID dolu gelsin
  document.getElementById('calisan-modal-baslik').textContent = 'Çalışan Ekle';
  document.getElementById('calisan-edit-id').value = '';
  document.getElementById('c-tid').value = userId;
  document.getElementById('c-tid').disabled = false;
  document.getElementById('c-ad').value = ad;
  document.getElementById('c-gorev').value = '';
  document.getElementById('c-dogum').value = '';
  document.getElementById('calisan-hata').style.display = 'none';
  document.getElementById('calisan-modal').classList.add('open');
}

async function bekleyenBildir(userId, ad, btn) {
  btn.textContent = '⏳'; btn.disabled = true;
  try {
    const r = await fetch('/panel/api/bekleyen-bildir', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({user_id: userId, ad: ad})
    });
    const d = await r.json();
    if(d.basarili) {
      btn.textContent = '✅ Gönderildi';
      btn.style.background = 'var(--green,#27ae60)';
      setTimeout(() => { btn.textContent = '📨 Eğitim Daveti Gönder'; btn.style.background=''; btn.disabled=false; }, 3000);
    } else {
      alert('Hata: ' + (d.hata||''));
      btn.textContent = '📨 Eğitim Daveti Gönder'; btn.disabled = false;
    }
  } catch(e) {
    alert('Bağlantı hatası');
    btn.textContent = '📨 Eğitim Daveti Gönder'; btn.disabled = false;
  }
}

async function calisanListesiYukle() {
  document.getElementById('calisan-liste').innerHTML='<div class="loading"><div class="spinner"></div></div>';
  try {
    const r = await fetch(`/panel/api/calisanlar?firma_id=${aktifFirma}`);
    const resp = await r.json();
    const d = Array.isArray(resp) ? resp : resp.calisanlar;
    window._botUsername = Array.isArray(resp) ? 'BasTasEgitimBot' : (resp.bot_username || 'BasTasEgitimBot');
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
          <div class="calisan-ad">
            ${c.ad_soyad}
            ${c.bugun_izinli ? '<span class="pill pill-izin">🏖 Bugün İzinli</span>' : ''}
            ${c.bugun_tamamladi ? '<span class="pill pill-gecti">✅ Bugün Tamamladı</span>' : ''}
          </div>
          <div class="calisan-gorev">${c.gorev}</div>
          ${c.telegram_id > 0 ? `<div class="calisan-id">ID: ${c.telegram_id}</div>` : '<div class="calisan-id" style="color:#e67e22">⚠ Telegram bağlı değil</div>'}
        </div>
        <div class="calisan-aksiyonlar">
          <button class="btn btn-primary btn-sm" onclick="egitimSecModalAc(${c.telegram_id},'${c.ad_soyad}',this)" ${c.telegram_id<=0?'disabled':''} title="Eğitim seç ve gönder">📤 Eğitim Gönder</button>
          <button class="btn btn-orange btn-sm" onclick="ekstraHakVer(${c.telegram_id},'${c.ad_soyad}',this)" ${c.telegram_id<=0?'disabled':''} title="Bugün tekrar girebilsin">🔁 Tekrar İzni</button>
          <button class="btn btn-green btn-sm" onclick="izinModalAc(${c.telegram_id},'${c.ad_soyad}')">🏖 İzin</button>
          <button class="btn btn-dark btn-sm" onclick="calisanDuzenle(${c.telegram_id},'${c.ad_soyad}','${c.gorev}','${c.dogum_tarihi}')">✏️</button>
          <button class="btn btn-dark btn-sm" onclick="arsivleModalAc(${c.telegram_id},'${c.ad_soyad}')">📦</button>
          <button class="btn btn-red btn-sm" onclick="silModalAc(${c.telegram_id},'${c.ad_soyad}')">🗑</button>
        </div>
      </div>
      <div class="calisan-ilerleme">
        <div style="display:flex;justify-content:space-between;align-items:center;font-size:12px;color:var(--muted);margin-bottom:6px">
          <span>Eğitim İlerlemesi</span>
          <div style="display:flex;gap:12px;align-items:center">
            <span title="Geçilen eğitim sayısı">✅ ${c.tamamlanan}/${c.toplam_egitim} geçti</span>
            <span title="Toplam katıldığı eğitim sayısı (geçti+kaldı)">📋 ${c.toplam_alinmis} katılım</span>
            ${c.son_egitim ? `<span title="Son eğitim tarihi">🗓 ${c.son_egitim}</span>` : ''}
            <button class="btn btn-dark" style="font-size:11px;padding:2px 8px;border-radius:6px" onclick="egitimDetayGoster(${c.telegram_id},'${c.ad_soyad}',this)">Detay</button>
          </div>
        </div>
        <div class="ilerleme-bar"><div class="ilerleme-dolu" style="width:${c.toplam_egitim?Math.round(c.tamamlanan/c.toplam_egitim*100):0}%"></div></div>
        <div id="detay-${c.telegram_id}" style="display:none;margin-top:10px"></div>
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
  const tidGercek = (!tid || tid <= 0) ? '' : tid;
  document.getElementById('c-tid').value = tidGercek;
  document.getElementById('c-tid').disabled = false;
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

  if(!ad||!gorev||!dogum){hataEl.textContent='Ad, görev ve doğum tarihi zorunludur.';hataEl.style.display='block';return;}
  if(!/^\d{2}\.\d{2}\.\d{4}$/.test(dogum)){hataEl.textContent='Doğum tarihi GG.AA.YYYY formatında olmalı.';hataEl.style.display='block';return;}

  const endpoint = editId ? '/panel/api/calisan-guncelle' : '/panel/api/calisan-ekle';
  try {
    const tidVal = tid ? parseInt(tid) : null;
    const r = await fetch(endpoint, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({telegram_id:tidVal,ad_soyad:ad,gorev,dogum_tarihi:dogum})});
    const d = await r.json();
    if(d.basarili){modalKapat('calisan-modal');calisanListesiYukle();}
    else{hataEl.textContent=d.hata||'Hata oluştu.';hataEl.style.display='block';}
  } catch(e){hataEl.textContent='Bağlantı hatası.';hataEl.style.display='block';}
}

// ── DAVETLER ─────────────────────────────

async function davetListesiYukle() {
  document.getElementById('davet-liste').innerHTML = '<div class="loading"><div class="spinner"></div></div>';
  const firma = aktifFirma || 'varsayilan';
  try {
    const url = '/panel/api/davetler?firma_id=' + firma;
    console.log('Davet URL:', url);
    const r = await fetch(url);
    const metin = await r.text();
    console.log('Davet API yanit:', metin.substring(0,200));
    let veri;
    try { veri = JSON.parse(metin); } catch(pe) {
      document.getElementById('davet-liste').innerHTML = '<div class="empty"><div class="empty-icon">⚠️</div>JSON parse hatasi: ' + metin.substring(0,100) + '</div>';
      return;
    }
    if(!r.ok || (veri && veri.hata)) {
      document.getElementById('davet-liste').innerHTML = '<div class="empty"><div class="empty-icon">⚠️</div>API Hatasi: ' + (veri.hata||r.status) + '</div>';
      return;
    }
    const liste = Array.isArray(veri) ? veri : [];
    console.log('Davet sayisi:', liste.length);
    // Render
    const el = document.getElementById('davet-liste');
    if(!el) { console.error('davet-liste bulunamadi'); return; }
    if(!liste.length) {
      el.innerHTML = '<div class="empty"><div class="empty-icon">📱</div><div>Henüz kimse eklenmemiş</div><button class="btn btn-primary" style="margin-top:16px" onclick="davetEkleModalAc()">+ İlk Kişiyi Ekle</button></div>';
      return;
    }
    const tbody = document.createElement('tbody');
    for(const d of liste) {
      const durum_renk = d.durum==='katildi'?'var(--green)':d.durum==='gonderildi'?'var(--yellow)':'var(--muted)';
      const durum_etiket = d.durum==='katildi'?'✅ Katıldı':d.durum==='gonderildi'?'📨 Gönderildi':'⏳ Bekliyor';
      const gonder_label = d.durum==='gonderildi' ? '↩ Tekrar' : '📨 Gönder';
      const tr = document.createElement('tr');
      tr.innerHTML = '<td><strong>' + d.ad_soyad + '</strong></td>'
        + '<td style="font-family:monospace">' + d.telefon + '</td>'
        + '<td><span style="color:' + durum_renk + ';font-weight:600">' + durum_etiket + '</span></td>'
        + '<td style="color:var(--muted)">' + (d.davet_tarihi||'—') + '</td>'
        + '<td style="color:var(--muted)">' + (d.katilma_tarihi||'—') + '</td>'
        + '<td></td>';
      const td = tr.lastChild;
      const div = document.createElement('div');
      div.style.display = 'flex'; div.style.gap = '6px';
      if(d.durum !== 'katildi') {
        const gBtn = document.createElement('button');
        gBtn.className = 'btn btn-primary btn-sm';
        gBtn.textContent = gonder_label;
        gBtn.onclick = (function(sn,ad,tel,tok){return function(e){davetGonder(sn,ad,tel,tok,e.target);};})(d.satir_no,d.ad_soyad,d.telefon,d.token);
        div.appendChild(gBtn);
      }
      const sBtn = document.createElement('button');
      sBtn.className = 'btn btn-red btn-sm'; sBtn.textContent = '🗑';
      sBtn.onclick = (function(sn){return function(e){davetSil(sn,e.target);};})(d.satir_no);
      div.appendChild(sBtn); td.appendChild(div); tbody.appendChild(tr);
    }
    const tbl = document.createElement('table');
    tbl.innerHTML = '<thead><tr><th>Ad Soyad</th><th>Telefon</th><th>Durum</th><th>Davet Tarihi</th><th>Katılma</th><th>İşlem</th></tr></thead>';
    tbl.appendChild(tbody);
    const wrap = document.createElement('div'); wrap.className = 'table-wrap';
    wrap.appendChild(tbl); el.innerHTML = ''; el.appendChild(wrap);
  } catch(e) {
    document.getElementById('davet-liste').innerHTML = '<div class="empty"><div class="empty-icon">⚠️</div>Yüklenemedi</div>';
  }
}


function davetEkleModalAc() {
  document.getElementById('dv-ad').value = '';
  document.getElementById('dv-tel').value = '';
  document.getElementById('dv-hata').style.display = 'none';
  document.getElementById('davet-ekle-modal').classList.add('open');
}

async function davetKaydet() {
  const ad = document.getElementById('dv-ad').value.trim();
  const tel = document.getElementById('dv-tel').value.trim();
  const hataEl = document.getElementById('dv-hata');
  if(!ad || !tel) { hataEl.textContent='Ad ve telefon zorunludur.'; hataEl.style.display='block'; return; }
  try {
    const r = await fetch('/panel/api/davet-ekle', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ad_soyad:ad, telefon:tel, firma_id:aktifFirma})
    });
    const d = await r.json();
    if(d.basarili) { modalKapat('davet-ekle-modal'); davetListesiYukle(); }
    else { hataEl.textContent = d.hata || 'Hata'; hataEl.style.display='block'; }
  } catch(e) { hataEl.textContent='Bağlantı hatası'; hataEl.style.display='block'; }
}

async function davetGonder(satirNo, adSoyad, telefon, token, btn) {
  if(btn.textContent.includes('Tekrar')) {
    if(!confirm('"'+adSoyad+'" kişisine daha önce davet gönderildi. Tekrar göndermek istiyor musunuz?')) return;
  }

  // Grup davet linkini al
  const grupR = await fetch(`/panel/api/firma-grup-linki?firma_id=${aktifFirma}`);
  const grupD = await grupR.json();
  const grupLink = grupD.link || 'https://t.me/+GRUP_DAVET_LINKI';
  const botUsername = grupD.bot_username || 'toolbox_egitim_bot';

  const mesaj = encodeURIComponent(
    'Merhaba ' + adSoyad + ',' + '\n' +
    '\n' +
    'Is basi egitim sistemine davet edildiniz.' + '\n' +
    '\n' +
    'Katilmak icin:' + '\n' +
    '1. Telegram yuklu degilse once yukleyin: https://telegram.org/dl' + '\n' +
    '\n' +
    '2. Gruba katilmak icin tiklayin: ' + grupLink + '\n' +
    '\n' +
    'Sorun yasarsaniz yoneticinizle iletisime gecin.'
  );

  // WhatsApp linkini ac
  const waLink = 'https://wa.me/' + telefon.replace(/[^0-9]/g,'') + '?text=' + mesaj;
  window.open(waLink, '_blank');

  // Gonderildi olarak isaretle
  await fetch('/panel/api/davet-gonderildi', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({satir_no: satirNo, firma_id: aktifFirma})
  });
  davetListesiYukle();
}

async function davetSil(satirNo, btn) {
  if(!confirm('Bu kişiyi listeden kaldırmak istiyor musunuz?')) return;
  btn.textContent = '⏳'; btn.disabled = true;
  try {
    const r = await fetch('/panel/api/davet-sil', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({satir_no: satirNo, firma_id: aktifFirma})
    });
    const d = await r.json();
    if(d.basarili) davetListesiYukle();
    else { alert('Hata: '+(d.hata||'')); btn.textContent='🗑'; btn.disabled=false; }
  } catch(e) { alert('Bağlantı hatası'); btn.textContent='🗑'; btn.disabled=false; }
}

// ── ARŞİV ────────────────────────────────
let calisanMod = 'aktif';

function calisanModGec(mod) {
  calisanMod = mod;
  document.getElementById('btn-aktif').className = 'btn btn-sm' + (mod==='aktif' ? ' btn-dark' : '');
  document.getElementById('btn-aktif').style.background = mod==='aktif' ? '' : 'transparent';
  document.getElementById('btn-aktif').style.color = mod==='aktif' ? '' : 'var(--muted)';
  document.getElementById('btn-arsiv').className = 'btn btn-sm' + (mod==='arsiv' ? ' btn-dark' : '');
  document.getElementById('btn-arsiv').style.background = mod==='arsiv' ? '' : 'transparent';
  document.getElementById('btn-arsiv').style.color = mod==='arsiv' ? '' : 'var(--muted)';
  document.getElementById('aktif-butonlar').style.display = mod==='aktif' ? 'flex' : 'none';
  if(mod === 'arsiv') arsivListesiYukle();
  else calisanListesiYukle();
}

async function arsivListesiYukle() {
  document.getElementById('calisan-liste').innerHTML = '<div class="loading"><div class="spinner"></div></div>';
  try {
    const r = await fetch(`/panel/api/arsiv-calisanlar?firma_id=${aktifFirma}`);
    const liste = await r.json();
    if(!liste.length) {
      document.getElementById('calisan-liste').innerHTML = '<div class="empty"><div class="empty-icon">📦</div>Arşivde çalışan yok</div>';
      return;
    }
    document.getElementById('calisan-liste').innerHTML = liste.map(c => `
      <div class="calisan-kart" style="opacity:0.85;border-left:3px solid var(--muted)">
        <div class="calisan-kart-header">
          <div>
            <div class="calisan-ad">${c.ad_soyad} <span style="font-size:11px;background:#f0ede8;padding:2px 8px;border-radius:4px;color:var(--muted)">📦 Arşiv</span></div>
            <div class="calisan-gorev">${c.gorev}</div>
            <div class="calisan-id">Arşivlenme: ${c.arsiv_tarihi || '—'}</div>
          </div>
          <div style="display:flex;gap:6px">
            <button class="btn btn-green btn-sm" onclick="arsivdenAlOnayla(${c.telegram_id},'${c.ad_soyad}',this)">↩ Geri Al</button>
            <button class="btn btn-dark btn-sm" onclick="arsivDetayGoster(${c.telegram_id},this)">📋 Detay</button>
          </div>
        </div>
        <div style="margin-top:12px;padding-top:12px;border-top:1px solid var(--border);display:flex;gap:20px;font-size:12px;color:var(--muted)">
          <span>✅ ${c.gecilen_egitim} eğitim geçti</span>
          <span>📋 ${c.toplam_katilim} katılım</span>
          <span>🗓 Son: ${c.son_egitim || '—'}</span>
        </div>
        <div id="arsiv-detay-${c.telegram_id}" style="display:none;margin-top:10px;padding:10px;background:var(--bg);border-radius:8px;font-size:12px">
          ${c.gecilen_liste.length ? '<div style="font-weight:700;margin-bottom:6px">Geçilen Eğitimler:</div>' + c.gecilen_liste.map(e => '<div style="padding:2px 0">✅ '+e+'</div>').join('') : '<div style="color:var(--muted)">Henüz geçilen eğitim yok</div>'}
        </div>
      </div>`).join('');
  } catch(e) {
    document.getElementById('calisan-liste').innerHTML = '<div class="empty"><div class="empty-icon">⚠️</div>Yüklenemedi</div>';
  }
}

function arsivDetayGoster(tid, btn) {
  const div = document.getElementById('arsiv-detay-' + tid);
  const acik = div.style.display !== 'none';
  div.style.display = acik ? 'none' : 'block';
  btn.textContent = acik ? '📋 Detay' : '🔼 Gizle';
}

function arsivleModalAc(tid, ad) {
  document.getElementById('arsivle-tid').value = tid;
  document.getElementById('arsivle-adi-text').textContent = '"' + ad + '" arşivlenecek.';
  document.getElementById('arsivle-modal').classList.add('open');
}

async function calisanArsivleOnayla() {
  const tid = document.getElementById('arsivle-tid').value;
  try {
    const r = await fetch('/panel/api/calisan-arsivle', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({telegram_id: parseInt(tid), firma_id: aktifFirma})
    });
    const d = await r.json();
    if(d.basarili) { modalKapat('arsivle-modal'); calisanListesiYukle(); }
    else { alert('Hata: ' + (d.hata||'')); }
  } catch(e) { alert('Bağlantı hatası'); }
}

async function arsivdenAlOnayla(tid, ad, btn) {
  if(!confirm('"' + ad + '" aktif listeye geri alınsın mı?')) return;
  btn.textContent = '⏳'; btn.disabled = true;
  try {
    const r = await fetch('/panel/api/calisan-arsivden-al', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({telegram_id: tid, firma_id: aktifFirma})
    });
    const d = await r.json();
    if(d.basarili) { calisanModGec('aktif'); }
    else { alert('Hata: ' + (d.hata||'')); btn.textContent = '↩ Geri Al'; btn.disabled = false; }
  } catch(e) { alert('Bağlantı hatası'); btn.textContent = '↩ Geri Al'; btn.disabled = false; }
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
    const r = await fetch(`/panel/api/egitimler?firma_id=${aktifFirma||''}`);
    renderEgitimler(await r.json());
  } catch(e) { document.getElementById('egitim-liste').innerHTML='<div class="empty"><div class="empty-icon">⚠️</div>Yüklenemedi</div>'; }
}

function renderEgitimler(egitimler) {
  if(!egitimler.length){document.getElementById('egitim-liste').innerHTML='<div class="empty"><div class="empty-icon">📚</div>Eğitim yok</div>';return;}
  document.getElementById('egitim-liste').innerHTML=egitimler.map(e=>`
    <div class="egitim-kart" id="ekart-${e.id}">
      <div class="egitim-kart-header">
        <div><div class="egitim-kart-baslik">${e.baslik}</div><span class="egitim-tur">${e.tur}</span></div>
        <div style="font-size:12px;color:var(--muted);white-space:nowrap">${e.sure} · ${e.soru_sayisi} soru</div>
      </div>
      <div class="egitim-kart-body">${e.metin_onizleme}</div>
      ${e.firma_etiketi ? `<div style="font-size:11px;color:var(--muted);margin-top:6px">🏭 ${e.firma_etiketi}</div>` : '<div style="font-size:11px;color:var(--muted);margin-top:6px">🌐 Tüm firmalar</div>'}
      <div class="egitim-kart-footer">
        <div style="display:flex;gap:8px;flex-wrap:wrap">
          <button class="btn btn-primary btn-sm" onclick="egitimGonder('${e.id}', this)">▶️ Şimdi Gönder</button>
          <button class="btn btn-dark btn-sm" onclick="egitimDetayAl('${e.id}',this)">✏️ Düzenle</button>
          <button class="btn btn-green btn-sm" onclick="topluIslemModalAc('${e.id}','${e.baslik}')">👥 Toplu</button>
          <button class="btn btn-red btn-sm" onclick="egitimSil('${e.id}','${e.baslik.replace(/'/g,"\'")}',this)">🗑 Sil</button>
        </div>
      </div>
    </div>`).join('');
}

// ── MANUEL EGITIM ────────────────────────
let meSoruSayisi = 0;

function firmaSecimDoldur(konteyner_id) {
  const div = document.getElementById(konteyner_id);
  if(!div) return;
  fetch('/panel/api/firmalar-detay')
    .then(r => r.json())
    .then(firmalar => {
      div.innerHTML = firmalar.map(f => `
        <label style="display:flex;align-items:center;gap:6px;cursor:pointer;padding:4px 10px;background:var(--card);border:1px solid var(--border);border-radius:6px;font-size:12px">
          <input type="checkbox" name="${konteyner_id}-firma" value="${f.firma_id}"> ${f.ad}
        </label>`).join('');
    })
    .catch(() => { div.innerHTML = '<div style="font-size:12px;color:var(--muted)">Yüklenemedi</div>'; });
}

function seciliFirmalariAl(konteyner_id) {
  return Array.from(document.querySelectorAll(`#${konteyner_id} input[type=checkbox]:checked`))
    .map(cb => cb.value);
}

function manuelEgitimModalAc() {
  document.getElementById('me-baslik').value = '';
  document.getElementById('me-tur').value = 'Is Guvenligi';
  document.getElementById('me-sure').value = '~10 dakika';
  document.getElementById('me-metin').value = '';
  document.getElementById('me-hata').style.display = 'none';
  meSoruSayisi = 0;
  document.getElementById('me-sorular-konteyner').innerHTML = '';
  // 3 bos soru ile baslat
  meYeniSoruEkle();
  meYeniSoruEkle();
  meYeniSoruEkle();
  firmaSecimDoldur('me-firma-secim');
  document.getElementById('manuel-egitim-modal').classList.add('open');
}

function meYeniSoruEkle() {
  meSoruSayisi++;
  const n = meSoruSayisi;
  const div = document.createElement('div');
  div.id = 'me-soru-' + n;
  div.style.cssText = 'background:var(--bg);border-radius:10px;padding:12px;margin-bottom:10px;border:1px solid var(--border)';
  div.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
      <span style="font-size:12px;font-weight:700;color:var(--muted)">SORU ${n}</span>
      <button onclick="document.getElementById('me-soru-${n}').remove()" style="background:none;border:none;cursor:pointer;color:var(--red)">✕</button>
    </div>
    <input type="text" class="form-input" id="me-s${n}-soru" placeholder="Soru metni?" style="margin-bottom:6px;font-size:13px">
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:6px">
      <input type="text" class="form-input" id="me-s${n}-a" placeholder="A şıkkı" style="font-size:12px">
      <input type="text" class="form-input" id="me-s${n}-b" placeholder="B şıkkı" style="font-size:12px">
      <input type="text" class="form-input" id="me-s${n}-c" placeholder="C şıkkı" style="font-size:12px">
      <input type="text" class="form-input" id="me-s${n}-d" placeholder="D şıkkı" style="font-size:12px">
    </div>
    <div style="display:flex;align-items:center;gap:8px;font-size:12px">
      <span style="color:var(--muted)">Doğru şık:</span>
      <label><input type="radio" name="me-dogru-${n}" value="0"> A</label>
      <label><input type="radio" name="me-dogru-${n}" value="1"> B</label>
      <label><input type="radio" name="me-dogru-${n}" value="2"> C</label>
      <label><input type="radio" name="me-dogru-${n}" value="3" checked> D</label>
    </div>`;
  document.getElementById('me-sorular-konteyner').appendChild(div);
}

async function manuelEgitimKaydet() {
  const baslik = document.getElementById('me-baslik').value.trim();
  const tur = document.getElementById('me-tur').value.trim() || 'Is Guvenligi';
  const sure = document.getElementById('me-sure').value.trim() || '~10 dakika';
  const metin = document.getElementById('me-metin').value.trim();
  const hataEl = document.getElementById('me-hata');

  if(!baslik || !metin) {
    hataEl.textContent = 'Baslik ve egitim metni zorunludur.';
    hataEl.style.display = 'block';
    return;
  }

  // Sorulari topla
  const sorular = [];
  const soruDivler = document.querySelectorAll('[id^="me-soru-"]');
  for(const div of soruDivler) {
    const n = div.id.replace('me-soru-','');
    const soru = document.getElementById('me-s'+n+'-soru')?.value.trim();
    const a = document.getElementById('me-s'+n+'-a')?.value.trim();
    const b = document.getElementById('me-s'+n+'-b')?.value.trim();
    const c = document.getElementById('me-s'+n+'-c')?.value.trim();
    const d = document.getElementById('me-s'+n+'-d')?.value.trim();
    const dogru = document.querySelector('input[name="me-dogru-'+n+'"]:checked')?.value;
    if(soru && a && b) {
      sorular.push({
        soru, secenekler: [a, b||'C', c||'D', d||'E'],
        dogru: parseInt(dogru||'0')
      });
    }
  }

  if(sorular.length < 2) {
    hataEl.textContent = 'En az 2 soru gereklidir.';
    hataEl.style.display = 'block';
    return;
  }

  // ID olustur
  // egitim_id sunucu tarafinda olusturuluyor, burada gerek yok

  try {
    const firmalar = seciliFirmalariAl('me-firma-secim');
    const r = await fetch('/panel/api/egitim-manuel-ekle', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({baslik, tur, sure, metin, sorular, firmalar})
    });
    const d = await r.json();
    if(d.basarili) {
      modalKapat('manuel-egitim-modal');
      egitimListesiYukle();
    } else {
      hataEl.textContent = 'Hata: ' + (d.hata||'Bilinmeyen');
      hataEl.style.display = 'block';
    }
  } catch(e) {
    hataEl.textContent = 'Baglanti hatasi';
    hataEl.style.display = 'block';
  }
}

async function egitimSil(id, baslik, btn) {
  // Egitim baska firmalarda da var mi?
  const r0 = await fetch('/panel/api/egitim-detay?id='+id);
  const d0 = await r0.json();
  const firmalar = d0.egitim?.firmalar || [];

  let kapsam = 'tum';
  if(firmalar.length > 1 || (firmalar.length === 0)) {
    // Birden fazla firmada veya tum firmalarda
    const secim = confirm('"' + baslik + '" egitimi birden fazla firmada mevcut.\n\nTamam = Sadece bu firmadan kaldir\nIptal = Tum firmalardan sil');
    kapsam = secim ? 'bu_firma' : 'tum';
    if(kapsam === 'tum' && !confirm('Tüm firmalardan silmek istediğinizden emin misiniz?')) return;
  } else {
    if(!confirm('"' + baslik + '" eğitimini silmek istediğinizden emin misiniz?')) return;
  }

  btn.textContent = '⏳'; btn.disabled = true;
  const r = await fetch('/panel/api/egitim-sil', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body:JSON.stringify({egitim_id:id, kapsam:kapsam, firma_id:aktifFirma})
  });
  const d = await r.json();
  if(d.basarili) {
    document.getElementById('ekart-'+id)?.remove();
  } else {
    alert('Hata: '+(d.hata||'Bilinmeyen'));
    btn.textContent = '🗑 Sil'; btn.disabled = false;
  }
}

async function egitimDetayAl(id, btn) {
  btn.textContent = '⏳';
  try {
    const r = await fetch('/panel/api/egitim-detay?id=' + id);
    const d = await r.json();
    if(d.basarili) {
      document.getElementById('ed-id').value = id;
      document.getElementById('ed-baslik').value = d.egitim.baslik || '';
      document.getElementById('ed-tur').value = d.egitim.tur || '';
      document.getElementById('ed-sure').value = d.egitim.sure || '';
      document.getElementById('ed-metin').value = d.egitim.metin || '';
      document.getElementById('ed-sorular').value = JSON.stringify(d.egitim.sorular || [], null, 2);
      document.getElementById('ed-hata').style.display = 'none';
      document.getElementById('egitim-duzenle-modal').classList.add('open');
    } else {
      alert('Detay alinamadi: ' + (d.hata||''));
    }
  } catch(e) { alert('Baglanti hatasi'); }
  btn.textContent = '✏️ Düzenle';
}

async function egitimDuzenleKaydet() {
  const id = document.getElementById('ed-id').value;
  const baslik = document.getElementById('ed-baslik').value.trim();
  const tur = document.getElementById('ed-tur').value.trim();
  const sure = document.getElementById('ed-sure').value.trim();
  const metin = document.getElementById('ed-metin').value.trim();
  const soruTxt = document.getElementById('ed-sorular').value.trim();
  const hataEl = document.getElementById('ed-hata');

  if(!baslik){ hataEl.textContent='Başlık zorunlu'; hataEl.style.display='block'; return; }

  let sorular = null;
  if(soruTxt) {
    try { sorular = JSON.parse(soruTxt); }
    catch(e) { hataEl.textContent='Sorular geçersiz JSON: '+e.message; hataEl.style.display='block'; return; }
  }
  hataEl.style.display = 'none';

  // Birden fazla firmada mi kontrol et
  let kapsam = 'tum';
  try {
    const r0 = await fetch('/panel/api/egitim-detay?id='+id);
    const d0 = await r0.json();
    const firmalar = d0.egitim?.firmalar || [];
    if(firmalar.length > 1 || firmalar.length === 0) {
      const secim = confirm('Bu egitim birden fazla firmada mevcut.\n\nTamam = Sadece bu firmadaki kopyayi guncelle\nIptal = Tum firmalarda guncelle');
      kapsam = secim ? 'bu_firma' : 'tum';
    }
  } catch(e) {}

  const r = await fetch('/panel/api/egitim-guncelle', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body:JSON.stringify({egitim_id:id, baslik, tur, sure, metin, sorular, kapsam, firma_id:aktifFirma})
  });
  const d = await r.json();
  if(d.basarili) { modalKapat('egitim-duzenle-modal'); egitimListesiYukle(); }
  else { hataEl.textContent='Hata: '+(d.hata||'Bilinmeyen'); hataEl.style.display='block'; }
}

// ── CALISAN AKSIYONLARI ──────────────────

async function egitimSecModalAc(tid, ad, btn) {
  if(!tid || tid <= 0) { alert('Telegram hesabı bağlı değil. Çalışanın bota /start yazması gerekiyor.'); return; }
  document.getElementById('egitim-sec-tid').value = tid;
  document.getElementById('egitim-sec-calisan-adi').textContent = ad;
  document.getElementById('egitim-sec-liste').innerHTML = '<div class="loading"><div class="spinner"></div>Yükleniyor...</div>';
  document.getElementById('egitim-sec-bos').style.display = 'none';
  document.getElementById('egitim-sec-modal').classList.add('open');

  try {
    const r = await fetch(`/panel/api/calisan-egitim-durumu?tid=${tid}`);
    const d = await r.json();

    if(!d.tamamlanmamis || d.tamamlanmamis.length === 0) {
      document.getElementById('egitim-sec-liste').innerHTML = '';
      document.getElementById('egitim-sec-bos').style.display = 'block';
      return;
    }

    document.getElementById('egitim-sec-liste').innerHTML = d.tamamlanmamis.map(e => `
      <div style="display:flex;justify-content:space-between;align-items:center;padding:12px 14px;background:var(--card);border:1px solid var(--border);border-radius:10px">
        <div>
          <div style="font-weight:600;font-size:14px">${e.baslik}</div>
          <div style="font-size:12px;color:var(--muted);margin-top:2px">${e.tur} · ${e.sure}</div>
        </div>
        <button class="btn btn-primary btn-sm" onclick="egitimGonderSecili('${e.id}',${tid},'${ad.replace(/'/g,"\'")}',this)">Gönder</button>
      </div>`).join('');

  } catch(e) {
    document.getElementById('egitim-sec-liste').innerHTML = '<div style="color:red">Yüklenemedi: ' + e.message + '</div>';
  }
}

async function egitimGonderSecili(egitimId, tid, ad, btn) {
  btn.textContent = '⏳'; btn.disabled = true;
  try {
    const r = await fetch('/panel/api/egitim-gonder-calisan', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({telegram_id: tid, egitim_id: egitimId})
    });
    const d = await r.json();
    if(d.basarili) {
      btn.textContent = '✅ Gönderildi';
      btn.style.background = 'var(--green,#27ae60)';
      btn.disabled = true;
    } else {
      alert('Hata: ' + (d.hata || 'Bilinmeyen hata'));
      btn.textContent = 'Gönder'; btn.disabled = false;
    }
  } catch(e) {
    alert('Bağlantı hatası');
    btn.textContent = 'Gönder'; btn.disabled = false;
  }
}

async function egitimGonderCalisan(tid, ad, btn) {
  if(!tid || tid <= 0) { alert('Bu çalışanın Telegram hesabı bağlı değil.'); return; }
  if(!confirm(ad + ' kisine bugunku egitimi gondermek istediginizden emin misiniz?')) return;
  btn.textContent = '⏳';
  btn.disabled = true;
  try {
    const r = await fetch('/panel/api/egitim-gonder-calisan', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({telegram_id: tid})
    });
    const d = await r.json();
    if(d.basarili) {
      btn.textContent = '✅ Gönderildi';
      btn.style.background = 'var(--green, #27ae60)';
      setTimeout(() => { btn.textContent = '📤 Eğitim Gönder'; btn.style.background = ''; btn.disabled = false; }, 3000);
    } else {
      alert('Hata: ' + (d.hata || 'Bilinmeyen hata'));
      btn.textContent = '📤 Eğitim Gönder';
      btn.disabled = false;
    }
  } catch(e) {
    alert('Bağlantı hatası');
    btn.textContent = '📤 Eğitim Gönder';
    btn.disabled = false;
  }
}

async function kayitButonuGonder(btn) {
  if(!confirm('Gruba kayıt butonu gönderilsin mi? Sisteme kayıtlı olmayan üyeler bu butona basarak kaydolabilir.')) return;
  btn.textContent = '⏳'; btn.disabled = true;
  try {
    const r = await fetch('/panel/api/kayit-butonu-gonder', {method:'POST'});
    const d = await r.json();
    if(d.basarili) {
      btn.textContent = '✅ Gönderildi';
      btn.style.background = 'var(--green,#27ae60)';
      setTimeout(() => { btn.textContent = '📌 Kayıt Butonu Gönder'; btn.style.background=''; btn.disabled=false; }, 4000);
    } else {
      alert('Hata: ' + (d.hata||''));
      btn.textContent = '📌 Kayıt Butonu Gönder'; btn.disabled = false;
    }
  } catch(e) {
    alert('Bağlantı hatası');
    btn.textContent = '📌 Kayıt Butonu Gönder'; btn.disabled = false;
  }
}

async function egitimDetayGoster(tid, ad, btn) {
  const detayDiv = document.getElementById('detay-' + tid);
  if(detayDiv.style.display !== 'none') {
    detayDiv.style.display = 'none';
    btn.textContent = 'Detay';
    return;
  }
  btn.textContent = '⏳';
  // tid ve ad'i detay div'e kaydet (Tekrar Gonder icin)
  detayDiv.dataset.tid = tid;
  detayDiv.dataset.ad = ad;
  try {
    const r = await fetch(`/panel/api/calisan-egitim-durumu?tid=${tid}`);
    const d = await r.json();
    const t = d.tamamlanan || [];
    const e = d.tamamlanmamis || [];
    detayDiv.innerHTML = `
      <div style="display:flex;flex-direction:column;gap:10px;margin-top:8px">
        ${t.length ? `
          <div style="font-size:11px;font-weight:700;color:var(--green);margin-bottom:2px">✅ TAMAMLANDI (${t.length})</div>
          ${t.map(x=>`
            <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 10px;background:#f0faf2;border:1px solid #c3e6cb;border-radius:8px">
              <div>
                <div style="font-size:12px;font-weight:600">${x.baslik}</div>
                ${x.kac_kez > 0 ? `<div style="font-size:11px;color:var(--muted)">${x.kac_kez} deneme · Son: ${x.son_tarih} · ${x.son_puan} puan</div>` : ''}
              </div>
              <button class="btn btn-dark" style="font-size:11px;padding:3px 8px" onclick="egitimGonderSecili('${x.id}',${tid},'${ad}',this)">↩ Tekrar</button>
            </div>`).join('')}
        ` : ''}
        ${e.length ? `
          <div style="font-size:11px;font-weight:700;color:var(--red,#e74c3c);margin-top:4px;margin-bottom:2px">⏳ TAMAMLANMADI (${e.length})</div>
          ${e.map(x=>`
            <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 10px;background:#fff8f0;border:1px solid #fcd;border-radius:8px">
              <div>
                <div style="font-size:12px;font-weight:600">${x.baslik}</div>
                ${x.kac_kez > 0 ? `<div style="font-size:11px;color:var(--muted)">${x.kac_kez} deneme · Son: ${x.son_tarih} · ${x.son_puan} puan</div>` : '<div style="font-size:11px;color:var(--muted)">Henüz almadı</div>'}
              </div>
              <button class="btn btn-primary" style="font-size:11px;padding:3px 8px" onclick="egitimGonderSecili('${x.id}',${tid},'${ad}',this)">Gönder</button>
            </div>`).join('')}
        ` : ''}
      </div>`;
    detayDiv.style.display = 'block';
    btn.textContent = 'Gizle';
  } catch(err) {
    btn.textContent = 'Detay';
  }
}

async function ekstraHakVer(tid, ad, btn) {
  if(!tid || tid <= 0) { alert('Bu çalışanın Telegram hesabı bağlı değil.'); return; }
  if(!confirm(ad + ' kisine bugun icin tekrar egitim izni vermek istiyor musunuz?')) return;
  btn.textContent = '⏳';
  btn.disabled = true;
  try {
    const r = await fetch('/panel/api/ekstra-hak', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({telegram_id: tid})
    });
    const d = await r.json();
    if(d.basarili) {
      btn.textContent = '✅ Hak Verildi';
      btn.style.background = 'var(--green, #27ae60)';
      setTimeout(() => { btn.textContent = '🔁 Tekrar İzni'; btn.style.background = ''; btn.disabled = false; }, 3000);
    } else {
      alert('Hata: ' + (d.hata || 'Bilinmeyen hata'));
      btn.textContent = '🔁 Tekrar İzni';
      btn.disabled = false;
    }
  } catch(e) {
    alert('Bağlantı hatası');
    btn.textContent = '🔁 Tekrar İzni';
    btn.disabled = false;
  }
}

// ── TOPLU İŞLEM ──────────────────────────

async function topluIslemModalAc(egitimId, egitimAdi) {
  document.getElementById('toplu-egitim-id').value = egitimId;
  document.getElementById('toplu-egitim-adi').textContent = egitimAdi;
  document.getElementById('toplu-hata').style.display = 'none';
  document.querySelector('input[name="toplu-kapsam"][value="hepsi"]').checked = true;
  document.querySelector('input[name="toplu-islem"][value="tamamlandi"]').checked = true;
  document.getElementById('toplu-calisan-secim').style.display = 'none';

  // Calisan listesini yukle
  try {
    const r = await fetch(`/panel/api/calisanlar?firma_id=${aktifFirma}`);
    const resp = await r.json();
    const calisanlar = Array.isArray(resp) ? resp : resp.calisanlar;
    document.getElementById('toplu-calisan-secim').innerHTML = calisanlar
      .filter(c => c.telegram_id > 0)
      .map(c => `
        <label style="display:flex;align-items:center;gap:8px;cursor:pointer;padding:4px 0">
          <input type="checkbox" name="toplu-calisan-cb" value="${c.telegram_id}"> 
          ${c.ad_soyad} <span style="color:var(--muted);font-size:11px">${c.gorev}</span>
        </label>`).join('');
  } catch(e) {}

  // Kapsam secimi degisince calisan listesini goster/gizle
  document.querySelectorAll('input[name="toplu-kapsam"]').forEach(r => {
    r.onchange = () => {
      document.getElementById('toplu-calisan-secim').style.display =
        r.value === 'secili' ? 'block' : 'none';
    };
  });

  document.getElementById('toplu-islem-modal').classList.add('open');
}

async function topluIslemUygula() {
  const egitimId = document.getElementById('toplu-egitim-id').value;
  const islem = document.querySelector('input[name="toplu-islem"]:checked')?.value;
  const kapsam = document.querySelector('input[name="toplu-kapsam"]:checked')?.value;
  const hataEl = document.getElementById('toplu-hata');

  let telegram_idler = [];
  if(kapsam === 'secili') {
    telegram_idler = Array.from(document.querySelectorAll('input[name="toplu-calisan-cb"]:checked'))
      .map(cb => parseInt(cb.value));
    if(!telegram_idler.length) {
      hataEl.textContent = 'En az bir çalışan seçin.';
      hataEl.style.display = 'block';
      return;
    }
  }

  const btn = document.querySelector('#toplu-islem-modal .btn-primary');
  btn.textContent = '⏳ Uygulanıyor...';
  btn.disabled = true;
  hataEl.style.display = 'none';

  try {
    const r = await fetch('/panel/api/toplu-islem', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        egitim_id: egitimId,
        islem: islem,
        kapsam: kapsam,
        telegram_idler: telegram_idler,
        firma_id: aktifFirma
      })
    });
    const d = await r.json();
    if(d.basarili) {
      modalKapat('toplu-islem-modal');
      alert(`✅ İşlem tamamlandı: ${d.etkilenen} çalışan güncellendi.`);
      calisanListesiYukle();
    } else {
      hataEl.textContent = 'Hata: ' + (d.hata || '');
      hataEl.style.display = 'block';
    }
  } catch(e) {
    hataEl.textContent = 'Bağlantı hatası';
    hataEl.style.display = 'block';
  }
  btn.textContent = 'Uygula';
  btn.disabled = false;
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
  firmaSecimDoldur('ai-firma-secim');
  document.getElementById('ai-modal').classList.add('open');
}

async function egitimUret() {
  const konu=document.getElementById('ai-konu').value.trim();
  if(!konu){alert('Konu girin.');return;}
  document.getElementById('ai-form').style.display='none';
  document.getElementById('ai-progress').style.display='block';
  try {
    const r=await fetch('/panel/api/egitim-uret',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({konu,sektor:document.getElementById('ai-sektor').value,notlar:document.getElementById('ai-notlar').value,firmalar:seciliFirmalariAl('ai-firma-secim')})});
    const d=await r.json();
    if(d.basarili){
      document.getElementById('ai-progress').style.display='none';
      document.getElementById('ai-success').style.display='block';
      document.getElementById('ai-success-detail').textContent=`"${d.baslik}" eklendi. /egitim_gonder ${d.id}`;
    } else {alert('Hata: '+(d.hata||'Bilinmeyen'));document.getElementById('ai-form').style.display='block';document.getElementById('ai-progress').style.display='none';}
  } catch(e){alert('Bağlantı hatası');document.getElementById('ai-form').style.display='block';document.getElementById('ai-progress').style.display='none';}
}

// Sayfa acilinca ana sayfayi goster
// Sayfa yuklenince calistir
window.onload = function() {
  try {
    const kaydedilen = sessionStorage.getItem('aktifFirma');
    const kaydedilenAdi = sessionStorage.getItem('aktifFirmaAdi');
    if(kaydedilen && kaydedilenAdi) {
      firmaAc(kaydedilen, kaydedilenAdi);
      return;
    }
  } catch(e) {}
  anaSeyfayaDon();
};
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
    firma_id=request.args.get("firma_id","varsayilan")
    try: kayitlar=tum_kayitlar_getir(firma_id)
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
        if k.get("durum") in ("GEÇTİ","GECTI"): ozet[konu]["gecti"]+=1
        else: ozet[konu]["kaldi"]+=1
    return jsonify({"kayitlar":f,"egitim_ozet":ozet})

@app.route("/panel/api/calisanlar")
def api_calisanlar():
    if not session.get("panel_giris"): return jsonify([]),401
    from config import EGITIMLER, BOT_USERNAME
    from durum import izinli_mi, bugun_tamamlayanlar
    from sheets import tum_kayitlar_getir

    firma_id = request.args.get("firma_id", "varsayilan")
    calisanlar = tum_calisanlar(firma_id)
    bugun = date.today().strftime("%d.%m.%Y")
    bugun_tamamlayan_listesi = bugun_tamamlayanlar(bugun)
    toplam_egitim = len(EGITIMLER)

    # Tum kayitlari TEK SEFERDE cek — her calisan icin ayri cekme
    try:
        tum_kayitlar = tum_kayitlar_getir(firma_id)
    except:
        tum_kayitlar = []

    # Her calisan icin gecilen egitimleri hesapla
    def gecilen_egitimler_hesapla(tid):
        gecilen = set()
        for k in tum_kayitlar:
            if str(k.get("telegram_id","")) == str(tid):
                if k.get("durum","") in ("GECTI","GECTİ"):
                    konu = k.get("egitim_konusu","")
                    for eid, e in EGITIMLER.items():
                        if e.get("baslik","") == konu:
                            gecilen.add(eid)
                            break
        return gecilen

    sonuc = []
    for tid, c in calisanlar.items():
        gecilen = gecilen_egitimler_hesapla(tid)
        tamamlanan = len(gecilen)
        # Toplam kac egitim almis (gecti/kaldi farketmez)
        toplam_alinmis = sum(1 for k in tum_kayitlar if str(k.get("telegram_id","")) == str(tid))
        # Son egitim tarihi
        calisan_kayitlar = [k for k in tum_kayitlar if str(k.get("telegram_id","")) == str(tid)]
        son_egitim = calisan_kayitlar[-1].get("tarih","") if calisan_kayitlar else ""

        sonuc.append({
            "telegram_id": tid,
            "ad_soyad": c["ad_soyad"],
            "gorev": c["gorev"],
            "dogum_tarihi": c["dogum_tarihi"],
            "bugun_izinli": izinli_mi(tid, bugun),
            "bugun_tamamladi": str(tid) in bugun_tamamlayan_listesi,
            "tamamlanan": tamamlanan,
            "toplam_egitim": toplam_egitim,
            "toplam_alinmis": toplam_alinmis,
            "son_egitim": son_egitim
        })

    return jsonify({"calisanlar": sonuc, "bot_username": BOT_USERNAME})

@app.route("/panel/api/calisan-ekle", methods=["POST"])
def api_calisan_ekle():
    if not session.get("panel_giris"): return jsonify({"basarili":False}),401
    d=request.get_json()
    try:
        raw = d.get("telegram_id", None)
        # raw None, 0, "None", "" hepsini None yap
        if raw is None or str(raw).strip() in ("", "None", "null", "0"):
            tid = None
        else:
            tid = int(str(raw).strip())
        calisan_ekle(tid, d["ad_soyad"], d["dogum_tarihi"], d["gorev"])
        return jsonify({"basarili":True})
    except Exception as e:
        import traceback
        return jsonify({"basarili":False,"hata":str(e),"detay":traceback.format_exc()})

@app.route("/panel/api/calisan-guncelle", methods=["POST"])
def api_calisan_guncelle():
    if not session.get("panel_giris"): return jsonify({"basarili":False}),401
    d=request.get_json()
    try:
        raw = d.get("telegram_id", None)
        if raw is None or str(raw).strip() in ("", "None", "null", "0"):
            tid = None
        else:
            tid = int(str(raw).strip())
        calisan_guncelle(tid, d["ad_soyad"], d["dogum_tarihi"], d["gorev"])
        return jsonify({"basarili":True})
    except Exception as e:
        import traceback
        return jsonify({"basarili":False,"hata":str(e),"detay":traceback.format_exc()})

@app.route("/panel/api/calisan-arsivle", methods=["POST"])
def api_calisan_arsivle():
    if not session.get("panel_giris"): return jsonify({"basarili":False}),401
    veri = request.get_json()
    tid = veri.get("telegram_id")
    firma_id = veri.get("firma_id","varsayilan")
    try:
        from calisanlar import calisan_arsivle
        basarili = calisan_arsivle(tid, firma_id)
        return jsonify({"basarili":basarili})
    except Exception as e:
        return jsonify({"basarili":False,"hata":str(e)})


@app.route("/panel/api/calisan-arsivden-al", methods=["POST"])
def api_calisan_arsivden_al():
    if not session.get("panel_giris"): return jsonify({"basarili":False}),401
    veri = request.get_json()
    tid = veri.get("telegram_id")
    firma_id = veri.get("firma_id","varsayilan")
    try:
        from calisanlar import calisan_arsivden_al
        basarili = calisan_arsivden_al(tid, firma_id)
        return jsonify({"basarili":basarili})
    except Exception as e:
        return jsonify({"basarili":False,"hata":str(e)})


@app.route("/panel/api/arsiv-calisanlar")
def api_arsiv_calisanlar():
    if not session.get("panel_giris"): return jsonify([]),401
    firma_id = request.args.get("firma_id","varsayilan")
    try:
        from sheets import tum_kayitlar_getir
        calisanlar = tum_calisanlar(firma_id, arsiv=True)
        tum_kayitlar = tum_kayitlar_getir(firma_id)
        liste = []
        for tid, c in calisanlar.items():
            tid_str = str(tid)
            kayitlar = [k for k in tum_kayitlar if k.get("telegram_id") == tid_str]
            gecilen = set(k.get("egitim_konusu") for k in kayitlar if k.get("durum") in ("GECTI","GECTİ"))
            son_egitim = max((k.get("tarih","") for k in kayitlar), default="")
            liste.append({
                "telegram_id": tid,
                "ad_soyad": c["ad_soyad"],
                "gorev": c["gorev"],
                "arsiv_tarihi": c.get("arsiv_tarihi",""),
                "toplam_katilim": len(kayitlar),
                "gecilen_egitim": len(gecilen),
                "gecilen_liste": sorted(gecilen),
                "son_egitim": son_egitim
            })
        return jsonify(liste)
    except Exception as e:
        return jsonify([])


@app.route("/panel/api/calisan-sil", methods=["POST"])
def api_calisan_sil():
    if not session.get("panel_giris"): return jsonify({"basarili":False}),401
    d = request.get_json()
    firma_id = d.get("firma_id","varsayilan")
    calisan_sil(int(d["telegram_id"]), firma_id) if d.get("telegram_id") else None
    return jsonify({"basarili":True})


@app.route("/panel/api/izin-ekle", methods=["POST"])
def api_izin_ekle():
    if not session.get("panel_giris"): return jsonify({"basarili":False}),401
    d=request.get_json()
    tid_izin = int(d["telegram_id"]) if d.get("telegram_id") else None
    if tid_izin:
        for t in d.get("tarihler",[]):
            izin_ekle(tid_izin, t)
    return jsonify({"basarili":True})

@app.route("/panel/api/egitimler")
def api_egitimler():
    if not session.get("panel_giris"): return jsonify([]),401
    firma_id = request.args.get("firma_id","")
    liste=[]
    for eid,e in EGITIMLER.items():
        # Firma filtresi — firmalar bos ise herkese goster
        egitim_firmalari = e.get("firmalar",[])
        if firma_id and egitim_firmalari and firma_id not in egitim_firmalari:
            continue
        temiz=e["metin"].replace("*","").replace("_","").strip()
        firma_etiketi = ""
        if egitim_firmalari:
            firma_etiketi = " | ".join(egitim_firmalari)
        liste.append({"id":eid,"baslik":e["baslik"],"tur":e["tur"],"sure":e["sure"],
                      "soru_sayisi":len(e["sorular"]),
                      "metin_onizleme":(temiz[:180]+"...") if len(temiz)>180 else temiz,
                      "firmalar":egitim_firmalari,"firma_etiketi":firma_etiketi})
    return jsonify(liste)

@app.route("/panel/api/egitim-uret", methods=["POST"])
def api_egitim_uret():
    if not session.get("panel_giris"): return jsonify({"basarili":False}),401
    veri = request.get_json()
    konu = veri.get("konu","").strip()
    sektor = veri.get("sektor","Cimento fabrikasi")
    notlar = veri.get("notlar","")
    firmalar = veri.get("firmalar", [])
    if not konu: return jsonify({"basarili":False,"hata":"Konu bos"})
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key: return jsonify({"basarili":False,"hata":"ANTHROPIC_API_KEY ayarlanmamis"})

    sistem = "Sen bir is guvenligi egitim uzmanisin. Verilen konuda Turkce egitim materyali olusturursun."

    icerik = (
        "Konu: " + konu + "\n"
        "Sektor: " + sektor + "\n"
        "Notlar: " + (notlar if notlar else "yok") + "\n\n"
        "Asagidaki formatta egitim olustur:\n\n"
        "BASLIK: [emoji ve baslik]\n"
        "TUR: [kategori]\n"
        "SURE: [sure]\n"
        "METIN_BASLANGIC\n"
        "[egitim metni - *kalin* yaz]\n"
        "METIN_BITIS\n"
        "SORU1: [soru]\n"
        "A1: [a] | B1: [b] | C1: [c] | D1: [d] | DOGRU1: [A/B/C/D]\n"
        "SORU2: [soru]\n"
        "A2: [a] | B2: [b] | C2: [c] | D2: [d] | DOGRU2: [A/B/C/D]\n"
        "SORU3: [soru]\n"
        "A3: [a] | B3: [b] | C3: [c] | D3: [d] | DOGRU3: [A/B/C/D]\n"
        "SORU4: [soru]\n"
        "A4: [a] | B4: [b] | C4: [c] | D4: [d] | DOGRU4: [A/B/C/D]\n"
        "SORU5: [soru]\n"
        "A5: [a] | B5: [b] | C5: [c] | D5: [d] | DOGRU5: [A/B/C/D]\n"
    )

    try:
        import requests as req_lib, time as tm, unicodedata
        resp = req_lib.post(
            "https://api.anthropic.com/v1/messages",
            headers={"Content-Type":"application/json","x-api-key":api_key,"anthropic-version":"2023-06-01"},
            json={"model":"claude-opus-4-5","max_tokens":3000,
                  "system":sistem,"messages":[{"role":"user","content":icerik}]},
            timeout=60
        )
        if not resp.ok:
            return jsonify({"basarili":False,"hata":"API "+str(resp.status_code)+": "+resp.text[:200]})

        ham = resp.json()["content"][0]["text"].strip()

        def al(anahtar):
            for satir in ham.split("\n"):
                s = satir.strip()
                if s.startswith(anahtar+":"):
                    return s.split(":",1)[1].strip()
                if "|" in s:
                    for parca in s.split("|"):
                        p = parca.strip()
                        if p.startswith(anahtar+":"):
                            return p.split(":",1)[1].strip()
            return ""

        def metin_blok():
            try:
                return ham.split("METIN_BASLANGIC")[1].split("METIN_BITIS")[0].strip()
            except:
                return konu + " hakkinda egitim."

        baslik = al("BASLIK") or konu
        tur = al("TUR") or "Is Guvenligi"
        sure = al("SURE") or "~10 dakika"
        egitim_metni = metin_blok()

        harf = {"A":0,"B":1,"C":2,"D":3}
        sorular = []
        for i in range(1,6):
            soru = al("SORU"+str(i))
            a = al("A"+str(i))
            b = al("B"+str(i))
            c = al("C"+str(i))
            d = al("D"+str(i))
            dogru = harf.get(al("DOGRU"+str(i)).upper()[:1], 0)
            if soru and a:
                sorular.append({"soru":soru,"secenekler":[a,b or "Diger",c or "Diger",d or "Hicbiri"],"dogru":dogru})

        if len(sorular) < 3:
            return jsonify({"basarili":False,"hata":"Yeterli soru uretilmedi. Tekrar deneyin."})

        eid = unicodedata.normalize("NFKD",konu.lower()).encode("ascii","ignore").decode("ascii")
        eid = re.sub(r"[^a-z0-9]","_",eid)
        eid = re.sub(r"_+","_",eid).strip("_")[:20]+"_"+str(int(tm.time()))[-4:]

        EGITIMLER[eid] = {"baslik":baslik,"tur":tur,"sure":sure,"metin":egitim_metni,"sorular":sorular,"firmalar":firmalar}
        try:
            from egitimler_sheets import egitim_ekle
            egitim_ekle(eid,baslik,tur,sure,egitim_metni,sorular,firmalar)
        except Exception as se:
            logger.warning("Sheets kayit: "+str(se))
        return jsonify({"basarili":True,"id":eid,"baslik":baslik})
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
                "text": "*" + egitim['baslik'] + "* egitimi basladi!\n\nKatilmak icin",
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


@app.route("/panel/api/calisan-egitim-durumu")
def api_calisan_egitim_durumu():
    """Calisanin egitim gecmisini dondur — her egitim icin kac kez aldigi, puani, gecip gecmedigi."""
    if not session.get("panel_giris"): return jsonify({}), 401
    tid = request.args.get("tid", 0, type=int)
    if not tid: return jsonify({"hata": "Gecersiz ID"})

    from durum import eksik_egitimler
    from sheets import tum_kayitlar_getir

    eksik = eksik_egitimler(tid)

    # Bu calisanin tum kayitlarini getir
    try:
        tum = tum_kayitlar_getir()
        calisan_kayitlar = [k for k in tum if str(k.get("telegram_id","")) == str(tid)]
    except:
        calisan_kayitlar = []

    # Her egitim icin istatistik hesapla
    egitim_istatistik = {}
    for k in calisan_kayitlar:
        konu = k.get("egitim_konusu","")
        if konu not in egitim_istatistik:
            egitim_istatistik[konu] = []
        egitim_istatistik[konu].append({
            "tarih": k.get("tarih",""),
            "saat": k.get("saat",""),
            "puan": k.get("puan",""),
            "durum": k.get("durum","")
        })

    tamamlanmamis = []
    tamamlanan = []

    for eid, e in EGITIMLER.items():
        baslik = e.get("baslik","")
        kayitlar = egitim_istatistik.get(baslik, [])
        son_kayit = kayitlar[-1] if kayitlar else None
        gecti_mi = any(k.get("durum") in ("GECTI","GECTİ") for k in kayitlar)

        bilgi = {
            "id": eid,
            "baslik": baslik,
            "tur": e.get("tur",""),
            "sure": e.get("sure",""),
            "kac_kez": len(kayitlar),
            "son_puan": son_kayit["puan"] if son_kayit else "-",
            "son_tarih": son_kayit["tarih"] if son_kayit else "-",
            "son_durum": son_kayit["durum"] if son_kayit else "-",
            "gecti": gecti_mi
        }

        if eid in eksik:
            tamamlanmamis.append(bilgi)
        else:
            tamamlanan.append(bilgi)

    return jsonify({
        "tamamlanmamis": tamamlanmamis,
        "tamamlanan": tamamlanan,
        "ozet": f"{len(tamamlanan)}/{len(EGITIMLER)} tamamlandi"
    })


@app.route("/panel/api/egitim-gonder-calisan", methods=["POST"])
def api_egitim_gonder_calisan():
    if not session.get("panel_giris"): return jsonify({"basarili":False}),401
    from durum import gunun_egitim_id, aktif_egitim_set, ekstra_hak_ver
    veri = request.get_json()
    tid = int(veri.get("telegram_id",0))
    if not tid: return jsonify({"basarili":False,"hata":"Gecersiz ID"})

    # Belirli bir egitim secildiyse onu kullan, yoksa gunun egitimini al
    egitim_id = veri.get("egitim_id", "").strip() or gunun_egitim_id()
    if not egitim_id:
        from durum import siradaki_egitim_al
        egitim_id, _ = siradaki_egitim_al()

    egitim = EGITIMLER.get(egitim_id)
    if not egitim: return jsonify({"basarili":False,"hata":"Aktif egitim yok"})

    aktif_egitim_set(egitim_id)
    # Ekstra hak ver ki butona basabilsin
    ekstra_hak_ver(tid)

    token = os.environ.get("TELEGRAM_BOT_TOKEN","")
    base = f"https://api.telegram.org/bot{token}"
    keyboard = {"inline_keyboard":[[{"text":"Egitime Basla","callback_data":f"egitim_baslat:{egitim_id}"}]]}

    import requests as req_lib
    try:
        resp = req_lib.post(f"{base}/sendMessage", json={
            "chat_id": tid,
            "text": "Yoneticiniz size bugunun egitimini gonderdi.\n\n*" + egitim['baslik'] + "*\n\nBaslamak icin asagidaki butona basin:",
            "parse_mode": "Markdown",
            "reply_markup": keyboard
        }, timeout=10)
        result = resp.json()
        if result.get("ok"):
            return jsonify({"basarili":True})
        else:
            hata = result.get("description","Telegram hatasi")
            # Bot bu kullaniciya mesaj gonderemiyor — /start yazmamis olabilir
            if "bot was blocked" in hata or "chat not found" in hata or "user is deactivated" in hata:
                return jsonify({"basarili":False,"hata":f"Kullanici botu engellemis veya bota hic mesaj yazmamis. Calisanin @BasTasEgitimBot'a /start yazmasi gerekiyor."})
            return jsonify({"basarili":False,"hata":hata})
    except Exception as e:
        return jsonify({"basarili":False,"hata":str(e)})


@app.route("/panel/api/ekstra-hak", methods=["POST"])
def api_ekstra_hak():
    if not session.get("panel_giris"): return jsonify({"basarili":False}),401
    from durum import ekstra_hak_ver, gunun_egitim_id, aktif_egitim_set
    veri = request.get_json()
    tid = int(veri.get("telegram_id",0))
    if not tid: return jsonify({"basarili":False,"hata":"Gecersiz ID"})

    egitim_id = gunun_egitim_id()
    if not egitim_id:
        from durum import siradaki_egitim_al
        egitim_id, _ = siradaki_egitim_al()

    egitim = EGITIMLER.get(egitim_id)
    if not egitim: return jsonify({"basarili":False,"hata":"Aktif egitim yok"})

    aktif_egitim_set(egitim_id)
    ekstra_hak_ver(tid)

    token = os.environ.get("TELEGRAM_BOT_TOKEN","")
    base = f"https://api.telegram.org/bot{token}"
    keyboard = {"inline_keyboard":[[{"text":"Egitime Basla","callback_data":f"egitim_baslat:{egitim_id}"}]]}

    import requests as req_lib
    try:
        req_lib.post(f"{base}/sendMessage", json={
            "chat_id": tid,
            "text": "Yoneticiniz size ek deneme hakki tanimladi.\n\n*" + egitim['baslik'] + "*\n\nBaslamak icin:",
            "parse_mode": "Markdown",
            "reply_markup": keyboard
        }, timeout=10)
        return jsonify({"basarili":True})
    except Exception as e:
        return jsonify({"basarili":False,"hata":str(e)})


@app.route("/panel/api/egitim-manuel-ekle", methods=["POST"])
def api_egitim_manuel_ekle():
    if not session.get("panel_giris"): return jsonify({"basarili":False}),401
    veri = request.get_json()
    baslik = veri.get("baslik","").strip()
    tur = veri.get("tur","Is Guvenligi").strip()
    sure = veri.get("sure","~10 dakika").strip()
    metin = veri.get("metin","").strip()
    sorular = veri.get("sorular",[])
    firmalar = veri.get("firmalar", [])

    if not baslik or not metin or len(sorular) < 2:
        return jsonify({"basarili":False,"hata":"Eksik bilgi"})

    import re, unicodedata, time
    eid = unicodedata.normalize('NFKD', baslik.lower())
    eid = eid.encode('ascii','ignore').decode('ascii')
    eid = re.sub(r'[^a-z0-9]','_', eid)
    eid = re.sub(r'_+','_', eid).strip('_')[:25]
    eid = eid + '_' + str(int(time.time()))[-4:]

    try:
        EGITIMLER[eid] = {"baslik":baslik,"tur":tur,"sure":sure,"metin":metin,"sorular":sorular,"firmalar":firmalar}
        from egitimler_sheets import egitim_ekle
        egitim_ekle(eid, baslik, tur, sure, metin, sorular, firmalar)
        return jsonify({"basarili":True,"id":eid})
    except Exception as e:
        return jsonify({"basarili":False,"hata":str(e)})


@app.route("/panel/api/egitim-sil", methods=["POST"])
def api_egitim_sil():
    if not session.get("panel_giris"): return jsonify({"basarili":False}),401
    veri = request.get_json()
    eid = veri.get("egitim_id","").strip()
    kapsam = veri.get("kapsam","tum")  # 'tum' veya 'bu_firma'
    firma_id = veri.get("firma_id","")
    try:
        from egitimler_sheets import egitim_sil, egitim_guncelle_tam, tum_egitimler
        if kapsam == "bu_firma" and firma_id:
            # Sadece bu firmadan kaldir
            egitim = EGITIMLER.get(eid,{})
            firmalar = egitim.get("firmalar",[])
            if firma_id in firmalar:
                firmalar.remove(firma_id)
            egitim_guncelle_tam(eid, firmalar=firmalar)
            EGITIMLER[eid]["firmalar"] = firmalar
            return jsonify({"basarili":True})
        else:
            # Tamamen sil
            basarili = egitim_sil(eid)
            if basarili:
                if eid in EGITIMLER: del EGITIMLER[eid]
                return jsonify({"basarili":True})
            return jsonify({"basarili":False,"hata":"Bulunamadi"})
    except Exception as e:
        return jsonify({"basarili":False,"hata":str(e)})


@app.route("/panel/api/egitim-detay")
def api_egitim_detay():
    if not session.get("panel_giris"): return jsonify({"basarili":False}),401
    eid = request.args.get("id","").strip()
    if eid not in EGITIMLER:
        return jsonify({"basarili":False,"hata":"Bulunamadi"})
    e = EGITIMLER[eid]
    return jsonify({"basarili":True,"egitim":{
        "id": eid,
        "baslik": e.get("baslik",""),
        "tur": e.get("tur",""),
        "sure": e.get("sure",""),
        "metin": e.get("metin",""),
        "sorular": e.get("sorular",[])
    }})


@app.route("/panel/api/egitim-guncelle", methods=["POST"])
def api_egitim_guncelle():
    if not session.get("panel_giris"): return jsonify({"basarili":False}),401
    veri = request.get_json()
    eid = veri.get("egitim_id","").strip()
    if eid not in EGITIMLER:
        return jsonify({"basarili":False,"hata":"Egitim bulunamadi"})
    try:
        from egitimler_sheets import egitim_guncelle_tam, tum_egitimler
        # Memory guncelle
        if veri.get("baslik"): EGITIMLER[eid]["baslik"] = veri["baslik"]
        if veri.get("tur"):    EGITIMLER[eid]["tur"]    = veri["tur"]
        if veri.get("sure"):   EGITIMLER[eid]["sure"]   = veri["sure"]
        if veri.get("metin"):  EGITIMLER[eid]["metin"]  = veri["metin"]
        if veri.get("sorular") is not None: EGITIMLER[eid]["sorular"] = veri["sorular"]
        # Sheets guncelle
        egitim_guncelle_tam(eid,
            baslik=veri.get("baslik"),
            tur=veri.get("tur"),
            sure=veri.get("sure"),
            metin=veri.get("metin"),
            sorular=veri.get("sorular")
        )
        return jsonify({"basarili":True})
    except Exception as e:
        return jsonify({"basarili":False,"hata":str(e)})


@app.route("/panel/api/mesaj-loglari")
def api_mesaj_loglari():
    if not session.get("panel_giris"): return jsonify([]), 401
    try:
        from handlers.grup_handler import mesaj_loglari
        return jsonify(list(mesaj_loglari))
    except Exception as e:
        return jsonify([])


@app.route("/panel/api/bekleyen-manuel-ekle", methods=["POST"])
def api_bekleyen_manuel_ekle():
    """Panelden manuel ID girilerek bekleyene ekle."""
    if not session.get("panel_giris"): return jsonify({"basarili":False}),401
    veri = request.get_json()
    uid = int(veri.get("user_id",0))
    if not uid: return jsonify({"basarili":False,"hata":"Gecersiz ID"})

    from calisanlar import calisan_bul
    if calisan_bul(uid):
        return jsonify({"basarili":False,"mesaj":"Bu kullanici zaten sistemde kayitli"})

    import requests as req_lib
    token = os.environ.get("TELEGRAM_BOT_TOKEN","")
    try:
        # Kullanici bilgisini Telegram'dan al
        r = req_lib.get(f"https://api.telegram.org/bot{token}/getChat",
                        params={"chat_id": uid}, timeout=5)
        d = r.json()
        if d.get("ok"):
            u = d["result"]
            ad = f"{u.get('first_name','')} {u.get('last_name','')}".strip() or f"Kullanici {uid}"
            username = f"@{u['username']}" if u.get("username") else ""
        else:
            ad = f"Kullanici {uid}"
            username = ""
    except:
        ad = f"Kullanici {uid}"
        username = ""

    from handlers.grup_handler import yeni_uyeler
    yeni_uyeler[uid] = {"ad": ad, "username": username}
    return jsonify({"basarili":True})


@app.route("/panel/api/bekleyenler")
def api_bekleyenler():
    """Grupta olup sistemde kaydi olmayan uyeleri dondur."""
    if not session.get("panel_giris"): return jsonify([]), 401
    try:
        from handlers.grup_handler import yeni_uyeler
        from calisanlar import tum_calisanlar
        kayitlilar = tum_calisanlar()
        kayitli_idler = {str(k) for k in kayitlilar.keys() if k > 0}
        sonuc = []
        for uid, bilgi in yeni_uyeler.items():
            if str(uid) not in kayitli_idler:
                sonuc.append({
                    "user_id": uid,
                    "ad": bilgi.get("ad", f"Kullanici {uid}"),
                    "username": bilgi.get("username", "")
                })
        return jsonify(sonuc)
    except Exception as e:
        return jsonify([])


@app.route("/panel/api/bekleyen-bildir", methods=["POST"])
def api_bekleyen_bildir():
    """Sistemde olmayan kullaniciya Telegram uzerinden eğitim daveti gonder."""
    if not session.get("panel_giris"): return jsonify({"basarili":False}), 401
    veri = request.get_json()
    uid = int(veri.get("user_id", 0))
    ad = veri.get("ad", "")
    if not uid: return jsonify({"basarili":False,"hata":"Gecersiz ID"})

    from durum import gunun_egitim_id, aktif_egitim_set, siradaki_egitim_al
    from config import EGITIMLER, BOT_USERNAME
    egitim_id = gunun_egitim_id()
    if not egitim_id:
        egitim_id, _ = siradaki_egitim_al()
    egitim = EGITIMLER.get(egitim_id, {})
    aktif_egitim_set(egitim_id)

    token = os.environ.get("TELEGRAM_BOT_TOKEN","")
    base = f"https://api.telegram.org/bot{token}"
    bot_link = f"https://t.me/{BOT_USERNAME}?start=egitim_{egitim_id}"

    import requests as req_lib
    try:
        req_lib.post(f"{base}/sendMessage", json={
            "chat_id": uid,
            "text": (
                f"Merhaba {ad}!\n\n"
                f"Is basi egitim sistemine hosgeldiniz.\n"
                f"Bugunun egitimi: *{egitim.get('baslik','')}*\n\n"
                f"Egitime baslamak icin asagidaki butona basin:"
            ),
            "parse_mode": "Markdown",
            "reply_markup": {"inline_keyboard":[[
                {"text": "Egitime Basla", "url": bot_link}
            ]]}
        }, timeout=10)
        return jsonify({"basarili":True})
    except Exception as e:
        return jsonify({"basarili":False,"hata":str(e)})


@app.route("/panel/api/kayit-butonu-gonder", methods=["POST"])
def api_kayit_butonu_gonder():
    """Gruba kayit butonu gonder."""
    if not session.get("panel_giris"): return jsonify({"basarili":False}),401
    from config import GRUP_ID, BOT_USERNAME
    token = os.environ.get("TELEGRAM_BOT_TOKEN","")
    base = f"https://api.telegram.org/bot{token}"
    kayit_link = f"https://t.me/{BOT_USERNAME}?start=kayit"
    import requests as req_lib
    try:
        resp = req_lib.post(f"{base}/sendMessage", json={
            "chat_id": GRUP_ID,
            "text": (
                "Sisteme kayitli degilseniz asagidaki butona basin.\n\n"
                "Dogum tarihinizi girerek 1 dakikada kaydinizi tamamlayabilirsiniz. "
                "Kayit sonrasi gunluk egitim bildirimleri otomatik gelecektir."
            ),
            "reply_markup": {"inline_keyboard": [[
                {"text": "Sisteme Kayit Ol", "url": kayit_link}
            ]]}
        }, timeout=10)
        result = resp.json()
        if result.get("ok"):
            return jsonify({"basarili":True})
        return jsonify({"basarili":False,"hata":result.get("description","")})
    except Exception as e:
        return jsonify({"basarili":False,"hata":str(e)})


@app.route("/panel/api/firmalar-detay")
def api_firmalar_detay():
    """Firma kartlari icin istatistikli liste."""
    if not session.get("panel_giris"): return jsonify([]), 401
    try:
        from firma_manager import tum_firmalar
        from durum import bugun_tamamlayanlar
        firmalar = tum_firmalar(force=True)
        bugun = date.today().strftime("%d.%m.%Y")
        bugun_tamamlayan_listesi = bugun_tamamlayanlar(bugun)
        sonuc = []
        for fid, f in firmalar.items():
            try:
                calisanlar = tum_calisanlar(fid)
                kayitlar = tum_kayitlar_getir(fid)
                bugun_gecti = sum(1 for k in kayitlar
                    if k.get("tarih") == bugun and k.get("durum") in ("GECTI","GECTİ"))
            except:
                calisanlar = {}
                kayitlar = []
                bugun_gecti = 0
            sonuc.append({
                "firma_id": fid,
                "ad": f["ad"],
                "grup_id": f.get("grup_id", 0),
                "calisan_sayisi": len(calisanlar),
                "bugun_tamamlayan": bugun_gecti,
                "toplam_kayit": len(kayitlar)
            })
        return jsonify(sonuc)
    except Exception as e:
        return jsonify([])


@app.route("/panel/api/firmalar")
def api_firmalar():
    if not session.get("panel_giris"): return jsonify([]), 401
    try:
        from firma_manager import tum_firmalar, _cache
        firmalar = tum_firmalar(force=True)
        return jsonify([
            {"firma_id": fid, "ad": f["ad"], "grup_id": f["grup_id"]}
            for fid, f in firmalar.items()
        ])
    except Exception as e:
        return jsonify([{"firma_id": "varsayilan", "ad": "Varsayılan", "grup_id": 0}])


@app.route("/panel/api/firma-sil", methods=["POST"])
def api_firma_sil():
    if not session.get("panel_giris"): return jsonify({"basarili":False}),401
    veri = request.get_json()
    firma_id = veri.get("firma_id","").strip()
    if firma_id == "varsayilan":
        return jsonify({"basarili":False,"hata":"Varsayılan firma silinemez"})
    try:
        from firma_manager import firma_sil
        firma_sil(firma_id)
        return jsonify({"basarili":True})
    except Exception as e:
        return jsonify({"basarili":False,"hata":str(e)})


@app.route("/panel/api/firma-guncelle", methods=["POST"])
def api_firma_guncelle():
    if not session.get("panel_giris"): return jsonify({"basarili":False}),401
    veri = request.get_json()
    firma_id = veri.get("firma_id","").strip()
    ad = veri.get("ad","").strip()
    grup_id_str = str(veri.get("grup_id","")).strip()
    if not firma_id or not ad:
        return jsonify({"basarili":False,"hata":"Eksik bilgi"})
    try:
        from firma_manager import tum_firmalar, _servis, FIRMALAR_SEKME
        s, sid = _servis()
        r = s.values().get(spreadsheetId=sid, range=f"{FIRMALAR_SEKME}!A2:F").execute()
        for i, satir in enumerate(r.get("values",[])):
            if satir and satir[0].strip() == firma_id:
                satir_no = i + 2
                grup_id = int(grup_id_str) if grup_id_str else (int(satir[2]) if len(satir)>2 and satir[2] else 0)
                mevcut = list(satir) + [""]*6
                mevcut[1] = ad
                mevcut[2] = str(grup_id)
                s.values().update(spreadsheetId=sid, range=f"{FIRMALAR_SEKME}!A{satir_no}",
                    valueInputOption="RAW", body={"values":[mevcut[:6]]}).execute()
                tum_firmalar(force=True)
                return jsonify({"basarili":True})
        return jsonify({"basarili":False,"hata":"Firma bulunamadi"})
    except Exception as e:
        return jsonify({"basarili":False,"hata":str(e)})


@app.route("/panel/api/firma-ekle", methods=["POST"])
def api_firma_ekle():
    if not session.get("panel_giris"): return jsonify({"basarili":False}), 401
    veri = request.get_json()
    ad = veri.get("ad","").strip()
    grup_id_str = str(veri.get("grup_id","")).strip()

    if not ad or not grup_id_str:
        return jsonify({"basarili":False,"hata":"Ad ve grup ID zorunlu"})

    try:
        grup_id = int(grup_id_str)
    except:
        return jsonify({"basarili":False,"hata":"Geçersiz grup ID formatı"})

    # Firma ID olustur (Turkce karaktersiz, kucuk harf)
    import re, unicodedata
    firma_id = unicodedata.normalize('NFKD', ad.lower())
    firma_id = firma_id.encode('ascii','ignore').decode('ascii')
    firma_id = re.sub(r'[^a-z0-9]', '_', firma_id)
    firma_id = re.sub(r'_+', '_', firma_id).strip('_')[:20]

    try:
        from firma_manager import firma_ekle, tum_firmalar
        mevcut = tum_firmalar(force=True)
        # Ayni grup_id zaten var mi?
        for fid, f in mevcut.items():
            if str(f.get("grup_id","")) == str(grup_id):
                return jsonify({"basarili":False,"hata":f"Bu grup ID zaten '{f['ad']}' firmasına kayıtlı"})
        # Ayni firma_id var mi?
        orijinal_id = firma_id
        sayac = 2
        while firma_id in mevcut:
            firma_id = f"{orijinal_id}_{sayac}"
            sayac += 1
        firma_ekle(firma_id, ad, grup_id)
        return jsonify({"basarili":True,"firma_id":firma_id})
    except Exception as e:
        return jsonify({"basarili":False,"hata":str(e)})


@app.route("/panel/api/toplu-islem", methods=["POST"])
def api_toplu_islem():
    """Egitimi tum veya secili calisanlar icin tamamlandi/sifirla."""
    if not session.get("panel_giris"): return jsonify({"basarili":False}), 401
    veri = request.get_json()
    egitim_id = veri.get("egitim_id","").strip()
    islem = veri.get("islem","tamamlandi")  # 'tamamlandi' veya 'sifirla'
    kapsam = veri.get("kapsam","hepsi")
    telegram_idler = veri.get("telegram_idler",[])
    firma_id = veri.get("firma_id","varsayilan")

    if not egitim_id:
        return jsonify({"basarili":False,"hata":"Egitim ID eksik"})

    egitim = EGITIMLER.get(egitim_id)
    if not egitim:
        return jsonify({"basarili":False,"hata":"Egitim bulunamadi"})

    # Calisan listesini al
    calisanlar = tum_calisanlar(firma_id)
    if kapsam == "secili" and telegram_idler:
        hedef_idler = [tid for tid in calisanlar.keys() if tid in telegram_idler]
    else:
        hedef_idler = list(calisanlar.keys())

    etkilenen = 0
    try:
        from durum import tamamlandi_kaydet, tekrar_izni_ver
        from sheets import kayit_ekle
        bugun = date.today().strftime("%d.%m.%Y")

        for tid in hedef_idler:
            c = calisanlar.get(tid, {})
            if islem == "tamamlandi":
                # Sheets'e gecti kaydı ekle
                kayit_ekle({
                    "tarih": bugun,
                    "saat": "00:00",
                    "ad_soyad": c.get("ad_soyad",""),
                    "telegram_id": str(tid),
                    "gorev": c.get("gorev",""),
                    "egitim_konusu": egitim.get("baslik",egitim_id),
                    "egitim_turu": egitim.get("tur",""),
                    "puan": "100",
                    "durum": "GECTI",
                    "kimlik_dogrulandi": "TOPLU",
                    "dogum_yili": c.get("dogum_tarihi","").split(".")[-1],
                    "deneme_no": "1"
                }, firma_id)
                tamamlandi_kaydet(tid, egitim_id)
            elif islem == "sifirla":
                # durum.json'dan kaldir
                tekrar_izni_ver(tid, egitim_id)
            etkilenen += 1

        return jsonify({"basarili":True,"etkilenen":etkilenen})
    except Exception as e:
        return jsonify({"basarili":False,"hata":str(e)})


@app.route("/panel/api/davetler")
def api_davetler():
    if not session.get("panel_giris"): return jsonify({"hata":"giris yok"}),401
    firma_id = request.args.get("firma_id","varsayilan")
    try:
        from davetler import tum_davetler
        return jsonify(tum_davetler(firma_id))
    except Exception as e:
        logger.error(f"Davetler API hatasi: {e}")
        return jsonify({"hata":str(e)}), 500


@app.route("/panel/api/davet-ekle", methods=["POST"])
def api_davet_ekle():
    if not session.get("panel_giris"): return jsonify({"basarili":False}),401
    veri = request.get_json()
    ad = veri.get("ad_soyad","").strip()
    tel = veri.get("telefon","").strip()
    firma_id = veri.get("firma_id","varsayilan")
    if not ad or not tel:
        return jsonify({"basarili":False,"hata":"Ad ve telefon zorunlu"})
    try:
        from davetler import davet_ekle
        sonuc = davet_ekle(ad, tel, firma_id)
        if "hata" in sonuc:
            return jsonify({"basarili":False,"hata":sonuc["hata"]})
        return jsonify({"basarili":True})
    except Exception as e:
        return jsonify({"basarili":False,"hata":str(e)})


@app.route("/panel/api/davet-gonderildi", methods=["POST"])
def api_davet_gonderildi():
    if not session.get("panel_giris"): return jsonify({"basarili":False}),401
    veri = request.get_json()
    satir_no = veri.get("satir_no")
    firma_id = veri.get("firma_id","varsayilan")
    try:
        from davetler import davet_gonderildi_isaretle
        davet_gonderildi_isaretle(satir_no, firma_id)
        return jsonify({"basarili":True})
    except Exception as e:
        return jsonify({"basarili":False,"hata":str(e)})


@app.route("/panel/api/davet-sil", methods=["POST"])
def api_davet_sil():
    if not session.get("panel_giris"): return jsonify({"basarili":False}),401
    veri = request.get_json()
    satir_no = veri.get("satir_no")
    firma_id = veri.get("firma_id","varsayilan")
    try:
        from davetler import davet_sil
        davet_sil(satir_no, firma_id)
        return jsonify({"basarili":True})
    except Exception as e:
        return jsonify({"basarili":False,"hata":str(e)})


@app.route("/panel/api/davet-ayarlari")
def api_davet_ayarlari():
    if not session.get("panel_giris"): return jsonify({"giris":"yok"}),401
    try:
        import os
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
        creds = Credentials.from_service_account_file(
            os.environ.get("GOOGLE_CREDENTIALS_PATH","credentials.json"),
            scopes=["https://www.googleapis.com/auth/spreadsheets"])
        s = build("sheets","v4",credentials=creds).spreadsheets()
        sid = os.environ.get("SPREADSHEET_ID")
        r = s.values().get(spreadsheetId=sid, range="Ayarlar!A1:B20").execute()
        ayarlar = {}
        for satir in r.get("values",[]):
            if satir and len(satir) >= 2:
                ayarlar[str(satir[0]).strip()] = str(satir[1]).strip()
            elif satir and len(satir) == 1:
                ayarlar[str(satir[0]).strip()] = ""
        from config import BOT_USERNAME
        return jsonify({
            "grup_link": ayarlar.get("grup_link",""),
            "admin_tel": ayarlar.get("admin_tel",""),
            "bot_username": BOT_USERNAME,
            "tum_ayarlar": ayarlar
        })
    except Exception as e:
        logger.error(f"Davet ayarlari hatasi: {e}")
        return jsonify({"grup_link":"","admin_tel":"","hata":str(e)})


@app.route("/panel/api/firma-grup-linki")
def api_firma_grup_linki():
    if not session.get("panel_giris"): return jsonify({}),401
    firma_id = request.args.get("firma_id","varsayilan")
    try:
        from firma_manager import tum_firmalar
        firma = tum_firmalar().get(firma_id, {})
        grup_id = firma.get("grup_id", 0)
        from durum import _sheets_index_oku
        ayarlar = _sheets_index_oku()
        link = ayarlar.get(f"grup_link_{firma_id}") or ayarlar.get("grup_link") or ""
        admin_tel = ayarlar.get("admin_tel") or ""
        from config import BOT_USERNAME
        return jsonify({"link": link, "grup_id": grup_id, "bot_username": BOT_USERNAME, "admin_tel": admin_tel})
    except Exception as e:
        from config import BOT_USERNAME
        return jsonify({"link":"","bot_username":BOT_USERNAME,"admin_tel":""})


@app.route("/panel/api/ayar-kaydet", methods=["POST"])
def api_ayar_kaydet():
    """Ayarlar sekmesine anahtar-deger cifti kaydet."""
    if not session.get("panel_giris"): return jsonify({"basarili":False}),401
    veri = request.get_json()
    anahtar = veri.get("anahtar","").strip()
    deger = veri.get("deger","").strip()
    if not anahtar:
        return jsonify({"basarili":False,"hata":"Anahtar bos"})
    try:
        from sheets import _servis
        s, sid = _servis()
        # Mevcut satirlari oku
        try:
            r = s.values().get(spreadsheetId=sid, range="Ayarlar!A1:B20").execute()
            satirlar = r.get("values",[])
        except:
            satirlar = []
        # Guncelle veya ekle
        guncellendi = False
        for i, satir in enumerate(satirlar):
            if satir and satir[0].strip() == anahtar:
                satir_no = i + 1
                s.values().update(spreadsheetId=sid, range=f"Ayarlar!A{satir_no}:B{satir_no}",
                    valueInputOption="RAW", body={"values":[[anahtar, deger]]}).execute()
                guncellendi = True
                break
        if not guncellendi:
            s.values().append(spreadsheetId=sid, range="Ayarlar!A1",
                valueInputOption="RAW", insertDataOption="INSERT_ROWS",
                body={"values":[[anahtar, deger]]}).execute()
        return jsonify({"basarili":True})
    except Exception as e:
        return jsonify({"basarili":False,"hata":str(e)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",8080)))
