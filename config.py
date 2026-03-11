"""
Yapılandırma — Eğitim içerikleri ve sistem ayarları
Yeni eğitim eklemek için bu dosyayı düzenleyin.
"""

# ─────────────────────────────────────────
# SİSTEM AYARLARI
# ─────────────────────────────────────────

GECME_NOTU = 70          # 100 üzerinden minimum geçme puanı
SORU_SAYISI = 5          # Her eğitimdeki soru sayısı
ADMIN_IDS = [            # Telegram User ID'leri — admin yetkisi
    1424268115,          # Admin
]

# Google Sheets
SPREADSHEET_ID = "BURAYA_SPREADSHEET_ID_GIRIN"   # Google Sheets URL'inden alınır
SHEET_NAME = "Egitim_Kayitlari"

# ─────────────────────────────────────────
# EĞİTİM İÇERİKLERİ
# Her gün /egitim_gonder komutuyla bir eğitim seçilip gönderilir.
# Yeni eğitim eklemek için aşağıdaki yapıyı kopyalayıp doldurun.
# ─────────────────────────────────────────

EGITIMLER = {

    "forklift_guvenligi": {
        "baslik": "🚜 Forklift Güvenliği",
        "tur": "İş Güvenliği",
        "sure": "~15 dakika",
        "metin": """
📋 *FORKLIFT GÜVENLİĞİ EĞİTİMİ*

Forklift operasyonunda güvenlik, iş kazalarının önlenmesi açısından kritik öneme sahiptir.

*1. Kullanım Öncesi Kontrol*
Forklift kullanmadan önce günlük kontrol listesini eksiksiz doldurunuz. Fren, direksiyon, sinyal ve uyarı sistemleri çalışır durumda olmalıdır.

*2. Emniyet Kemeri*
Araç içinde emniyet kemeri her zaman takılı olmalıdır. Bu kurala istisna yoktur.

*3. Yük Taşıma*
Maksimum yük kapasitesini asla aşmayınız. Yük taşırken görüş alanınız daralır; gerektiğinde geri geri gidiniz.

*4. Yaya Güzergahları*
Forklift ile yaya güzergahlarının kesiştiği noktalarda *tam duruş* yapılması zorunludur. Önce yayaları geçirin.

*5. Hız Limiti*
Kapalı alan hız limiti saatte 10 km'dir. Islak veya kaygan zeminlerde daha yavaş gidiniz.

*6. Park Etme*
Aracı park ederken çatalları yere indirin, el frenini çekin ve motoru kapatın.

━━━━━━━━━━━━━━━━━━━━
Metni okuduktan sonra sınava geçebilirsiniz.
        """,
        "sorular": [
            {
                "soru": "Forklift kullanmadan önce ne yapılmalıdır?",
                "secenekler": [
                    "Günlük kontrol listesi doldurulmalıdır",
                    "Doğrudan yük alınmalıdır",
                    "Şef onayı beklenir",
                    "Sadece yakıt kontrol edilir"
                ],
                "dogru": 0   # 0'dan başlayan index — A şıkkı doğru
            },
            {
                "soru": "Yaya güzergahlarında forklift ne yapmalıdır?",
                "secenekler": [
                    "Hızla geçiş yapar",
                    "Korna çalarak ilerler",
                    "Tam duruş yapar",
                    "Işıklı uyarı verir"
                ],
                "dogru": 2   # C şıkkı
            },
            {
                "soru": "Kapalı alanda forklift hız limiti nedir?",
                "secenekler": [
                    "20 km/s",
                    "15 km/s",
                    "10 km/s",
                    "5 km/s"
                ],
                "dogru": 2
            },
            {
                "soru": "Forklift park edilirken çatallar ne durumda olmalıdır?",
                "secenekler": [
                    "Yüksekte bekletilir",
                    "Yere indirilir",
                    "Orta seviyede tutulur",
                    "Fark etmez"
                ],
                "dogru": 1
            },
            {
                "soru": "Emniyet kemeri kuralı için hangisi doğrudur?",
                "secenekler": [
                    "Kısa mesafelerde gerekli değil",
                    "Sadece ağır yük taşırken takılır",
                    "Her zaman takılı olmalıdır",
                    "Şoförün tercihine bırakılmış"
                ],
                "dogru": 2
            }
        ]
    },

    "kke_kullanimi": {
        "baslik": "🦺 Kişisel Koruyucu Ekipman (KKE)",
        "tur": "İş Güvenliği",
        "sure": "~12 dakika",
        "metin": """
📋 *KİŞİSEL KORUYUCU EKİPMAN EĞİTİMİ*

Kişisel koruyucu ekipmanlar, iş kazaları ve meslek hastalıklarına karşı son savunma hattınızdır.

*1. Baret*
Baş yaralanmalarına karşı koruma sağlar. Hasar görmüş baret kullanılmaz, derhal değiştirilir.

*2. Güvenlik Ayakkabısı*
Çelik burunlu güvenlik ayakkabısı her çalışma alanında zorunludur. Spor ayakkabı ile çalışma yasaktır.

*3. Koruyucu Gözlük*
Kimyasal sıçrama ve talaş riski olan tüm operasyonlarda gözlük takılmalıdır.

*4. İş Eldiveni*
Kesici, aşındırıcı ve kimyasal maddelerle çalışırken uygun eldiven kullanınız.

*5. İşitme Koruyucu*
85 dB üzeri gürültülü ortamlarda kulak tıkacı veya kulaklık zorunludur.

━━━━━━━━━━━━━━━━━━━━
        """,
        "sorular": [
            {
                "soru": "Hasar görmüş baret ne zaman değiştirilmelidir?",
                "secenekler": [
                    "6 ayda bir",
                    "Hasar tespit edildiği anda",
                    "Yılda bir",
                    "Yönetici onayından sonra"
                ],
                "dogru": 1
            },
            {
                "soru": "Hangi ortamda işitme koruyucu zorunludur?",
                "secenekler": [
                    "50 dB üzeri",
                    "70 dB üzeri",
                    "85 dB üzeri",
                    "100 dB üzeri"
                ],
                "dogru": 2
            },
            {
                "soru": "Güvenlik ayakkabısı hakkında hangisi doğrudur?",
                "secenekler": [
                    "Spor ayakkabı ile çalışılabilir",
                    "Sadece ağır işlerde gerekli",
                    "Her çalışma alanında zorunludur",
                    "Tercihе bırakılmıştır"
                ],
                "dogru": 2
            },
            {
                "soru": "Koruyucu gözlük ne zaman takılmalıdır?",
                "secenekler": [
                    "Sadece kimyasal çalışmalarda",
                    "Kimyasal sıçrama ve talaş riski olan tüm operasyonlarda",
                    "Yalnızca kaynak işlemlerinde",
                    "Zorunlu değil"
                ],
                "dogru": 1
            },
            {
                "soru": "KKE'nin temel amacı nedir?",
                "secenekler": [
                    "Çalışanı şık göstermek",
                    "Firma imajını korumak",
                    "İş kazası ve meslek hastalıklarına karşı koruma",
                    "Denetim geçmek"
                ],
                "dogru": 2
            }
        ]
    },

    # ─── YENİ EĞİTİM ŞABLONU ───────────────────────────────
    # "egitim_anahtar_adi": {
    #     "baslik": "📋 Eğitim Başlığı",
    #     "tur": "Tür",
    #     "sure": "~XX dakika",
    #     "metin": "Eğitim metni buraya...",
    #     "sorular": [
    #         {
    #             "soru": "Soru metni?",
    #             "secenekler": ["A", "B", "C", "D"],
    #             "dogru": 0
    #         },
    #     ]
    # },
}
