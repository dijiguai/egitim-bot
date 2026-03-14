"""
Gruba yeni uye katilinca otomatik bildirim
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import ADMIN_IDS

logger = logging.getLogger(__name__)

# Onay bekleyenler: { user_id: {ad, username} }
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
        username = f"@{user.username}" if user.username else "kullanici_adi_yok"

        # Zaten kayitli mi?
        try:
            from calisanlar import calisan_bul
            if calisan_bul(user_id):
                logger.info(f"Zaten kayitli: {ad}")
                continue
        except:
            pass

        yeni_uyeler[user_id] = {"ad": ad, "username": username}

        keyboard = [[
            InlineKeyboardButton("✅ Sisteme Ekle", callback_data=f"yeni_uye_ekle:{user_id}"),
            InlineKeyboardButton("❌ Yoksay", callback_data=f"yeni_uye_yoksay:{user_id}")
        ]]

        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=(
                        f"👤 Gruba yeni uye katildi!\n\n"
                        f"Ad: {ad}\n"
                        f"Kullanici adi: {username}\n"
                        f"Telegram ID: {user_id}\n\n"
                        f"Panelden eklemek icin asagidaki butona basin:"
                    ),
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            except Exception as e:
                logger.warning(f"Admin bildirimi gonderilemedi: {e}")


async def yeni_uye_ekle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Onayla butonuna basilinca gorev ve dogum tarihi sor."""
    query = update.callback_query
    await query.answer()
    user_id = int(query.data.split(":")[1])
    bilgi = yeni_uyeler.get(user_id, {})
    ad = bilgi.get("ad", f"Kullanici {user_id}")

    # Admin'den bilgi bekle
    context.user_data["bekleyen_uye"] = {"user_id": user_id, "ad": ad}

    await query.edit_message_text(
        f"*{ad}* sisteme eklemek icin:\n\n"
        f"Su formati kullanarak yayin:\n"
        f"`/hizli_ekle {user_id} [Gorev] [GG.AA.YYYY]`\n\n"
        f"Ornek:\n"
        f"`/hizli_ekle {user_id} Operatör 15.06.1990`\n\n"
        f"Ekledikten sonra panelden 'Egitim Gonder' butonu ile egitime yonlendirebilirsiniz.",
        parse_mode="Markdown"
    )


async def yeni_uye_yoksay_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = int(query.data.split(":")[1])
    bilgi = yeni_uyeler.pop(user_id, {})
    await query.edit_message_text(f"❌ {bilgi.get('ad','?')} yoksayildi.")
