"""
İzin yönetimi komutları
"""

import logging
from datetime import date
from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_IDS
from calisanlar import tum_calisanlar
from durum import izin_ekle, izin_kaldir, izinli_mi, eksik_egitimler

logger = logging.getLogger(__name__)

def admin_mi(uid): return uid in ADMIN_IDS
def bugun(): return date.today().strftime("%d.%m.%Y")


async def izin_ekle_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_mi(update.effective_user.id):
        await update.message.reply_text("⛔ Yetkiniz yok.")
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
        uid = int(args[0])
    except ValueError:
        await update.message.reply_text("❌ Geçersiz Telegram ID.")
        return

    tarihler = args[1:] if len(args) > 1 else [bugun()]
    calisanlar = tum_calisanlar()
    ad = calisanlar.get(uid, {}).get("ad_soyad", f"ID:{uid}")

    for t in tarihler:
        izin_ekle(uid, t)

    await update.message.reply_text(
        f"✅ *{ad}* için izin eklendi.\n📅 {', '.join(tarihler)}",
        parse_mode="Markdown"
    )


async def izin_kaldir_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_mi(update.effective_user.id):
        await update.message.reply_text("⛔ Yetkiniz yok.")
        return
    args = context.args
    if not args:
        await update.message.reply_text("Kullanım: `/izin_kaldir [telegram_id] [tarih]`", parse_mode="Markdown")
        return
    try:
        uid = int(args[0])
    except ValueError:
        await update.message.reply_text("❌ Geçersiz ID.")
        return

    tarih = args[1] if len(args) > 1 else bugun()
    calisanlar = tum_calisanlar()
    ad = calisanlar.get(uid, {}).get("ad_soyad", f"ID:{uid}")
    izin_kaldir(uid, tarih)
    await update.message.reply_text(f"✅ *{ad}* için {tarih} izni kaldırıldı.", parse_mode="Markdown")


async def izinliler_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_mi(update.effective_user.id):
        await update.message.reply_text("⛔ Yetkiniz yok.")
        return
    b = bugun()
    calisanlar = tum_calisanlar()
    liste = [
        f"🏖 {c['ad_soyad']} ({c['gorev']})"
        for uid, c in calisanlar.items()
        if izinli_mi(uid, b)
    ]
    if liste:
        await update.message.reply_text(f"🏖 *Bugün İzinliler ({b}):*\n\n" + "\n".join(liste), parse_mode="Markdown")
    else:
        await update.message.reply_text(f"✅ Bugün ({b}) izinli çalışan yok.")


async def eksik_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_mi(update.effective_user.id):
        await update.message.reply_text("⛔ Yetkiniz yok.")
        return
    from config import EGITIMLER
    calisanlar = tum_calisanlar()
    args = context.args

    if args:
        try:
            uid = int(args[0])
        except ValueError:
            await update.message.reply_text("❌ Geçersiz ID.")
            return
        ad = calisanlar.get(uid, {}).get("ad_soyad", f"ID:{uid}")
        eksikler = eksik_egitimler(uid)
        if not eksikler:
            await update.message.reply_text(f"✅ *{ad}* tüm eğitimleri tamamlamış!", parse_mode="Markdown")
            return
        liste = "\n".join([f"• {EGITIMLER[e]['baslik']}" for e in eksikler if e in EGITIMLER])
        await update.message.reply_text(
            f"📋 *{ad}* — Eksik ({len(eksikler)}/{len(EGITIMLER)}):\n\n{liste}",
            parse_mode="Markdown"
        )
    else:
        satirlar = []
        for uid, c in calisanlar.items():
            eksikler = eksik_egitimler(uid)
            tamamlanan = len(EGITIMLER) - len(eksikler)
            bar = "█" * tamamlanan + "░" * len(eksikler)
            satirlar.append(f"{c['ad_soyad']}: {bar} {tamamlanan}/{len(EGITIMLER)}")
        metin = "📊 *Eğitim Tamamlama Durumu:*\n\n" + "\n".join(satirlar) if satirlar else "Henüz çalışan yok."
        await update.message.reply_text(metin, parse_mode="Markdown")
