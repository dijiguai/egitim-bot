"""
Admin komutları
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import ADMIN_IDS, EGITIMLER, GRUP_ID
from calisanlar import tum_calisanlar

logger = logging.getLogger(__name__)

def admin_mi(uid): return uid in ADMIN_IDS


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if admin_mi(user.id):
        await update.message.reply_text(
            f"👋 Merhaba *{user.first_name}*!\n\n"
            f"🛠 *Admin Komutları:*\n"
            f"/egitim\\_gonder [id] — Eğitim gönder\n"
            f"/rapor — Bugünkü özet\n"
            f"/kalanlar — Eğitim almamışlar\n"
            f"/izin\\_ekle [tid] [tarih] — İzin ekle\n"
            f"/izin\\_kaldir [tid] [tarih] — İzin kaldır\n"
            f"/izinliler — Bugün izinliler\n"
            f"/eksik — Eksik eğitim özeti\n"
            f"/hizli\\_ekle [tid] [gorev] [dogum] — Hızlı ekle\n"
            f"/bekleyenler — Onay bekleyen üyeler\n"
            f"/yardim — Tüm komutlar",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"👋 Merhaba *{user.first_name}*!\n\n"
            f"Eğitim sisteminize hoş geldiniz. "
            f"Bugünkü eğitim hazır olduğunda bildirim alacaksınız.",
            parse_mode="Markdown"
        )


async def egitim_gonder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_mi(update.effective_user.id):
        await update.message.reply_text("⛔ Yetkiniz yok.")
        return

    args = context.args
    if not args:
        liste = "\n".join([f"• `{k}` — {v['baslik']}" for k, v in EGITIMLER.items()])
        await update.message.reply_text(
            f"📋 *Mevcut Eğitimler:*\n\n{liste}\n\n"
            f"Kullanım: `/egitim_gonder [egitim_id]`",
            parse_mode="Markdown"
        )
        return

    egitim_id = args[0]
    egitim = EGITIMLER.get(egitim_id)
    if not egitim:
        await update.message.reply_text(f"❌ '{egitim_id}' bulunamadı.")
        return

    keyboard = [[InlineKeyboardButton("▶️ Eğitime Başla", callback_data=f"egitim_baslat:{egitim_id}")]]
    markup = InlineKeyboardMarkup(keyboard)

    # Gruba gönder
    if GRUP_ID and GRUP_ID != 0:
        try:
            await context.bot.send_message(
                chat_id=GRUP_ID,
                text=f"📋 *{egitim['baslik']}* eğitimi başladı!\n\nKatılmak için butona basın 👇",
                parse_mode="Markdown",
                reply_markup=markup
            )
        except Exception as e:
            logger.error(f"Grup mesajı hatası: {e}")

    # Çalışanlara kişisel gönder
    calisanlar = tum_calisanlar()
    import asyncio
    for uid, c in calisanlar.items():
        try:
            await context.bot.send_message(
                chat_id=uid,
                text=f"📋 Yeni eğitim: *{egitim['baslik']}*\n\nBaşlamak için butona basın 👇",
                parse_mode="Markdown",
                reply_markup=markup
            )
            await asyncio.sleep(0.1)
        except Exception as e:
            logger.warning(f"{c['ad_soyad']} bildirimi gönderilemedi: {e}")

    await update.message.reply_text(f"✅ *{egitim['baslik']}* gönderildi.", parse_mode="Markdown")


async def rapor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_mi(update.effective_user.id):
        await update.message.reply_text("⛔ Yetkiniz yok.")
        return
    from sheets import kayitlari_getir
    from datetime import date as d
    bugun = d.today().strftime("%d.%m.%Y")
    try:
        kayitlar = kayitlari_getir(bugun, bugun)
        gecti = [k for k in kayitlar if k.get("durum") == "GEÇTİ"]
        kaldi = [k for k in kayitlar if k.get("durum") == "KALDI"]
        await update.message.reply_text(
            f"📊 *{bugun} Raporu*\n\n"
            f"✅ Geçti: {len(gecti)}\n"
            f"❌ Kaldı: {len(kaldi)}\n"
            f"📋 Toplam: {len(kayitlar)}",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Rapor alınamadı: {e}")


async def kalanlar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_mi(update.effective_user.id):
        await update.message.reply_text("⛔ Yetkiniz yok.")
        return
    from sheets import kayitlari_getir
    from datetime import date as d
    bugun = d.today().strftime("%d.%m.%Y")
    calisanlar = tum_calisanlar()
    try:
        kayitlar = kayitlari_getir(bugun, bugun)
        katilan_idler = {k.get("telegram_id") for k in kayitlar}
        kalanlar_list = [
            f"• {c['ad_soyad']} ({c['gorev']})"
            for uid, c in calisanlar.items()
            if str(uid) not in katilan_idler
        ]
        if kalanlar_list:
            await update.message.reply_text(
                f"⏳ *Bugün Eğitim Almayan Çalışanlar:*\n\n" + "\n".join(kalanlar_list),
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("✅ Tüm çalışanlar bugün eğitimini tamamladı!")
    except Exception as e:
        await update.message.reply_text(f"❌ Veri alınamadı: {e}")


async def yardim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_mi(update.effective_user.id):
        return
    await update.message.reply_text(
        "📖 *Tüm Admin Komutları:*\n\n"
        "/egitim\\_gonder [id] — Manuel eğitim gönder\n"
        "/rapor — Bugünkü özet\n"
        "/kalanlar — Eğitim almayan çalışanlar\n"
        "/izin\\_ekle [tid] [tarih] — İzin ekle\n"
        "/izin\\_kaldir [tid] [tarih] — İzin kaldır\n"
        "/izinliler — Bugün izinliler\n"
        "/eksik — Eksik eğitim özeti\n"
        "/hizli\\_ekle [tid] [gorev] [dogum] — Hızlı çalışan ekle\n"
        "/bekleyenler — Onay bekleyen üyeler\n",
        parse_mode="Markdown"
    )


async def hizli_ekle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /hizli_ekle 123456789 Operatör 15.06.1990
    Telegram adını otomatik alır, görev ve doğum tarihini siz girin.
    """
    if not admin_mi(update.effective_user.id):
        await update.message.reply_text("⛔ Yetkiniz yok.")
        return

    args = context.args
    if len(args) < 3:
        await update.message.reply_text(
            "Kullanım: `/hizli_ekle [telegram_id] [gorev] [GG.AA.YYYY]`\n"
            "Örnek: `/hizli_ekle 123456789 Operatör 15.06.1990`",
            parse_mode="Markdown"
        )
        return

    try:
        tid = int(args[0])
    except ValueError:
        await update.message.reply_text("❌ Geçersiz Telegram ID.")
        return

    gorev = args[1]
    dogum = args[2]

    # Onay bekleyenlerden adı al
    from handlers.kayit_handler import onay_bekleyenler
    bilgi = onay_bekleyenler.pop(tid, {})
    ad = bilgi.get("ad", f"Çalışan {tid}")

    from calisanlar import calisan_ekle
    calisan_ekle(tid, ad, dogum, gorev)

    await update.message.reply_text(
        f"✅ *{ad}* sisteme eklendi!\n\n"
        f"Telegram ID: `{tid}`\n"
        f"Görev: {gorev}\n"
        f"Doğum: {dogum}",
        parse_mode="Markdown"
    )


async def bekleyenler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Onay bekleyen üyeleri listele."""
    if not admin_mi(update.effective_user.id):
        return

    from handlers.kayit_handler import onay_bekleyenler
    if not onay_bekleyenler:
        await update.message.reply_text("✅ Onay bekleyen kimse yok.")
        return

    satirlar = []
    for tid, bilgi in onay_bekleyenler.items():
        satirlar.append(f"• *{bilgi['ad']}* {bilgi['username']}\n  ID: `{tid}`")

    await update.message.reply_text(
        "👥 *Onay Bekleyen Üyeler:*\n\n" + "\n\n".join(satirlar) + "\n\n"
        "Eklemek için: `/hizli_ekle [id] [gorev] [dogum]`",
        parse_mode="Markdown"
    )
