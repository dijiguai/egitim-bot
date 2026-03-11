"""
Yönetici Paneli — Flask web uygulaması
Bot ile aynı sunucuda çalışır, /panel adresinden erişilir.
"""

from flask import Flask, render_template_string, jsonify, request, session, redirect
from datetime import date, timedelta
import os
from sheets import kayitlari_getir, tum_kayitlar_getir
from config import EGITIMLER

app = Flask(__name__)
app.secret_key = os.environ.get("PANEL_SECRET_KEY", "egitimbot2026")

PANEL_SIFRE = os.environ.get("PANEL_SIFRE", "admin123")  # Railway'de değiştir!

HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Eğitim Yönetici Paneli</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
:root {
  --bg: #f5f3ef;
  --card: #ffffff;
  --dark: #1a1a18;
  --accent: #e85c2e;
  --accent2: #2e7de8;
  --green: #27a86e;
  --red: #e83a2e;
  --yellow: #e8b82e;
  --border: #e2ddd6;
  --muted: #8c8780;
  --text: #2a2a28;
}
body {
  background: var(--bg);
  color: var(--text);
  font-family: 'DM Sans', sans-serif;
  min-height: 100vh;
}

/* LOGIN */
.login-wrap {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--dark);
}
.login-box {
  background: #242420;
  border: 1px solid #333;
  border-radius: 16px;
  padding: 40px;
  width: 340px;
}
.login-title {
  font-family: 'Syne', sans-serif;
  font-size: 22px;
  font-weight: 800;
  color: #fff;
  margin-bottom: 6px;
}
.login-sub { font-size: 13px; color: #666; margin-bottom: 28px; }
.login-box input {
  width: 100%;
  background: #1a1a18;
  border: 1px solid #333;
  border-radius: 10px;
  padding: 12px 16px;
  color: #fff;
  font-size: 14px;
  margin-bottom: 12px;
  outline: none;
  font-family: 'DM Sans', sans-serif;
}
.login-box input:focus { border-color: var(--accent); }
.login-btn {
  width: 100%;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: 10px;
  padding: 13px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  font-family: 'Syne', sans-serif;
}
.login-err { color: var(--red); font-size: 12px; margin-top: 8px; text-align: center; }

/* HEADER */
.header {
  background: var(--dark);
  padding: 0 24px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  z-index: 100;
}
.header-logo {
  font-family: 'Syne', sans-serif;
  font-weight: 800;
  font-size: 16px;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 10px;
}
.logo-dot {
  width: 8px; height: 8px;
  background: var(--accent);
  border-radius: 50%;
  animation: pulse 2s infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.3); }
}
.header-right { display: flex; align-items: center; gap: 12px; }
.header-date { font-size: 12px; color: #666; font-family: 'DM Sans', sans-serif; }
.logout-btn {
  background: #333;
  color: #aaa;
  border: none;
  border-radius: 8px;
  padding: 6px 14px;
  font-size: 12px;
  cursor: pointer;
}

/* MAIN */
.main { padding: 24px; max-width: 1100px; margin: 0 auto; }

/* FILTERS */
.filters {
  display: flex;
  gap: 10px;
  margin-bottom: 24px;
  flex-wrap: wrap;
  align-items: center;
}
.filter-group { display: flex; flex-direction: column; gap: 4px; }
.filter-label { font-size: 10px; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; }
select, input[type=date] {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 13px;
  color: var(--text);
  outline: none;
  font-family: 'DM Sans', sans-serif;
  cursor: pointer;
}
select:focus, input[type=date]:focus { border-color: var(--accent); }
.filter-btn {
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 9px 20px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  align-self: flex-end;
  font-family: 'Syne', sans-serif;
}

/* STATS */
.stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 24px; }
@media (max-width: 640px) { .stats { grid-template-columns: repeat(2, 1fr); } }
.stat {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 20px;
  position: relative;
  overflow: hidden;
}
.stat::after {
  content: '';
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 3px;
  background: var(--accent);
}
.stat.green::after { background: var(--green); }
.stat.red::after { background: var(--red); }
.stat.blue::after { background: var(--accent2); }
.stat-label { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; }
.stat-val { font-family: 'Syne', sans-serif; font-size: 36px; font-weight: 800; line-height: 1; }
.stat-val.green { color: var(--green); }
.stat-val.red { color: var(--red); }
.stat-val.blue { color: var(--accent2); }
.stat-val.orange { color: var(--accent); }
.stat-sub { font-size: 12px; color: var(--muted); margin-top: 6px; }

