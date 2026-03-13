"""
Admin komutlari
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
    await update.message.reply_text(
        f"Merhaba *{user.first_name}*! Admin panelindesiniz.\n\n"
        f"Komutlar icin /yardim",
        parse_mode="Markdown"
    )


async def egitim_gonder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_mi(update.effective_user.id): return
    args = context.args
    if not args:
        liste = "\n".join([f"- {k}: {v['baslik']}" for k, v in EGITIMLER.items()])
        await update.message.reply_text(f"Egitimler:\n{liste}\n\nKullanim: /egitim_gonder [id]")
        return

    egitim_id = args[0]
    egitim = EGITIMLER.get(egitim_id)
    if not egitim:
        await update.message.reply_text(f"'{egitim_id}' bulunamadi.")
        return

    from durum import aktif_egitim_set
    aktif_egitim_set(egitim_id)

    keyboard = [[InlineKeyboardButton("Egitime Basla", callback_data=f"egitim_baslat:{egitim_id}")]]
    markup = InlineKeyboardMarkup(keyboard)

    import asyncio, requests as req_lib, os
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    base = f"https://api.telegram.org/bot{token}"

    if GRUP_ID and GRUP_ID != 0:
        try:
            req_lib.post(f"{base}/sendMessage", json={
                "chat_id": GRUP_ID,
                "text": f"*{egitim['baslik']}* eğitimi başladı!\n\nKatılmak için 👇",
                "parse_mode": "Markdown",
                "reply_markup": {"inline_keyboard": [[{"text": "Egitime Basla", "callback_data": f"egitim_baslat:{egitim_id}"}]]}
            }, timeout=10)
        except Exception as e:
            logger.error(f"Grup mesaji hatasi: {e}")

    calisanlar = tum_calisanlar()
    for uid, c in calisanlar.items():
        try:
            await context.bot.send_message(
                chat_id=uid,
                text=f"Yeni egitim: *{egitim['baslik']}*\n\nBaslamak icin 👇",
                parse_mode="Markdown", reply_markup=markup
            )
            await asyncio.sleep(0.1)
        except Exception as e:
            logger.warning(f"{c['ad_soyad']} bildirimi gonderilemedi: {e}")

    await update.message.reply_text(f"*{egitim['baslik']}* gonderildi.", parse_mode="Markdown")


async def egitim_tekrar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /egitim_tekrar [telegram_id]
    Calisana bugun icin 1 ekstra deneme hakki verir ve eğitimi tekrar gönderir.
    """
    if not admin_mi(update.effective_user.id): return

    args = context.args
    if not args:
        await update.message.reply_text(
            "Kullanim: /egitim_tekrar [telegram_id]\n\n"
            "Calisanin bugunluk deneme hakkini 1 arttirir."
        )
        return

    try:
        tid = int(args[0])
    except ValueError:
        await update.message.reply_text("Gecersiz ID.")
        return

    from durum import ekstra_hak_ver, gunun_egitim_id, aktif_egitim_set
    egitim_id = gunun_egitim_id()
    if not egitim_id:
        await update.message.reply_text("Bugun aktif egitim yok.")
        return

    egitim = EGITIMLER.get(egitim_id)
    calisan = tum_calisanlar().get(tid)
    if not calisan:
        await update.message.reply_text("Calisan bulunamadi.")
        return

    ekstra_hak_ver(tid)
    aktif_egitim_set(egitim_id)

    keyboard = [[InlineKeyboardButton("Egitime Basla", callback_data=f"egitim_baslat:{egitim_id}")]]
    try:
        await context.bot.send_message(
            chat_id=tid,
            text=(
                f"Yoneticiniz size ek deneme hakki tanimladı.\n\n"
                f"*{egitim['baslik']}*\n\nBaslamak icin 👇"
            ),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        await update.message.reply_text(
            f"*{calisan['ad_soyad']}* icin ekstra hak verildi ve egitim gonderildi.",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"Mesaj gonderilemedi: {e}")


async def rapor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_mi(update.effective_user.id): return
    from sheets import kayitlari_getir
    from datetime import date
    bugun = date.today().strftime("%d.%m.%Y")
    try:
        kayitlar = kayitlari_getir(bugun, bugun)
        gecti = [k for k in kayitlar if k.get("durum") in ("GECTI", "GECTİ")]
        kaldi = [k for k in kayitlar if k.get("durum") == "KALDI"]

        # Deneme sayisi ozeti
        den_ozet = ""
        for k in kayitlar:
            den = k.get("deneme_no", "")
            if den and str(den) != "1":
                den_ozet += f"\n  {k.get('ad_soyad','?')}: {den}. denemede"

        mesaj = (
            f"*{bugun} Raporu*\n\n"
            f"Gecti: {len(gecti)}\n"
            f"Kaldi: {len(kaldi)}\n"
            f"Toplam: {len(kayitlar)}"
        )
        if den_ozet:
            mesaj += f"\n\nBirden fazla deneme:{den_ozet}"

        await update.message.reply_text(mesaj, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Rapor alinamadi: {e}")


async def kalanlar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_mi(update.effective_user.id): return
    from sheets import kayitlari_getir
    from datetime import date
    bugun = date.today().strftime("%d.%m.%Y")
    calisanlar = tum_calisanlar()
    try:
        kayitlar = kayitlari_getir(bugun, bugun)
        katilan = {str(k.get("telegram_id")) for k in kayitlar}
        liste = [
            f"- {c['ad_soyad']} ({c['gorev']})  /egitim\\_tekrar {uid}"
            for uid, c in calisanlar.items()
            if str(uid) not in katilan
        ]
        if liste:
            await update.message.reply_text(
                f"*Bugun egitim almayan calisanlar:*\n\n" + "\n".join(liste) +
                f"\n\nEkstra hak icin komutu kullanin.",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("Tum calisanlar bugun egitimini tamamladi!")
    except Exception as e:
        await update.message.reply_text(f"Veri alinamadi: {e}")


async def yardim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_mi(update.effective_user.id): return
    await update.message.reply_text(
        "*Admin Komutlari:*\n\n"
        "/egitim\\_gonder [id] - Manuel egitim gonder\n"
        "/egitim\\_tekrar [tid] - Calisana ekstra hak ver\n"
        "/rapor - Bugunun ozeti (kacinci denemede gecti)\n"
        "/kalanlar - Egitim almayan calisanlar\n"
        "/izin\\_ekle [tid] [tarih] - Izin ekle\n"
        "/izin\\_kaldir [tid] [tarih] - Izin kaldir\n"
        "/izinliler - Bugun izinliler\n"
        "/eksik - Eksik egitim ozeti\n"
        "/bekleyenler - Onay bekleyen uyeler",
        parse_mode="Markdown"
    )


async def hizli_ekle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_mi(update.effective_user.id): return
    args = context.args
    if len(args) < 3:
        await update.message.reply_text("Kullanim: /hizli_ekle [telegram_id] [gorev] [GG.AA.YYYY]")
        return
    try:
        tid = int(args[0])
    except ValueError:
        await update.message.reply_text("Gecersiz ID.")
        return

    gorev = args[1]
    dogum = args[2]
    from handlers.kayit_handler import onay_bekleyenler
    bilgi = onay_bekleyenler.pop(tid, {})
    ad = bilgi.get("ad", f"Calisan {tid}")
    from calisanlar import calisan_ekle
    calisan_ekle(tid, ad, dogum, gorev)
    await update.message.reply_text(f"*{ad}* eklendi! ID: {tid}", parse_mode="Markdown")


async def bekleyenler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_mi(update.effective_user.id): return
    from handlers.kayit_handler import onay_bekleyenler
    if not onay_bekleyenler:
        await update.message.reply_text("Onay bekleyen kimse yok.")
        return
    satirlar = [f"- *{b['ad']}* {b['username']} | `{tid}`" for tid, b in onay_bekleyenler.items()]
    await update.message.reply_text(
        "*Onay Bekleyenler:*\n\n" + "\n".join(satirlar) +
        "\n\nEklemek: /hizli_ekle [id] [gorev] [dogum]",
        parse_mode="Markdown"
    )
