"""
Grup mesaj dinleme ve uye tespiti
"""

import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import ADMIN_IDS, GRUP_ID

logger = logging.getLogger(__name__)

# Kayitsiz uyeler: { user_id: {ad, username, ilk_gorulme, son_mesaj, mesajlar} }
yeni_uyeler = {}

# Mesaj loglari: [ {user_id, ad, username, mesaj, zaman} ]
mesaj_loglari = []
MAX_LOG = 500  # En fazla 500 mesaj tut


def _simdi():
    try:
        import pytz
        tz = pytz.timezone("Europe/Istanbul")
        return datetime.now(tz).strftime("%d.%m.%Y %H:%M")
    except:
        return datetime.utcnow().strftime("%d.%m.%Y %H:%M")


async def yeni_uye_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gruba yeni uye katilinca tetiklenir."""
    if not update.message or not update.message.new_chat_members:
        return

    for user in update.message.new_chat_members:
        if user.is_bot:
            continue

        user_id = user.id
        ad = f"{user.first_name or ''} {user.last_name or ''}".strip()
        username = f"@{user.username}" if user.username else ""

        try:
            from calisanlar import calisan_bul
            if calisan_bul(user_id):
                continue
        except:
            pass

        simdi = _simdi()
        yeni_uyeler[user_id] = {
            "ad": ad, "username": username,
            "ilk_gorulme": simdi, "son_mesaj": simdi, "mesaj_sayisi": 0
        }

        # Davet listesinde bu kullanici var mi? (token olmadan gruba katilmis olabilir)
        davet_bulundu = False
        try:
            from davetler import tum_davetler, davet_katildi_isaretle
            from calisanlar import calisan_ekle
            firma_id_lokal = firma_id or "varsayilan"
            davetler = tum_davetler(firma_id_lokal)
            # Ad benzerligine gore esle
            ad_lower = ad.lower().replace("i", "i").replace("İ", "i")
            for d in davetler:
                if d.get("durum") == "katildi":
                    continue
                d_ad = d.get("ad_soyad","").lower()
                if ad_lower and (ad_lower in d_ad or d_ad in ad_lower or
                    ad.split()[0].lower() in d_ad):
                    # Eslesme bulundu - kayit tamamla
                    token = d.get("token","")
                    if token:
                        calisan_ekle(user_id, d["ad_soyad"], "00.00.0000", "Belirsiz", firma_id_lokal)
                        davet_katildi_isaretle(token, user_id, firma_id_lokal)
                        davet_bulundu = True
                        try:
                            await context.bot.send_message(
                                chat_id=user_id,
                                text=(
                                    f"Hosgeldiniz *{d['ad_soyad'].split()[0]}*!\n\n"
                                    f"Sisteme basariyla kayit oldunuz.\n"
                                    f"Her sabah 08:00'de gunluk egitim bildiriminiz gelecek."
                                ),
                                parse_mode="Markdown"
                            )
                        except:
                            pass
                        break
        except Exception as e:
            logger.warning(f"Davet eslestirme hatasi: {e}")

        # Davet bulunamadiysa grup icinde kayit butonu goster
        # (ozel mesaj gonderilemez - kisi bota hic yazmamis olabilir)
        if not davet_bulundu:
            try:
                from config import BOT_USERNAME
                bot_link = f"https://t.me/{BOT_USERNAME}?start=kayit"
                mention = f"@{username.lstrip('@')}" if username else ad
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=(
                        f"Hosgeldin {mention}! 👋\n\n"
                        f"Egitim sistemine kayit olmak icin asagidaki butona bas."
                    ),
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("Sisteme Kayit Ol", url=bot_link)
                    ]])
                )
            except Exception as e:
                logger.warning(f"Grup kayit mesaji gonderilemedi: {e}")

        keyboard = [[
            InlineKeyboardButton("Sisteme Ekle", callback_data=f"yeni_uye_ekle:{user_id}"),
            InlineKeyboardButton("Yoksay", callback_data=f"yeni_uye_yoksay:{user_id}")
        ]]
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=(
                        f"Gruba yeni uye katildi!\n\n"
                        f"Ad: {ad}\n"
                        f"Kullanici adi: {username}\n"
                        f"ID: {user_id}\n"
                        f"Davet eslesti: {'Evet' if davet_bulundu else 'Hayir'}\n"
                        f"Saat: {simdi}"
                    ),
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            except Exception as e:
                logger.warning(f"Admin bildirimi: {e}")


async def grup_mesaj_dinle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Grupta yazilan tum mesajlari dinler.
    - Kayitsiz uyeleri tespit eder
    - Mesaj loglarini tutar
    """
    if not update.message:
        return

    chat = update.effective_chat
    if not chat or chat.type not in ("group", "supergroup"):
        return

    logger.info(f"Grup mesaji alindi: chat_id={chat.id}, GRUP_ID={GRUP_ID}")

    # Hangi firmaya ait oldugunu bul
    firma_id = None
    try:
        from firma_manager import grup_id_den_firma
        firma_id, _ = grup_id_den_firma(chat.id)
    except:
        pass

    # Bilinen bir firma grubu mu?
    if not firma_id:
        # Eski sistem ile kontrol
        if str(chat.id) != str(GRUP_ID):
            logger.info(f"Bilinmeyen grup, atlandi: {chat.id}")
            return
        firma_id = "varsayilan"

    logger.info(f"Grup mesaji: firma={firma_id}, chat={chat.id}")

    user = update.effective_user
    if not user or user.is_bot:
        return

    uid = user.id
    ad = f"{user.first_name or ''} {user.last_name or ''}".strip()
    username = f"@{user.username}" if user.username else ""
    msg = update.message
    if msg.text:
        mesaj_metni = msg.text
    elif msg.sticker:
        mesaj_metni = f"[Sticker: {msg.sticker.emoji or ''}]"
    elif msg.photo:
        mesaj_metni = "[Fotoğraf]"
    elif msg.video:
        mesaj_metni = "[Video]"
    elif msg.voice:
        mesaj_metni = "[Sesli mesaj]"
    elif msg.document:
        mesaj_metni = "[Dosya]"
    else:
        mesaj_metni = "[Medya]"
    simdi = _simdi()

    # Mesaj loguna ekle
    global mesaj_loglari
    mesaj_loglari.append({
        "user_id": uid,
        "ad": ad,
        "username": username,
        "mesaj": mesaj_metni[:200],  # max 200 karakter
        "zaman": simdi,
        "kayitli": False  # asagida guncellenir
    })
    if len(mesaj_loglari) > MAX_LOG:
        mesaj_loglari = mesaj_loglari[-MAX_LOG:]

    # Admin ise sadece logla, ekleme yapma
    if uid in ADMIN_IDS:
        mesaj_loglari[-1]["kayitli"] = True
        return

    # Kayitli mi?
    try:
        from calisanlar import tum_calisanlar
        kayitlilar = tum_calisanlar()
        if uid in kayitlilar:
            mesaj_loglari[-1]["kayitli"] = True
            return
    except:
        pass

    # Bekleyenlere ekle / guncelle
    if uid not in yeni_uyeler:
        yeni_uyeler[uid] = {
            "ad": ad, "username": username,
            "ilk_gorulme": simdi, "son_mesaj": simdi, "mesaj_sayisi": 1
        }
        logger.info(f"Yeni kayitsiz uye tespit edildi: {ad} ({uid})")

        # Admin'e bildirim
        keyboard = [[
            InlineKeyboardButton("Sisteme Ekle", callback_data=f"yeni_uye_ekle:{uid}"),
            InlineKeyboardButton("Yoksay", callback_data=f"yeni_uye_yoksay:{uid}")
        ]]
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=(
                        f"Grupta kayitsiz aktif uye!\n\n"
                        f"Ad: {ad}\n"
                        f"Kullanici adi: {username}\n"
                        f"ID: {uid}\n"
                        f"Saat: {simdi}\n\n"
                        f"Mesaj: {mesaj_metni[:100]}"
                    ),
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            except Exception as e:
                logger.warning(f"Bildirim: {e}")
    else:
        yeni_uyeler[uid]["son_mesaj"] = simdi
        yeni_uyeler[uid]["mesaj_sayisi"] = yeni_uyeler[uid].get("mesaj_sayisi", 0) + 1


