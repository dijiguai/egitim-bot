"""
Gruba yeni uye katilinca otomatik bildirim
Grupta mesaj yazanlari takip ederek kayitsiz uyeleri tespit eder
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import ADMIN_IDS

logger = logging.getLogger(__name__)

# Kayitsiz uyeler: { user_id: {ad, username} }
yeni_uyeler = {}


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

        yeni_uyeler[user_id] = {"ad": ad, "username": username}

        keyboard = [[
            InlineKeyboardButton("Sisteme Ekle", callback_data=f"yeni_uye_ekle:{user_id}"),
            InlineKeyboardButton("Yoksay", callback_data=f"yeni_uye_yoksay:{user_id}")
        ]]

        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=(
                        "Gruba yeni uye katildi!\n\n"
                        f"Ad: {ad}\n"
                        f"Kullanici adi: {username}\n"
                        f"ID: {user_id}\n\n"
                        "Sisteme eklemek ister misiniz?"
                    ),
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            except Exception as e:
                logger.warning(f"Admin bildirimi gonderilemedi: {e}")


async def grup_mesaj_dinle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Grupta mesaj yazanlari takip eder, kayitsiz uyeleri tespit eder."""
    from config import GRUP_ID

    if not update.message:
        return
    chat = update.effective_chat
    if not chat or str(chat.id) != str(GRUP_ID):
        return

    user = update.effective_user
    if not user or user.is_bot or user.id in ADMIN_IDS:
        return

    uid = user.id

    try:
        from calisanlar import tum_calisanlar
        if uid in tum_calisanlar():
            return
    except:
        return

    if uid in yeni_uyeler:
        return

    ad = f"{user.first_name or ''} {user.last_name or ''}".strip()
    username = f"@{user.username}" if user.username else ""
    yeni_uyeler[uid] = {"ad": ad, "username": username}
    logger.info(f"Aktif uye tespit edildi: {ad} ({uid})")

    keyboard = [[
        InlineKeyboardButton("Sisteme Ekle", callback_data=f"yeni_uye_ekle:{uid}"),
        InlineKeyboardButton("Yoksay", callback_data=f"yeni_uye_yoksay:{uid}")
    ]]

    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=(
                    "Grupta kayitsiz aktif uye tespit edildi!\n\n"
                    f"Ad: {ad}\n"
                    f"Kullanici adi: {username}\n"
                    f"ID: {uid}\n\n"
                    "Sisteme eklemek ister misiniz?"
                ),
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            logger.warning(f"Bildirim gonderilemedi: {e}")


async def yeni_uye_ekle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = int(query.data.split(":")[1])
    bilgi = yeni_uyeler.get(user_id, {})
    ad = bilgi.get("ad", f"Kullanici {user_id}")

    await query.edit_message_text(
        f"{ad} sisteme eklemek icin:\n\n"
        f"/hizli_ekle {user_id} [Gorev] [GG.AA.YYYY]\n\n"
        f"Ornek:\n"
        f"/hizli_ekle {user_id} Operator 15.06.1990"
    )


async def yeni_uye_yoksay_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = int(query.data.split(":")[1])
    bilgi = yeni_uyeler.pop(user_id, {})
    await query.edit_message_text(f"{bilgi.get('ad','?')} yoksayildi.")


async def grup_uyelerini_tara(app):
    """Bot baslarken grup adminlerini tarar."""
    from config import GRUP_ID
    from calisanlar import tum_calisanlar

    if not GRUP_ID or GRUP_ID == 0:
        return

    try:
        kayitlilar = tum_calisanlar()
        kayitli_idler = {k for k in kayitlilar.keys() if k > 0}

        uyeler = await app.bot.get_chat_administrators(GRUP_ID)
        for uye in uyeler:
            u = uye.user
            if u.is_bot or u.id in kayitli_idler or u.id in yeni_uyeler:
                continue
            ad = f"{u.first_name or ''} {u.last_name or ''}".strip()
            username = f"@{u.username}" if u.username else ""
            yeni_uyeler[u.id] = {"ad": ad, "username": username}
            logger.info(f"Admin tespit edildi: {ad} ({u.id})")

        logger.info(f"Tarama tamamlandi: {len(yeni_uyeler)} bekleyen")
    except Exception as e:
        logger.warning(f"Grup tarama hatasi: {e}")
