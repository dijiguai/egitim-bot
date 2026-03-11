"""
İş Başı Eğitim Botu — Ana Dosya
Bot + Yönetici Paneli + Otomatik Zamanlayıcı
"""

import logging
import os
import threading
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from handlers import egitim_handler, admin_handler, kayit_handler, izin_handler
from panel import app as flask_app
from scheduler import zamanlayici_baslat

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


def flask_baslat():
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Panel port {port} üzerinde başlatılıyor...")
    flask_app.run(host="0.0.0.0", port=port, use_reloader=False)


def main():
    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN ortam değişkeni ayarlanmamış!")

    # Flask panelini başlat
    t = threading.Thread(target=flask_baslat, daemon=True)
    t.start()

    app = Application.builder().token(TOKEN).build()

    # Zamanlayıcıyı başlat (08:00 otomatik eğitim)
    zamanlayici_baslat(app)

    # Admin komutları
    app.add_handler(CommandHandler("start", admin_handler.start))
    app.add_handler(CommandHandler("egitim_gonder", admin_handler.egitim_gonder))
    app.add_handler(CommandHandler("rapor", admin_handler.rapor))
    app.add_handler(CommandHandler("kalanlar", admin_handler.kalanlar))
    app.add_handler(CommandHandler("yardim", admin_handler.yardim))
    app.add_handler(CommandHandler("grup_id", admin_handler.grup_id))

    # İzin yönetimi (admin)
    app.add_handler(CommandHandler("izin_ekle", izin_handler.izin_ekle_cmd))
    app.add_handler(CommandHandler("izin_kaldir", izin_handler.izin_kaldir_cmd))
    app.add_handler(CommandHandler("izinliler", izin_handler.izinliler_cmd))
    app.add_handler(CommandHandler("eksik", izin_handler.eksik_cmd))

    # Buton tıklamaları
    app.add_handler(CallbackQueryHandler(egitim_handler.buton_handler))

    # Metin mesajları — kimlik doğrulama
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, kayit_handler.metin_handler))

    logger.info("Bot başlatılıyor...")
    app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
