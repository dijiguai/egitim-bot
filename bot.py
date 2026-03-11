"""
İş Başı Eğitim Botu — Ana Dosya
"""

import logging
import os
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from handlers import egitim_handler, admin_handler, kayit_handler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


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

    # Buton tıklamaları
    app.add_handler(CallbackQueryHandler(egitim_handler.buton_handler))

    # Metin mesajları — kimlik doğrulama
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, kayit_handler.metin_handler))

    logger.info("Bot başlatılıyor...")
    app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
