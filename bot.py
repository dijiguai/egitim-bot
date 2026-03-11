"""
İş Başı Eğitim Botu — Ana Dosya
Telegram Bot + Google Sheets entegrasyonu
"""

import logging
import os
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from handlers import egitim_handler, admin_handler, kayit_handler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Konuşma adımları
KIMLIK_DOGRULAMA = 1

def main():
    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN ortam değişkeni ayarlanmamış!")

    app = Application.builder().token(TOKEN).build()

    # Admin komutları
    app.add_handler(CommandHandler("start", admin_handler.start))
    app.add_handler(CommandHandler("egitim_gonder", admin_handler.egitim_gonder))
    app.add_handler(CommandHandler("rapor", admin_handler.rapor))
    app.add_handler(CommandHandler("kalanlar", admin_handler.kalanlar))
    app.add_handler(CommandHandler("yardim", admin_handler.yardim))

    # Eğitim akışı (buton tıklamaları)
    app.add_handler(CallbackQueryHandler(egitim_handler.buton_handler))

    # Kimlik doğrulama (metin mesajı — doğum tarihi)
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(egitim_handler.sinav_bitti, pattern="^sinav_bitti$")],
        states={
            KIMLIK_DOGRULAMA: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, kayit_handler.kimlik_dogrula)
            ]
        },
        fallbacks=[CommandHandler("iptal", kayit_handler.iptal)],
        per_user=True,
        per_chat=False,
    )
    app.add_handler(conv_handler)

    logger.info("Bot başlatılıyor...")
    app.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    main()
