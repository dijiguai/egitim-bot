"""
Is Basi Egitim Botu - Ana Dosya
"""

import logging, os, threading
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from handlers import egitim_handler, admin_handler, kayit_handler, izin_handler
from handlers.grup_handler import yeni_uye_handler, yeni_uye_ekle_callback, yeni_uye_yoksay_callback
from panel import app as flask_app
from scheduler import zamanlayici_baslat

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def egitimler_yukle():
    """Config'deki egitimler Sheets'te yoksa yukle, sonra EGITIMLER'i guncelle."""
    try:
        from config import EGITIMLER
        from egitimler_sheets import config_egitimlerini_sheets_e_yukle, tum_egitimler
        config_egitimlerini_sheets_e_yukle(EGITIMLER)
        # EGITIMLER dict'ini Sheets'ten gelen veriyle guncelle
        sheets_egitimler = tum_egitimler()
        EGITIMLER.clear()
        EGITIMLER.update(sheets_egitimler)
        logger.info(f"Egitimler Sheets'ten yuklendi: {len(EGITIMLER)} adet")
    except Exception as e:
        logger.error(f"Egitim yukleme hatasi: {e}")


def flask_baslat():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host="0.0.0.0", port=port, use_reloader=False)


def main():
    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN ayarlanmamis!")

    # Egitimler Sheets'e yukle
    egitimler_yukle()

    threading.Thread(target=flask_baslat, daemon=True).start()

    app = Application.builder().token(TOKEN).build()
    zamanlayici_baslat(app)

    app.add_handler(CommandHandler("start", kayit_handler.start_handler))
    app.add_handler(CommandHandler("egitim_gonder", admin_handler.egitim_gonder))
    app.add_handler(CommandHandler("egitim_tekrar", admin_handler.egitim_tekrar))
    app.add_handler(CommandHandler("rapor", admin_handler.rapor))
    app.add_handler(CommandHandler("kalanlar", admin_handler.kalanlar))
    app.add_handler(CommandHandler("yardim", admin_handler.yardim))
    app.add_handler(CommandHandler("hizli_ekle", admin_handler.hizli_ekle))
    app.add_handler(CommandHandler("bekleyenler", admin_handler.bekleyenler))
    app.add_handler(CommandHandler("izin_ekle", izin_handler.izin_ekle_cmd))
    app.add_handler(CommandHandler("izin_kaldir", izin_handler.izin_kaldir_cmd))
    app.add_handler(CommandHandler("izinliler", izin_handler.izinliler_cmd))
    app.add_handler(CommandHandler("eksik", izin_handler.eksik_cmd))
    # Gruba yeni uye katilimi
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, yeni_uye_handler))

    # Callback handler — oncelik sirasi onemli
    app.add_handler(CallbackQueryHandler(yeni_uye_ekle_callback, pattern="^yeni_uye_ekle:"))
    app.add_handler(CallbackQueryHandler(yeni_uye_yoksay_callback, pattern="^yeni_uye_yoksay:"))
    app.add_handler(CallbackQueryHandler(egitim_handler.buton_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, kayit_handler.metin_handler))

    logger.info("Bot baslatiliyor...")
    app.run_polling(allowed_updates=["message", "callback_query", "chat_member"])


if __name__ == "__main__":
    main()
