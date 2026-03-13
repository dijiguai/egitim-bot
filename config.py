"""
Yapılandırma — Eğitim içerikleri ve sistem ayarları
"""

GECME_NOTU = 70

# Botun Telegram kullanici adi (@olmadan) — @BotFather'dan ogrenilir
BOT_USERNAME = "toolbox_egitim_bot"  # <- BURAYA BOTUN KULLANICI ADINI YAZ
ADMIN_IDS = [1424268115]

# Telegram grup ID
GRUP_ID = -5162987964  # Telegram grup ID

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

EGITIMLER = {

    "forklift_guvenligi": {
        "baslik": "🚜 Forklift Güvenliği",
        "tur": "İş Güvenliği",
        "sure": "~15 dakika",
        "metin": """📋 *FORKLIFT GÜVENLİĞİ EĞİTİMİ*

Forklift operasyonunda güvenlik, iş kazalarının önlenmesi açısından kritik öneme sahiptir.

*1. Kullanım Öncesi Kontrol*
Forklift kullanmadan önce günlük kontrol listesini eksiksiz doldurunuz.

*2. Emniyet Kemeri*
Araç içinde emniyet kemeri her zaman takılı olmalıdır.

*3. Yük Taşıma*
Maksimum yük kapasitesini asla aşmayınız. Yük taşırken görüş alanınız daralır; gerektiğinde geri geri gidiniz.

*4. Yaya Güzergahları*
Yaya güzergahlarında *tam duruş* yapılması zorunludur.

*5. Hız Limiti*
Kapalı alan hız limiti saatte 10 km'dir.""",
        "sorular": [
            {"soru": "Forklift kullanmadan önce ne yapılmalıdır?", "secenekler": ["Günlük kontrol listesi doldurulmalıdır", "Doğrudan yük alınmalıdır", "Şef onayı beklenir", "Sadece yakıt kontrol edilir"], "dogru": 0},
            {"soru": "Yaya güzergahlarında forklift ne yapmalıdır?", "secenekler": ["Hızla geçiş yapar", "Korna çalarak ilerler", "Tam duruş yapar", "Işıklı uyarı verir"], "dogru": 2},
            {"soru": "Kapalı alanda forklift hız limiti nedir?", "secenekler": ["20 km/s", "15 km/s", "10 km/s", "5 km/s"], "dogru": 2},
            {"soru": "Forklift park edilirken çatallar ne durumda olmalıdır?", "secenekler": ["Yüksekte bekletilir", "Yere indirilir", "Orta seviyede tutulur", "Fark etmez"], "dogru": 1},
            {"soru": "Emniyet kemeri kuralı için hangisi doğrudur?", "secenekler": ["Kısa mesafelerde gerekli değil", "Sadece ağır yük taşırken takılır", "Her zaman takılı olmalıdır", "Şoförün tercihine bırakılmış"], "dogru": 2}
        ]
    },

    "kke_kullanimi": {
        "baslik": "🦺 Kişisel Koruyucu Ekipman (KKE)",
        "tur": "İş Güvenliği",
        "sure": "~12 dakika",
        "metin": """📋 *KİŞİSEL KORUYUCU EKİPMAN EĞİTİMİ*

Kişisel koruyucu ekipmanlar iş kazalarına karşı son savunma hattınızdır.

*1. Baret*
Hasar görmüş baret kullanılmaz, derhal değiştirilir.

*2. Güvenlik Ayakkabısı*
Çelik burunlu güvenlik ayakkabısı her alanda zorunludur.

*3. Koruyucu Gözlük*
Kimyasal sıçrama ve talaş riski olan tüm operasyonlarda zorunludur.

*4. İş Eldiveni*
Kesici ve kimyasal maddelerle çalışırken uygun eldiven kullanınız.

*5. İşitme Koruyucu*
85 dB üzeri gürültülü ortamlarda zorunludur.""",
        "sorular": [
            {"soru": "Hasar görmüş baret ne zaman değiştirilmelidir?", "secenekler": ["6 ayda bir", "Hasar tespit edildiği anda", "Yılda bir", "Yönetici onayından sonra"], "dogru": 1},
            {"soru": "Hangi ortamda işitme koruyucu zorunludur?", "secenekler": ["50 dB üzeri", "70 dB üzeri", "85 dB üzeri", "100 dB üzeri"], "dogru": 2},
            {"soru": "Güvenlik ayakkabısı hakkında hangisi doğrudur?", "secenekler": ["Spor ayakkabı ile çalışılabilir", "Sadece ağır işlerde gerekli", "Her çalışma alanında zorunludur", "Tercihe bırakılmıştır"], "dogru": 2},
            {"soru": "Koruyucu gözlük ne zaman takılmalıdır?", "secenekler": ["Sadece kimyasal çalışmalarda", "Kimyasal sıçrama ve talaş riski olan tüm operasyonlarda", "Yalnızca kaynak işlemlerinde", "Zorunlu değil"], "dogru": 1},
            {"soru": "KKE'nin temel amacı nedir?", "secenekler": ["Çalışanı şık göstermek", "Firma imajını korumak", "İş kazası ve meslek hastalıklarına karşı koruma", "Denetim geçmek"], "dogru": 2}
        ]
    },

    "cimento_uretim_sureci": {
        "baslik": "🏭 Çimento Üretim Süreci ve Güvenlik",
        "tur": "Çimento / Üretim",
        "sure": "~15 dakika",
        "metin": """📋 *ÇİMENTO ÜRETİM SÜRECİ VE GÜVENLİK EĞİTİMİ*

*1. Ham Madde Hazırlığı*
Kireçtaşı, kil ve diğer ham maddeler kırıcılarda öğütülür. Kırıcı çevresinde toz maskesi zorunludur. Dönen parçalara kesinlikle el ile müdahale edilmez.

*2. Fırın Operasyonu*
Döner fırınlar 1450°C'ye ulaşır. Fırın bölgesinde ısıya dayanıklı eldiven ve gözlük zorunludur. Fırın çevresinde yetkisiz personel bulundurulamaz.

*3. Klinkerin Soğutulması*
Fırından çıkan klinker soğutucudan geçer. Soğutucu bölgesinde yüksek sıcaklık tehlikesi mevcuttur, uygun KKE kullanılmalıdır.

*4. Öğütme ve Silolar*
Değirmenler yoğun toz üretir. Bu bölgede P3 sınıfı toz maskesi kullanılmalıdır. Silo içine girmek için özel izin ve kapalı alan prosedürü uygulanır.

*5. Sevkiyat*
Çimento yükleme sırasında toz maskesi ve gözlük takılmalıdır.""",
        "sorular": [
            {"soru": "Döner fırın çevresinde hangi KKE zorunludur?", "secenekler": ["Yalnızca baret", "Isıya dayanıklı eldiven ve gözlük", "Yalnızca maske", "KKE gerekmez"], "dogru": 1},
            {"soru": "Silo içine girmek için ne gerekir?", "secenekler": ["Şef onayı yeterli", "Özel izin ve kapalı alan prosedürü", "Sadece maske takmak", "Hiçbir şey gerekmez"], "dogru": 1},
            {"soru": "Çimento öğütme bölgesinde hangi maske kullanılmalıdır?", "secenekler": ["Cerrahi maske", "P1 sınıfı maske", "P3 sınıfı toz maskesi", "Maske gerekmez"], "dogru": 2},
            {"soru": "Döner fırınlar kaç dereceye ulaşır?", "secenekler": ["500°C", "900°C", "1200°C", "1450°C"], "dogru": 3},
            {"soru": "Kırıcı çevresinde çalışırken ne zorunludur?", "secenekler": ["Toz maskesi", "Yalnızca baret", "İşitme koruyucu", "Hiçbir şey"], "dogru": 0}
        ]
    },

    "toz_maruziyeti": {
        "baslik": "😷 Toz Maruziyeti ve Korunma",
        "tur": "Çimento / Sağlık",
        "sure": "~12 dakika",
        "metin": """📋 *TOZ MARUZİYETİ VE KORUNMA EĞİTİMİ*

*1. Çimento Tozu Neden Tehlikelidir?*
Çimento tozu içindeki silis partikülleri akciğerlere yerleşerek silikoz hastalığına yol açabilir. Bu hastalık geri döndürülemez.

*2. Maruziyet Sınırları*
İş yeri toz ölçümleri düzenli yapılmalıdır. Limit değerlerin üzerinde toz varsa çalışma durdurulmalıdır.

*3. Doğru Maske Seçimi*
Cerrahi maske çimento tozuna karşı koruma sağlamaz. En az FFP2 (P2) sınıfı, tercihen FFP3 (P3) sınıfı maske kullanılmalıdır. Maske yüze tam oturmalı, boşluk bırakmamalıdır.

*4. Cilt Korunması*
Islak çimento ciltle temas ettiğinde kimyasal yanık oluşturabilir. Çimento ile doğrudan temas halinde su geçirmez eldiven kullanılmalıdır.

*5. Sağlık Taraması*
Toza maruz kalan çalışanlar yılda bir akciğer grafisi çektirmelidir.""",
        "sorular": [
            {"soru": "Çimento tozu hangi hastalığa yol açabilir?", "secenekler": ["Grip", "Silikoz", "Astım", "Bronşit"], "dogru": 1},
            {"soru": "Çimento tozu için minimum hangi maske kullanılmalıdır?", "secenekler": ["Cerrahi maske", "Bez maske", "FFP2 (P2) sınıfı maske", "Hiçbir şey gerekmez"], "dogru": 2},
            {"soru": "Islak çimento cilde temas ederse ne olur?", "secenekler": ["Renk değişimi", "Kimyasal yanık", "Alerjik reaksiyon", "Hiçbir şey olmaz"], "dogru": 1},
            {"soru": "Toza maruz kalan çalışanlar ne sıklıkla akciğer grafisi çektirmelidir?", "secenekler": ["5 yılda bir", "3 yılda bir", "2 yılda bir", "Yılda bir"], "dogru": 3},
            {"soru": "Silikoz hastalığı hakkında hangisi doğrudur?", "secenekler": ["Tedavisi kolaydır", "Geri döndürülemez", "Antibiyotikle geçer", "Geçici bir hastalıktır"], "dogru": 1}
        ]
    },

    "yuklu_arac_guvenligi": {
        "baslik": "🚛 Yüklü Araç ve Nakliye Güvenliği",
        "tur": "Çimento / Nakliye",
        "sure": "~12 dakika",
        "metin": """📋 *YÜKLÜ ARAÇ VE NAKLİYE GÜVENLİĞİ EĞİTİMİ*

*1. Araç Kabul ve Çıkışı*
Fabrikaya giren tüm araçlar güvenlik noktasında durdurulur. Sürücüler araçtan inmeden önce güvenlik yetkilisinin onayını beklemelidir.

*2. Yükleme Alanı Kuralları*
Yükleme sırasında araç freni çekilmiş olmalıdır. Yükleme tamamlanmadan araç hareket ettirilemez. Çevredeki yaya trafiğine dikkat edilmelidir.

*3. Yük Sabitleme*
Çimento torbası yüklerinde yük örtüsü kullanılması zorunludur. Dökme çimento taşımada tank kapakları kontrol edilmelidir. Aşırı yükleme kesinlikle yasaktır.

*4. Saha İçi Hız*
Fabrika içinde maksimum hız 15 km/saattir. Tüm kavşaklarda tam dur yapılmalıdır.

*5. Gece Operasyonları*
Gece çalışmalarında reflektif yelek zorunludur. Araç aydınlatmaları tam çalışır durumda olmalıdır.""",
        "sorular": [
            {"soru": "Fabrika içinde maksimum hız limiti nedir?", "secenekler": ["10 km/s", "15 km/s", "20 km/s", "30 km/s"], "dogru": 1},
            {"soru": "Yükleme sırasında araç ne durumda olmalıdır?", "secenekler": ["Rölantide çalışır", "Freni çekilmiş", "Motor kapalı", "Fark etmez"], "dogru": 1},
            {"soru": "Gece operasyonlarında ne zorunludur?", "secenekler": ["Sadece far açık olmak", "Reflektif yelek", "İkinci sürücü", "Hiçbir şey"], "dogru": 1},
            {"soru": "Çimento torbası taşımada ne zorunludur?", "secenekler": ["Yük örtüsü", "Ekstra bağlama", "İkinci araç", "Sadece fren"], "dogru": 0},
            {"soru": "Kavşaklarda ne yapılmalıdır?", "secenekler": ["Yavaşlayarak geç", "Tam dur yapılmalıdır", "Korna çal geç", "Hız değiştirme"], "dogru": 1}
        ]
    },

    "kapali_alan_calisma": {
        "baslik": "🕳️ Kapalı Alan Çalışma Güvenliği",
        "tur": "İş Güvenliği",
        "sure": "~15 dakika",
        "metin": """📋 *KAPALI ALAN ÇALIŞMA GÜVENLİĞİ EĞİTİMİ*

Çimento fabrikalarında silolar, değirmenler ve bunkler kapalı alan sayılır. Bu alanlarda çalışma en riskli operasyonlar arasındadır.

*1. İzin Sistemi*
Kapalı alana girmeden önce "Kapalı Alan Çalışma İzni" formu doldurulmalı ve yetkili tarafından imzalanmalıdır.

*2. Gaz Ölçümü*
Girişten önce oksijen, yanıcı gaz ve zehirli gaz ölçümü yapılmalıdır. Oksijen seviyesi %19.5 ile %23.5 arasında olmalıdır.

*3. Gözetçi*
Kapalı alanda çalışan her ekip için dışarıda bir gözetçi bulunmalıdır. Gözetçi alanı terk edemez.

*4. İletişim*
İçerideki çalışan ile gözetçi arasında sürekli iletişim sağlanmalıdır. İletişim kesilirse çalışma derhal durdurulur.

*5. Acil Tahliye*
Tahliye planı önceden belirlenmeli ve tüm ekip tarafından bilinmelidir.""",
        "sorular": [
            {"soru": "Kapalı alana girmeden önce ne yapılmalıdır?", "secenekler": ["Şefe haber ver", "Kapalı Alan Çalışma İzni alınmalıdır", "Sadece maske tak", "Diğer çalışanlara söyle"], "dogru": 1},
            {"soru": "Kapalı alanda oksijen seviyesi kaç olmalıdır?", "secenekler": ["%10-%15", "%15-%19", "%19.5-%23.5", "%25 üzeri"], "dogru": 2},
            {"soru": "Gözetçi ne yapabilir?", "secenekler": ["Kısa süre ayrılabilir", "Alanı terk edemez", "İçeri girebilir", "Başka iş yapabilir"], "dogru": 1},
            {"soru": "İletişim kesilirse ne yapılır?", "secenekler": ["Devam edilir", "Çalışma derhal durdurulur", "Gözetçi içeri girer", "10 dakika beklenir"], "dogru": 1},
            {"soru": "Çimento fabrikasında kapalı alan sayılan yer hangisidir?", "secenekler": ["Ofis", "Yemekhane", "Silo", "Otopark"], "dogru": 2}
        ]
    },

    "yangin_onleme": {
        "baslik": "🔥 Yangın Önleme ve Müdahale",
        "tur": "Acil Durum",
        "sure": "~12 dakika",
        "metin": """📋 *YANGIN ÖNLEME VE MÜDAHALE EĞİTİMİ*

*1. Yangın Üçgeni*
Yangın için üç unsur gerekir: ısı, oksijen ve yakıt. Bu üçünden biri ortadan kaldırılırsa yangın söner.

*2. Yangın Sınıfları*
A Sınıfı: Katı maddeler (odun, kağıt)
B Sınıfı: Sıvı maddeler (akaryakıt, yağ)
C Sınıfı: Gaz yangınları
D Sınıfı: Metal yangınları

*3. İlk Müdahale*
Yangını fark ettiğinde önce alarmı ver. Küçük yangınlarda uygun tüpü kullanarak müdahale et. Büyük yangınlarda tahliye et ve itfaiyeyi ara.

*4. Yangın Tüpü Kullanımı (PASS)*
P — Pimi çek
A — Aleve doğru nişan al
S — Sıkıştır (kolu bas)
S — Süpür (yan yana hareket et)

*5. Tahliye*
Asansör kullanma, merdiveni kullan. Dumanı önlemek için ağzını kapat.""",
        "sorular": [
            {"soru": "Yangın tüpü kullanımında PASS'ın ilk adımı nedir?", "secenekler": ["Aleve nişan al", "Pimi çek", "Kolu bas", "Süpür"], "dogru": 1},
            {"soru": "Akaryakıt yangını hangi sınıfa girer?", "secenekler": ["A Sınıfı", "B Sınıfı", "C Sınıfı", "D Sınıfı"], "dogru": 1},
            {"soru": "Büyük yangında ilk yapılması gereken nedir?", "secenekler": ["Yangını söndür", "Tahliye et ve itfaiyeyi ara", "Su dök", "Bekle"], "dogru": 1},
            {"soru": "Yangın tahliyesinde ne kullanılmalıdır?", "secenekler": ["Asansör", "Pencere", "Merdiven", "İp"], "dogru": 2},
            {"soru": "Yangın için gereken üç unsur nedir?", "secenekler": ["Su, hava, toprak", "Isı, oksijen, yakıt", "Elektrik, su, gaz", "Kıvılcım, nem, rüzgar"], "dogru": 1}
        ]
    },

    "elektrik_guvenligi": {
        "baslik": "⚡ Elektrik Güvenliği",
        "tur": "İş Güvenliği",
        "sure": "~12 dakika",
        "metin": """📋 *ELEKTRİK GÜVENLİĞİ EĞİTİMİ*

*1. Kilitleme/Etiketleme (LOTO)*
Elektrikli ekipmana bakım yapmadan önce mutlaka enerji kesilmeli, kilit takılmalı ve etiket asılmalıdır. Bu prosedüre LOTO denir.

*2. Yetkisiz Müdahale Yasağı*
Elektrik panolarına ve kablolara yetkisiz müdahale kesinlikle yasaktır. Tüm elektrik işleri yetkili elektrikçi tarafından yapılmalıdır.

*3. Su ve Elektrik*
Islak elle elektrikli ekipmana dokunmayın. Elektrik motorları ve panolarının çevresinde su kullanmayın.

*4. Kablo Güvenliği*
Hasarlı kablo veya fişi kullanmayın, derhal bildirin. Kabloları geçiş yollarına sermeyiniz.

*5. Elektrik Çarpması*
Elektrik çarpması durumunda önce kaynağı kesin. Çarpılan kişiye çıplak elle dokunmayın, yalıtımlı materyal kullanın.""",
        "sorular": [
            {"soru": "LOTO prosedürü ne anlama gelir?", "secenekler": ["Lojistik operasyon", "Kilitleme ve etiketleme", "Elektrik testi", "Bakım onayı"], "dogru": 1},
            {"soru": "Elektrik çarpması durumunda ilk yapılması gereken nedir?", "secenekler": ["Çarpılan kişiyi tut", "Enerji kaynağını kes", "Su dök", "Bekle"], "dogru": 1},
            {"soru": "Hasarlı kablo ile ne yapılmalıdır?", "secenekler": ["Bantla sarılır", "Kullanmaya devam edilir", "Derhal bildirilir", "Kendin tamir et"], "dogru": 2},
            {"soru": "Elektrik panolarına kim müdahale edebilir?", "secenekler": ["Her çalışan", "Sadece yönetici", "Yetkili elektrikçi", "İsteyen herkes"], "dogru": 2},
            {"soru": "Islak elle elektrikli ekipmana ne yapılmalıdır?", "secenekler": ["Dikkatli dokunulabilir", "Eldivenle dokunulabilir", "Kesinlikle dokunulmamalıdır", "Kuru bezle silinir"], "dogru": 2}
        ]
    },

    "acil_durum_tahliye": {
        "baslik": "🚨 Acil Durum ve Tahliye Prosedürleri",
        "tur": "Acil Durum",
        "sure": "~10 dakika",
        "metin": """📋 *ACİL DURUM VE TAHLİYE PROSEDÜRLERİ EĞİTİMİ*

*1. Alarm Sistemleri*
Sürekli alarm: Yangın — derhal tahliye
Aralıklı alarm: Kimyasal sızıntı — rüzgar yönünün tersine kaç
Kısa-uzun alarm: Tatbikat

*2. Tahliye Noktaları*
Her çalışan kendi bölgesinin tahliye çıkışını ve toplanma noktasını bilmelidir. Toplanma noktasında yoklama yapılır.

*3. Yaralı Varsa*
Hareket ettirmeyin. Güvenli bir alandaysanız ilk yardım uygulayın. Derhal 112'yi arayın.

*4. Kimyasal Sızıntı*
Gaz maskesi takın. Rüzgar yönünün tersine kaçın. Kimyasal maddeye temas ettiyseniz 15 dakika bol suyla yıkayın.

*5. Deprem*
Sağlam bir masa altına girin. Sarsıntı geçince tahliye edin. Asansör kullanmayın.""",
        "sorular": [
            {"soru": "Sürekli alarm ne anlama gelir?", "secenekler": ["Tatbikat", "Kimyasal sızıntı", "Yangın — tahliye", "Mesai sonu"], "dogru": 2},
            {"soru": "Kimyasal sızıntıda hangi yöne kaçılır?", "secenekler": ["Rüzgar yönüne", "Rüzgar yönünün tersine", "En yakın çıkışa", "Rastgele"], "dogru": 1},
            {"soru": "Tahliyede yaralı kişiye ne yapılır?", "secenekler": ["Hemen kaldır", "Hareket ettirme, 112'yi ara", "Su ver", "Beklet"], "dogru": 1},
            {"soru": "Kimyasal madde temas ederse ne yapılır?", "secenekler": ["Kurula", "15 dakika bol suyla yıka", "Bant sar", "Bekle"], "dogru": 1},
            {"soru": "Depremde ilk yapılması gereken nedir?", "secenekler": ["Hemen dışarı çık", "Sağlam bir masa altına gir", "Asansörü kullan", "Pencereye koş"], "dogru": 1}
        ]
    },

    "el_alet_guvenligi": {
        "baslik": "🔧 El Aleti ve Ekipman Güvenliği",
        "tur": "İş Güvenliği",
        "sure": "~10 dakika",
        "metin": """📋 *EL ALETİ VE EKİPMAN GÜVENLİĞİ EĞİTİMİ*

*1. Doğru Alet Seçimi*
Her iş için doğru aleti kullanın. Yanlış alet kullanımı hem işi bozar hem yaralanmaya yol açar.

*2. Alet Kontrolü*
Kullanmadan önce aleti kontrol edin. Hasarlı, çatlamış veya gevşek saplı aletler kullanılmaz.

*3. Kesici Aletler*
Kesici aletleri kendinizden uzağa doğru kullanın. Kullanmadığınızda kılıfına takın. Asla çantada açık taşımayın.

*4. Elektrikli Aletler*
Elektrikli aleti çalıştırmadan önce güvenlik muhafazasını kontrol edin. Islak zeminde elektrikli alet kullanmayın.

*5. Depolama*
Aletleri kullandıktan sonra temizleyin ve yerine kaldırın. Yüksek yerlerde açık bırakmayın, düşme riski oluşturur.""",
        "sorular": [
            {"soru": "Hasarlı el aleti ile ne yapılmalıdır?", "secenekler": ["Dikkatlice kullanılır", "Bantla tamir edilir", "Kullanılmaz, bildirilir", "Fark etmez"], "dogru": 2},
            {"soru": "Kesici aletler hangi yönde kullanılır?", "secenekler": ["Kendinize doğru", "Kendinizden uzağa doğru", "Yere doğru", "Fark etmez"], "dogru": 1},
            {"soru": "Elektrikli alet ne zaman kullanılamaz?", "secenekler": ["Gece", "Islak zeminde", "Kapalı alanda", "Soğuk havada"], "dogru": 1},
            {"soru": "Kullanılmayan kesici alet nerede bulunmalıdır?", "secenekler": ["Cepte açık", "Çantada açık", "Kılıfında", "Tezgahta"], "dogru": 2},
            {"soru": "Alet kullanımından önce ne yapılmalıdır?", "secenekler": ["Direk kullanılır", "Kontrol edilir", "Yağlanır", "Amire gösterilir"], "dogru": 1}
        ]
    },

    "ergonomi_manuel_tasima": {
        "baslik": "💪 Ergonomi ve Manuel Taşıma",
        "tur": "İş Sağlığı",
        "sure": "~10 dakika",
        "metin": """📋 *ERGONOMİ VE MANUEL TAŞIMA EĞİTİMİ*

*1. Doğru Kaldırma Tekniği*
Yükü kaldırmadan önce yakına çekin. Dizlerinizi bükerek çömelin, sırtınızı dik tutun. Yükü bacak kaslarınızla kaldırın, bel kaslarınızla değil.

*2. Taşıma Limitleri*
Bir kişi için maksimum taşıma ağırlığı 25 kg'dır. Bu ağırlığın üzerindeki yükler için mekanik yardım veya ikinci kişi kullanılmalıdır.

*3. Çimento Torbası Taşıma*
50 kg'lık çimento torbası tek başına taşınamaz. Mutlaka iki kişi veya mekanik araç kullanılmalıdır.

*4. Tekrarlayan Hareketler*
Sürekli aynı hareketi yapmak kas-iskelet hastalıklarına yol açar. Belirli aralıklarla mola verin ve esneme egzersizleri yapın.

*5. Çalışma Pozisyonu*
Uzun süre eğilmek veya bükümlü çalışmaktan kaçının. Mümkünse çalışma yüzeyinin yüksekliğini ayarlayın.""",
        "sorular": [
            {"soru": "Bir kişi için maksimum taşıma ağırlığı kaçtır?", "secenekler": ["10 kg", "15 kg", "25 kg", "50 kg"], "dogru": 2},
            {"soru": "Yük kaldırırken hangi kaslar kullanılmalıdır?", "secenekler": ["Bel kasları", "Bacak kasları", "Kol kasları", "Karın kasları"], "dogru": 1},
            {"soru": "50 kg çimento torbası nasıl taşınır?", "secenekler": ["Tek kişi taşır", "İki kişi veya mekanik araçla", "Omuzda taşınır", "Sürüklenerek"], "dogru": 1},
            {"soru": "Doğru kaldırma tekniğinde sırt nasıl olmalıdır?", "secenekler": ["Öne eğik", "Dik", "Yana eğik", "Fark etmez"], "dogru": 1},
            {"soru": "Tekrarlayan hareketler ne gibi sorunlara yol açar?", "secenekler": ["Göz hastalığı", "Kas-iskelet hastalıkları", "İşitme kaybı", "Cilt hastalığı"], "dogru": 1}
        ]
    },

    "kaza_bildirim": {
        "baslik": "📝 Kaza ve Ramak Kala Bildirimi",
        "tur": "İş Güvenliği",
        "sure": "~10 dakika",
        "metin": """📋 *KAZA VE RAMAK KALA BİLDİRİMİ EĞİTİMİ*

*1. İş Kazası Nedir?*
İşyerinde veya işin yürütümü sırasında meydana gelen, çalışanı hemen veya sonradan bedenen ya da ruhen zarara uğratan olaylardır.

*2. Ramak Kala Nedir?*
Yaralanma veya maddi hasara yol açmayan ancak açabilecek potansiyeldeki olaylardır. Ramak kala bildirimi kaza önlemede en önemli araçtır.

*3. Bildirim Zorunluluğu*
Tüm kazalar ve ramak kala olayları bildirilmek zorundadır. Bildirmeyen çalışan iş güvenliği kurallarını ihlal etmiş sayılır.

*4. Nasıl Bildirilir?*
Önce güvenli ortam sağla. Yaralıya ilk yardım yap. Amirini ve güvenlik birimine bildir. Kaza tutanağını imzala.

*5. Neden Bildirmeliyiz?*
Kazaları bildirmek, aynı kazanın tekrar yaşanmasını önler. Bildirim ceza almak değil, güvenliği artırmaktır.""",
        "sorular": [
            {"soru": "Ramak kala olayı ne demektir?", "secenekler": ["Ölümlü kaza", "Yaralanma olmayan ama olabilecek olay", "İş durması", "Ekipman arızası"], "dogru": 1},
            {"soru": "Kaza sonrası ilk yapılması gereken nedir?", "secenekler": ["Tutanak yaz", "Güvenli ortam sağla ve ilk yardım yap", "Amiri ara", "Devam et"], "dogru": 1},
            {"soru": "Ramak kala bildirimi neden önemlidir?", "secenekler": ["Ceza almak için", "Aynı kazanın tekrarını önlemek için", "Zorunlu olduğu için", "Sigorta için"], "dogru": 1},
            {"soru": "Kazayı bildirmemek ne anlama gelir?", "secenekler": ["Normal karşılanır", "İş güvenliği kurallarını ihlal", "Terfi nedeni", "Ödüllendirilir"], "dogru": 1},
            {"soru": "Kaza bildirimi kime yapılır?", "secenekler": ["Sadece doktora", "Amir ve güvenlik birimine", "Sadece amire", "Hiç kimseye"], "dogru": 1}
        ]
    },
}
