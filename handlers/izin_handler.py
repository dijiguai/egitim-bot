"""
İzin yönetimi komutları
"""

import logging
from datetime import date, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_IDS, CALISANLAR
from durum import izin_ekle, izin_kaldir, izinli_mi, eksik_egitimler

logger = logging.getLogger(__name__)

def admin_mi(user_id): return user_id in ADMIN_IDS

def bugunun_tarihi(): return date.today().strftime("%d.%m.%Y")


async def izin_ekle_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /izin_ekle [telegram_id] [tarih(ler)]
    Örnek: /izin_ekle 123456789 12.03.2026
    Örnek: /izin_ekle 123456789 12.03.2026 13.03.2026
    Tarih girilmezse bugün için izin eklenir.
    """
    if not admin_mi(update.effective_user.id):
        await update.message.reply_text("⛔ Bu komutu kullanma yetkiniz yok.")
        return

    args = context.args
    if not args:
        await update.message.reply_text(
            "Kullanım: `/izin_ekle [telegram_id] [tarih]`\n"
            "Örnek: `/izin_ekle 123456789 12.03.2026`\n"
            "Tarih girilmezse bugün için izin eklenir.",
            parse_mode="Markdown"
        )
        return

    try:
        user_id = int(args[0])
    except ValueError:
        await update.message.reply_text("❌ Geçersiz Telegram ID.")
        return

    tarihler = args[1:] if len(args) > 1 else [bugunun_tarihi()]
    calisan = CALISANLAR.get(user_id)
    ad = calisan["ad_soyad"] if calisan else f"ID:{user_id}"

    for tarih in tarihler:
        izin_ekle(user_id, tarih)

    tarih_str = ", ".join(tarihler)
    await update.message.reply_text(
        f"✅ *{ad}* için izin eklendi.\n📅 Tarih(ler): {tarih_str}\n\n"
        f"Bu çalışan belirtilen günlerde eğitim bildirimi almayacak.",
        parse_mode="Markdown"
    )


async def izin_kaldir_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /izin_kaldir [telegram_id] [tarih]
    """
    if not admin_mi(update.effective_user.id):
        await update.message.reply_text("⛔ Bu komutu kullanma yetkiniz yok.")
        return

    args = context.args
    if len(args) < 1:
        await update.message.reply_text("Kullanım: `/izin_kaldir [telegram_id] [tarih]`", parse_mode="Markdown")
        return

    try:
        user_id = int(args[0])
    except ValueError:
        await update.message.reply_text("❌ Geçersiz Telegram ID.")
        return

    tarih = args[1] if len(args) > 1 else bugunun_tarihi()
    calisan = CALISANLAR.get(user_id)
    ad = calisan["ad_soyad"] if calisan else f"ID:{user_id}"

    izin_kaldir(user_id, tarih)
    await update.message.reply_text(
        f"✅ *{ad}* için {tarih} tarihli izin kaldırıldı.",
        parse_mode="Markdown"
    )


async def izinliler_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /izinliler — bugün izinli çalışanlar
    """
    if not admin_mi(update.effective_user.id):
        await update.message.reply_text("⛔ Bu komutu kullanma yetkiniz yok.")
        return

    bugun = bugunun_tarihi()
    izinli_liste = []

    for user_id, calisan in CALISANLAR.items():
        if izinli_mi(user_id, bugun):
            izinli_liste.append(f"🏖 {calisan['ad_soyad']} ({calisan['gorev']})")

    if not izinli_liste:
        await update.message.reply_text(f"✅ Bugün ({bugun}) izinli çalışan yok.")
        return

    metin = f"🏖 *Bugün İzinli Çalışanlar ({bugun}):*\n\n" + "\n".join(izinli_liste)
    await update.message.reply_text(metin, parse_mode="Markdown")


async def eksik_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /eksik [telegram_id] — çalışanın eksik eğitimleri
    /eksik — tüm çalışanların eksik özeti
    """
    if not admin_mi(update.effective_user.id):
        await update.message.reply_text("⛔ Bu komutu kullanma yetkiniz yok.")
        return

    from config import EGITIMLER
    args = context.args

    if args:
        try:
            user_id = int(args[0])
            calisan = CALISANLAR.get(user_id)
            ad = calisan["ad_soyad"] if calisan else f"ID:{user_id}"
            eksikler = eksik_egitimler(user_id)
            if not eksikler:
                await update.message.reply_text(f"✅ *{ad}* tüm eğitimleri tamamlamış!", parse_mode="Markdown")
                return
            liste = "\n".join([f"• {EGITIMLER[e]['baslik']}" for e in eksikler if e in EGITIMLER])
            await update.message.reply_text(
                f"📋 *{ad}* — Eksik Eğitimler ({len(eksikler)}/{len(EGITIMLER)}):\n\n{liste}",
                parse_mode="Markdown"
            )
        except ValueError:
            await update.message.reply_text("❌ Geçersiz ID.")
    else:
        # Tüm çalışanlar özeti
        satirlar = []
        for user_id, calisan in CALISANLAR.items():
            eksikler = eksik_egitimler(user_id)
            tamamlanan = len(EGITIMLER) - len(eksikler)
            bar = "█" * tamamlanan + "░" * len(eksikler)
            satirlar.append(f"{calisan['ad_soyad']}: {bar} {tamamlanan}/{len(EGITIMLER)}")

        metin = "📊 *Eğitim Tamamlama Durumu:*\n\n" + "\n".join(satirlar) if satirlar else "Henüz çalışan eklenmemiş."
        await update.message.reply_text(metin, parse_mode="Markdown")
