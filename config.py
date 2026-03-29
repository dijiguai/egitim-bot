"""
Yapılandırma — Eğitim içerikleri ve sistem ayarları
"""

GECME_NOTU = 70

# Botun Telegram kullanici adi (@olmadan) — @BotFather'dan ogrenilir
BOT_USERNAME = "toolbox_egitim_bot"  # <- BURAYA BOTUN KULLANICI ADINI YAZ
ADMIN_IDS = [1424268115]

# Telegram grup ID
GRUP_ID = -1003774513585  # Telegram grup ID

# Calisanlar { telegram_id: { ad_soyad, dogum_tarihi, gorev } }
CALISANLAR = {
    # 1424268115: {
    #     "ad_soyad": "Ad Soyad",
    #     "dogum_tarihi": "GG.AA.YYYY",
    #     "gorev": "Gorev"
    # },
}

SPREADSHEET_ID = "1SQ2elAYL2NrJFrbiJYF10m1ra7lP5vt9sMy9zCQ1538"
SHEET_NAME = "Sayfa1"

EGITIMLER = {}  # Sheets'ten yüklenir — egitimler_sheets.py