/* SECTIONS */
.section-title {
  font-family: 'Syne', sans-serif;
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  color: var(--muted);
  margin-bottom: 14px;
  margin-top: 28px;
}

/* TABLE */
.table-wrap {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 14px;
  overflow: hidden;
  overflow-x: auto;
}
table { width: 100%; border-collapse: collapse; font-size: 13px; min-width: 600px; }
th {
  background: #f9f7f4;
  padding: 11px 16px;
  text-align: left;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--muted);
  font-weight: 600;
  border-bottom: 1px solid var(--border);
  white-space: nowrap;
}
td {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
  color: var(--text);
}
tr:last-child td { border-bottom: none; }
tr:hover td { background: #faf8f5; }
.pill {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 600;
}
.pill-gecti { background: #e8f7f0; color: var(--green); }
.pill-kaldi { background: #fdecea; color: var(--red); }
.puan-yuksek { color: var(--green); font-weight: 700; }
.puan-dusuk { color: var(--red); font-weight: 700; }

/* CALISAN KARTI */
.calisan-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 14px; }
.calisan-kart {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.15s;
}
.calisan-kart:hover { border-color: var(--accent); transform: translateY(-1px); }
.calisan-ad { font-family: 'Syne', sans-serif; font-weight: 700; font-size: 15px; margin-bottom: 4px; }
.calisan-gorev { font-size: 12px; color: var(--muted); margin-bottom: 14px; }
.calisan-stats { display: flex; gap: 16px; }
.calisan-stat-item { text-align: center; }
.calisan-stat-val { font-family: 'Syne', sans-serif; font-size: 20px; font-weight: 800; }
.calisan-stat-lbl { font-size: 10px; color: var(--muted); margin-top: 2px; }

/* EGITIM ISTATISTIK */
.egitim-satir {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 16px;
}
.egitim-baslik { font-weight: 600; font-size: 14px; flex: 1; }
.egitim-meta { font-size: 12px; color: var(--muted); }
.bar-wrap { flex: 1; background: #f0ede8; border-radius: 4px; height: 8px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 4px; background: var(--green); transition: width 0.5s; }
.bar-fill.dusuk { background: var(--red); }
.bar-fill.orta { background: var(--yellow); }
.bar-pct { font-family: 'Syne', sans-serif; font-size: 14px; font-weight: 700; min-width: 45px; text-align: right; }

/* LOADING */
.loading { text-align: center; padding: 60px; color: var(--muted); font-size: 14px; }
.spinner {
  width: 32px; height: 32px;
  border: 3px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 16px;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* EMPTY */
.empty { text-align: center; padding: 48px; color: var(--muted); }
.empty-icon { font-size: 40px; margin-bottom: 12px; }

/* RESPONSIVE */
@media (max-width: 480px) {
  .main { padding: 16px; }
  .header { padding: 0 16px; }
  .filters { flex-direction: column; align-items: stretch; }
  .filter-btn { width: 100%; text-align: center; }
}
</style>
</head>
<body>

{% if not logged_in %}
<div class="login-wrap">
  <div class="login-box">
    <div class="login-title">Yönetici Girişi</div>
    <div class="login-sub">İş Başı Eğitim Paneli</div>
    <form method="POST" action="/panel/login">
      <input type="password" name="sifre" placeholder="Şifre" autofocus>
      {% if hata %}<div class="login-err">⚠️ Yanlış şifre</div>{% endif %}
      <button class="login-btn" type="submit">Giriş Yap</button>
    </form>
  </div>
</div>

{% else %}
<div class="header">
  <div class="header-logo">
    <div class="logo-dot"></div>
    Eğitim Paneli
  </div>
  <div class="header-right">
    <span class="header-date" id="bugun-label"></span>
    <a href="/panel/cikis"><button class="logout-btn">Çıkış</button></a>
  </div>
</div>

<div class="main">

  <!-- FİLTRELER -->
  <div class="filters">
    <div class="filter-group">
      <span class="filter-label">Başlangıç</span>
      <input type="date" id="tarih-bas" value="">
    </div>
    <div class="filter-group">
      <span class="filter-label">Bitiş</span>
      <input type="date" id="tarih-bitis" value="">
    </div>
    <div class="filter-group">
      <span class="filter-label">Durum</span>
      <select id="durum-filtre">
        <option value="">Tümü</option>
        <option value="GEÇTİ">Geçti</option>
        <option value="KALDI">Kaldı</option>
      </select>
    </div>
    <button class="filter-btn" onclick="verileriYukle()">Filtrele</button>
    <button class="filter-btn" style="background:#555" onclick="bugunSec()">Bugün</button>
  </div>

  <!-- STATS -->
  <div class="stats">
    <div class="stat orange">
      <div class="stat-label">Toplam Kayıt</div>
      <div class="stat-val orange" id="st-toplam">—</div>
      <div class="stat-sub">Seçili dönem</div>
    </div>
    <div class="stat green">
      <div class="stat-label">Geçti</div>
      <div class="stat-val green" id="st-gecti">—</div>
      <div class="stat-sub" id="st-oran">—</div>
    </div>
    <div class="stat red">
      <div class="stat-label">Kaldı</div>
      <div class="stat-val red" id="st-kaldi">—</div>
      <div class="stat-sub">Yeniden eğitim</div>
    </div>
    <div class="stat blue">
      <div class="stat-label">Ort. Puan</div>
      <div class="stat-val blue" id="st-puan">—</div>
      <div class="stat-sub">100 üzerinden</div>
    </div>
  </div>

  <!-- GÜNLÜK TABLO -->
  <div class="section-title">Eğitim Kayıtları</div>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>Tarih</th>
          <th>Saat</th>
          <th>Çalışan</th>
          <th>Görev</th>
          <th>Eğitim Konusu</th>
          <th>Puan</th>
          <th>Durum</th>
          <th>Kimlik</th>
        </tr>
      </thead>
      <tbody id="kayit-tbody">
        <tr><td colspan="8"><div class="loading"><div class="spinner"></div>Yükleniyor...</div></td></tr>
      </tbody>
    </table>
  </div>

  <!-- ÇALIŞAN BAZINDA -->
  <div class="section-title">Çalışan Bazında Geçmiş</div>
  <div class="calisan-grid" id="calisan-grid">
    <div class="loading"><div class="spinner"></div></div>
  </div>

  <!-- EĞİTİM İSTATİSTİK -->
  <div class="section-title">Eğitim Bazında Başarı Oranı</div>
  <div id="egitim-stats">
    <div class="loading"><div class="spinner"></div></div>
  </div>

</div>

<script>
const bugun = new Date().toISOString().split('T')[0];
const bugunTR = new Date().toLocaleDateString('tr-TR', {day:'2-digit',month:'long',year:'numeric'});
document.getElementById('bugun-label').textContent = bugunTR;
document.getElementById('tarih-bas').value = bugun;
document.getElementById('tarih-bitis').value = bugun;

function bugunSec() {
  document.getElementById('tarih-bas').value = bugun;
  document.getElementById('tarih-bitis').value = bugun;
  verileriYukle();
}

async function verileriYukle() {
  const bas = document.getElementById('tarih-bas').value;
  const bitis = document.getElementById('tarih-bitis').value;
  const durum = document.getElementById('durum-filtre').value;

  // Tarihleri TR formatına çevir
  const basTR = bas.split('-').reverse().join('.');
  const bitisTR = bitis.split('-').reverse().join('.');

  // Loading göster
  document.getElementById('kayit-tbody').innerHTML = '<tr><td colspan="8"><div class="loading"><div class="spinner"></div>Yükleniyor...</div></td></tr>';
  document.getElementById('calisan-grid').innerHTML = '<div class="loading"><div class="spinner"></div></div>';
  document.getElementById('egitim-stats').innerHTML = '<div class="loading"><div class="spinner"></div></div>';

  try {
    const res = await fetch(`/panel/api/kayitlar?bas=${basTR}&bitis=${bitisTR}&durum=${encodeURIComponent(durum)}`);
    const data = await res.json();
    renderAll(data);
  } catch(e) {
    document.getElementById('kayit-tbody').innerHTML = '<tr><td colspan="8"><div class="empty"><div class="empty-icon">⚠️</div>Veri yüklenemedi</div></td></tr>';
  }
}

function renderAll(data) {
  const { kayitlar, calisan_ozet, egitim_ozet } = data;

  // Stats
  const toplam = kayitlar.length;
  const gecti = kayitlar.filter(k => k.durum === 'GEÇTİ').length;
  const kaldi = kayitlar.filter(k => k.durum === 'KALDI').length;
  const puanlar = kayitlar.filter(k => k.puan).map(k => parseInt(k.puan) || 0);
  const ortPuan = puanlar.length ? Math.round(puanlar.reduce((a,b)=>a+b,0)/puanlar.length) : 0;
  const oran = toplam ? Math.round((gecti/toplam)*100) : 0;

  document.getElementById('st-toplam').textContent = toplam;
  document.getElementById('st-gecti').textContent = gecti;
  document.getElementById('st-oran').textContent = `%${oran} başarı`;
  document.getElementById('st-kaldi').textContent = kaldi;
  document.getElementById('st-puan').textContent = ortPuan;

  // Tablo
  if (!kayitlar.length) {
    document.getElementById('kayit-tbody').innerHTML = '<tr><td colspan="8"><div class="empty"><div class="empty-icon">📋</div>Bu dönemde kayıt yok</div></td></tr>';
  } else {
    document.getElementById('kayit-tbody').innerHTML = kayitlar.map(k => `
      <tr>
        <td>${k.tarih || '—'}</td>
        <td>${k.saat || '—'}</td>
        <td><strong>${k.ad_soyad || '—'}</strong></td>
        <td style="color:#8c8780;font-size:12px">${k.gorev || '—'}</td>
        <td>${k.egitim_konusu || '—'}</td>
        <td class="${parseInt(k.puan)>=70?'puan-yuksek':'puan-dusuk'}">${k.puan || '—'}</td>
        <td><span class="pill ${k.durum==='GEÇTİ'?'pill-gecti':'pill-kaldi'}">${k.durum || '—'}</span></td>
        <td style="font-size:12px">${k.kimlik_dogrulandi==='EVET'?'✅':'—'}</td>
      </tr>
    `).join('');
  }

  // Çalışan bazında
  if (!calisan_ozet || !Object.keys(calisan_ozet).length) {
    document.getElementById('calisan-grid').innerHTML = '<div class="empty"><div class="empty-icon">👥</div>Veri yok</div>';
  } else {
    document.getElementById('calisan-grid').innerHTML = Object.entries(calisan_ozet).map(([ad, c]) => `
      <div class="calisan-kart">
        <div class="calisan-ad">${ad}</div>
        <div class="calisan-gorev">${c.gorev}</div>
        <div class="calisan-stats">
          <div class="calisan-stat-item">
            <div class="calisan-stat-val" style="color:var(--accent)">${c.toplam}</div>
            <div class="calisan-stat-lbl">Eğitim</div>
          </div>
          <div class="calisan-stat-item">
            <div class="calisan-stat-val" style="color:var(--green)">${c.gecti}</div>
            <div class="calisan-stat-lbl">Geçti</div>
          </div>
          <div class="calisan-stat-item">
            <div class="calisan-stat-val" style="color:var(--red)">${c.kaldi}</div>
            <div class="calisan-stat-lbl">Kaldı</div>
          </div>
          <div class="calisan-stat-item">
            <div class="calisan-stat-val" style="color:var(--accent2)">${c.ort_puan}</div>
            <div class="calisan-stat-lbl">Ort. Puan</div>
          </div>
        </div>
      </div>
    `).join('');
  }

  // Eğitim istatistik
  if (!egitim_ozet || !Object.keys(egitim_ozet).length) {
    document.getElementById('egitim-stats').innerHTML = '<div class="empty"><div class="empty-icon">📊</div>Veri yok</div>';
  } else {
    document.getElementById('egitim-stats').innerHTML = Object.entries(egitim_ozet).map(([konu, e]) => {
      const pct = e.toplam ? Math.round((e.gecti/e.toplam)*100) : 0;
      const cls = pct >= 70 ? '' : pct >= 50 ? 'orta' : 'dusuk';
      return `
        <div class="egitim-satir">
          <div>
            <div class="egitim-baslik">${konu}</div>
            <div class="egitim-meta">${e.toplam} katılım · ${e.gecti} geçti · ${e.kaldi} kaldı</div>
          </div>
          <div class="bar-wrap"><div class="bar-fill ${cls}" style="width:${pct}%"></div></div>
          <div class="bar-pct" style="color:${pct>=70?'var(--green)':pct>=50?'var(--yellow)':'var(--red)'}">${pct}%</div>
        </div>
      `;
    }).join('');
  }
}

// Sayfa açılınca bugünü yükle
verileriYukle();
</script>
{% endif %}
</body>
</html>
"""


@app.route("/panel", methods=["GET"])
def panel():
    logged_in = session.get("panel_giris", False)
    return render_template_string(HTML, logged_in=logged_in, hata=False)


@app.route("/panel/login", methods=["POST"])
def login():
    sifre = request.form.get("sifre", "")
    if sifre == PANEL_SIFRE:
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

    # Tarih filtresi
    def tarih_araliginda(tarih_str):
        try:
            from datetime import datetime
            t = datetime.strptime(tarih_str, "%d.%m.%Y")
            b = datetime.strptime(bas, "%d.%m.%Y") if bas else None
            bi = datetime.strptime(bitis, "%d.%m.%Y") if bitis else None
            if b and t < b: return False
            if bi and t > bi: return False
            return True
        except:
            return True

    filtrelenmis = [k for k in kayitlar if tarih_araliginda(k.get("tarih", ""))]
    if durum_filtre:
        filtrelenmis = [k for k in filtrelenmis if k.get("durum") == durum_filtre]

    # Çalışan özeti
    calisan_ozet = {}
    for k in filtrelenmis:
        ad = k.get("ad_soyad", "Bilinmiyor")
        if ad not in calisan_ozet:
            calisan_ozet[ad] = {"toplam": 0, "gecti": 0, "kaldi": 0, "puanlar": [], "gorev": k.get("gorev", "—")}
        calisan_ozet[ad]["toplam"] += 1
        if k.get("durum") == "GEÇTİ":
            calisan_ozet[ad]["gecti"] += 1
        else:
            calisan_ozet[ad]["kaldi"] += 1
        try:
            calisan_ozet[ad]["puanlar"].append(int(k.get("puan", 0)))
        except:
            pass

    for ad in calisan_ozet:
        puanlar = calisan_ozet[ad]["puanlar"]
        calisan_ozet[ad]["ort_puan"] = round(sum(puanlar)/len(puanlar)) if puanlar else 0
        del calisan_ozet[ad]["puanlar"]

    # Eğitim özeti
    egitim_ozet = {}
    for k in filtrelenmis:
        konu = k.get("egitim_konusu", "Bilinmiyor")
        if konu not in egitim_ozet:
            egitim_ozet[konu] = {"toplam": 0, "gecti": 0, "kaldi": 0}
        egitim_ozet[konu]["toplam"] += 1
        if k.get("durum") == "GEÇTİ":
            egitim_ozet[konu]["gecti"] += 1
        else:
            egitim_ozet[konu]["kaldi"] += 1

    return jsonify({
        "kayitlar": filtrelenmis,
        "calisan_ozet": calisan_ozet,
        "egitim_ozet": egitim_ozet,
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
