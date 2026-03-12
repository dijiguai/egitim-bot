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
            f"👋 Merhaba *{user.first_name}*! Admin panelindesiniz.\n\n"
            f"Tüm komutlar için /yardim",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"👋 Merhaba *{user.first_name}*!\n"
            f"Bugünkü eğitim hazır olduğunda bildirim alacaksınız.",
            parse_mode="Markdown"
        )


async def egitim_gonder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manuel eğitim gönder — aynı zamanda eğitimi 'açık' yapar."""
    if not admin_mi(update.effective_user.id):
        await update.message.reply_text("⛔ Yetkiniz yok.")
        return

    args = context.args
    if not args:
        liste = "\n".join([f"• `{k}` — {v['baslik']}" for k, v in EGITIMLER.items()])
        await update.message.reply_text(
            f"📋 *Mevcut Eğitimler:*\n\n{liste}\n\n"
            f"Kullanım: `/egitim_gonder [id]`",
            parse_mode="Markdown"
        )
        return

    egitim_id = args[0]
    egitim = EGITIMLER.get(egitim_id)
    if not egitim:
        await update.message.reply_text(f"❌ '{egitim_id}' bulunamadı.")
        return

    from durum import aktif_egitim_set
    aktif_egitim_set(egitim_id)

    keyboard = [[InlineKeyboardButton("▶️ Eğitime Başla", callback_data=f"egitim_baslat:{egitim_id}")]]
    markup = InlineKeyboardMarkup(keyboard)

    if GRUP_ID and GRUP_ID != 0:
        try:
            await context.bot.send_message(
                chat_id=GRUP_ID,
                text=f"📋 *{egitim['baslik']}* eğitimi başladı!\n\nKatılmak için 👇",
                parse_mode="Markdown", reply_markup=markup
            )
        except Exception as e:
            logger.error(f"Grup mesajı hatası: {e}")

    import asyncio
    calisanlar = tum_calisanlar()
    for uid, c in calisanlar.items():
        try:
            await context.bot.send_message(
                chat_id=uid,
                text=f"📋 Yeni eğitim: *{egitim['baslik']}*\n\nBaşlamak için 👇",
                parse_mode="Markdown", reply_markup=markup
            )
            await asyncio.sleep(0.1)
        except Exception as e:
            logger.warning(f"{c['ad_soyad']} bildirimi gönderilemedi: {e}")

    await update.message.reply_text(f"✅ *{egitim['baslik']}* gönderildi.", parse_mode="Markdown")


async def egitim_tekrar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /egitim_tekrar [telegram_id] — Kalan çalışana bugünkü eğitimi tekrar açar.
    """
    if not admin_mi(update.effective_user.id):
        await update.message.reply_text("⛔ Yetkiniz yok.")
        return

    args = context.args
    if not args:
        await update.message.reply_text(
            "Kullanım: `/egitim_tekrar [telegram_id]`\n"
            "Bugünkü eğitimi o çalışana tekrar açar.",
            parse_mode="Markdown"
        )
        return

    try:
        tid = int(args[0])
    except ValueError:
        await update.message.reply_text("❌ Geçersiz ID.")
        return

    from durum import gunun_egitim_id, tekrar_izni_ver, aktif_egitim_set
    egitim_id = gunun_egitim_id()

    if not egitim_id:
        await update.message.reply_text("❌ Bugün aktif eğitim yok.")
        return

    egitim = EGITIMLER.get(egitim_id)
    calisan = tum_calisanlar().get(tid)
    if not calisan:
        await update.message.reply_text("❌ Çalışan bulunamadı.")
        return

    # Eğitimi tekrar açık yap
    aktif_egitim_set(egitim_id)
    # Tamamlanmış kaydından kaldır (tekrar girebilsin)
    tekrar_izni_ver(tid, egitim_id)

    keyboard = [[InlineKeyboardButton("▶️ Eğitime Başla", callback_data=f"egitim_baslat:{egitim_id}")]]
    markup = InlineKeyboardMarkup(keyboard)

    try:
        await context.bot.send_message(
            chat_id=tid,
            text=(
                f"📋 Yöneticiniz bugünkü eğitimi tekrar almanız için açtı.\n\n"
                f"*{egitim['baslik']}*\n\nBaşlamak için 👇"
            ),
            parse_mode="Markdown", reply_markup=markup
        )
        await update.message.reply_text(
            f"✅ *{calisan['ad_soyad']}* için eğitim tekrar açıldı.",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Mesaj gönderilemedi: {e}")


async def rapor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_mi(update.effective_user.id): return
    from sheets import kayitlari_getir
    from datetime import date
    bugun = date.today().strftime("%d.%m.%Y")
    try:
        kayitlar = kayitlari_getir(bugun, bugun)
        gecti = [k for k in kayitlar if k.get("durum") == "GEÇTİ"]
        kaldi = [k for k in kayitlar if k.get("durum") == "KALDI"]
        await update.message.reply_text(
            f"📊 *{bugun} Raporu*\n\n"
            f"✅ Geçti: {len(gecti)}\n❌ Kaldı: {len(kaldi)}\n📋 Toplam: {len(kayitlar)}",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Rapor alınamadı: {e}")


async def kalanlar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_mi(update.effective_user.id): return
    from sheets import kayitlari_getir
    from datetime import date
    bugun = date.today().strftime("%d.%m.%Y")
    calisanlar = tum_calisanlar()
    try:
        kayitlar = kayitlari_getir(bugun, bugun)
        katilan = {k.get("telegram_id") for k in kayitlar}
        liste = [
            f"• {c['ad_soyad']} ({c['gorev']}) — /egitim\\_tekrar {uid}"
            for uid, c in calisanlar.items()
            if str(uid) not in katilan
        ]
        if liste:
            await update.message.reply_text(
                f"⏳ *Bugün Eğitim Almayan Çalışanlar:*\n\n" + "\n".join(liste) + 
                f"\n\nTekrar açmak için komuta tıklayın.",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("✅ Tüm çalışanlar bugün eğitimini tamamladı!")
    except Exception as e:
        await update.message.reply_text(f"❌ Veri alınamadı: {e}")


async def yardim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_mi(update.effective_user.id): return
    await update.message.reply_text(
        "📖 *Admin Komutları:*\n\n"
        "/egitim\\_gonder [id] — Manuel eğitim gönder\n"
        "/egitim\\_tekrar [tid] — Çalışana tekrar al\n"
        "/rapor — Bugünkü özet\n"
        "/kalanlar — Eğitim almayan çalışanlar\n"
        "/izin\\_ekle [tid] [tarih] — İzin ekle\n"
        "/izin\\_kaldir [tid] [tarih] — İzin kaldır\n"
        "/izinliler — Bugün izinliler\n"
        "/eksik — Eksik eğitim özeti\n"
        "/hizli\\_ekle [tid] [gorev] [dogum] — Hızlı çalışan ekle\n"
        "/bekleyenler — Onay bekleyen üyeler",
        parse_mode="Markdown"
    )


async def hizli_ekle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_mi(update.effective_user.id): return
    args = context.args
    if len(args) < 3:
        await update.message.reply_text(
            "Kullanım: `/hizli_ekle [telegram_id] [gorev] [GG.AA.YYYY]`",
            parse_mode="Markdown"
        )
        return
    try:
        tid = int(args[0])
    except ValueError:
        await update.message.reply_text("❌ Geçersiz ID.")
        return

    gorev = args[1]
    dogum = args[2]

    from handlers.kayit_handler import onay_bekleyenler
    bilgi = onay_bekleyenler.pop(tid, {})
    ad = bilgi.get("ad", f"Çalışan {tid}")

    from calisanlar import calisan_ekle
    calisan_ekle(tid, ad, dogum, gorev)

    await update.message.reply_text(
        f"✅ *{ad}* sisteme eklendi!\nID: `{tid}` · Görev: {gorev}",
        parse_mode="Markdown"
    )


async def bekleyenler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_mi(update.effective_user.id): return
    from handlers.kayit_handler import onay_bekleyenler
    if not onay_bekleyenler:
        await update.message.reply_text("✅ Onay bekleyen kimse yok.")
        return
    satirlar = [f"• *{b['ad']}* {b['username']}\n  ID: `{tid}`" for tid, b in onay_bekleyenler.items()]
    await update.message.reply_text(
        "👥 *Onay Bekleyenler:*\n\n" + "\n\n".join(satirlar) +
        "\n\nEklemek: `/hizli_ekle [id] [gorev] [dogum]`",
        parse_mode="Markdown"
    )