async def yeni_uye_ekle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = int(query.data.split(":")[1])
    bilgi = yeni_uyeler.get(user_id, {})
    ad = bilgi.get("ad", f"Kullanici {user_id}")
    username = bilgi.get("username", "")

    # Panel URL'ini env'den al, yoksa Railway default
    import os, urllib.parse
    panel_base = os.environ.get("PANEL_URL", "https://egitim-bot-production.up.railway.app")
    ad_encoded = urllib.parse.quote(ad)
    panel_link = f"{panel_base}/panel/ekle-calisan?tid={user_id}&ad={ad_encoded}"

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = [[InlineKeyboardButton("Panelde Ekle", url=panel_link)]]

    metin = (
        f"*{ad}* ({username}) sisteme eklemek icin paneli acin:\n\n"
        f"ID: `{user_id}`\n\n"
        f"Asagidaki butona basin, form otomatik dolacak."
    )
    await query.edit_message_text(
        metin,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def yeni_uye_yoksay_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = int(query.data.split(":")[1])
    bilgi = yeni_uyeler.pop(user_id, {})
    await query.edit_message_text(f"{bilgi.get('ad','?')} yoksayildi.")


async def grup_uyelerini_tara(app):
    """Bot baslarken grup adminlerini tarar."""
    if not GRUP_ID or GRUP_ID == 0:
        return
    try:
        from calisanlar import tum_calisanlar
        kayitlilar = tum_calisanlar()
        kayitli_idler = {k for k in kayitlilar.keys() if k > 0}
        uyeler = await app.bot.get_chat_administrators(GRUP_ID)
        simdi = _simdi()
        for uye in uyeler:
            u = uye.user
            if u.is_bot or u.id in kayitli_idler or u.id in yeni_uyeler:
                continue
            ad = f"{u.first_name or ''} {u.last_name or ''}".strip()
            username = f"@{u.username}" if u.username else ""
            yeni_uyeler[u.id] = {
                "ad": ad, "username": username,
                "ilk_gorulme": simdi, "son_mesaj": "-", "mesaj_sayisi": 0
            }
        logger.info(f"Tarama: {len(yeni_uyeler)} bekleyen")
    except Exception as e:
        logger.warning(f"Tarama hatasi: {e}")
