"""
İş Başı Eğitim Botu — Ana Dosya
Bot + Yönetici Paneli birlikte çalışır
"""

import logging
import os
import threading
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from handlers import egitim_handler, admin_handler, kayit_handler
from panel import app as flask_app

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


def flask_baslat():
    """Paneli ayrı thread'de çalıştır."""
    port = int(os.environ.get("PORT", 5000))
    flask_app.run(host="0.0.0.0", port=port, use_reloader=False)


def main():
    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN ortam değişkeni ayarlanmamış!")

    # Flask panelini arka planda başlat
    t = threading.Thread(target=flask_baslat, daemon=True)
    t.start()
    logger.info("Yönetici paneli başlatıldı.")

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
