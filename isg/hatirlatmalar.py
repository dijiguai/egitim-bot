"""
isg/hatirlatmalar.py
====================
Scheduler'dan çağrılan async ISG bildirim fonksiyonları.
bildirim_sistemi.py'deki sync fonksiyonları async wrapper ile sarar.
"""

import logging
import asyncio

logger = logging.getLogger(__name__)


async def haftalik_egitim_ozeti(app=None):
    """Her Pazartesi 08:30 — haftalık ISG özeti."""
    try:
        from bildirim_sistemi import haftalik_isg_ozet
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, haftalik_isg_ozet)
        logger.info("Haftalık ISG özeti gönderildi")
        return 1
    except Exception as e:
        logger.error(f"Haftalık ISG özet hatası: {e}")
        return 0


async def uzman_sozlesme_uyarisi(app=None):
    """Her Pazartesi 09:00 — sözleşme bitiş uyarıları."""
    try:
        from bildirim_sistemi import uzman_sozlesme_uyari
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, uzman_sozlesme_uyari)
        logger.info("Uzman sözleşme uyarısı gönderildi")
        return 1
    except Exception as e:
        logger.error(f"Uzman sözleşme uyarı hatası: {e}")
        return 0


async def aylik_zorunlu_kontrol(app=None):
    """Her Pazartesi 09:15 — zorunlu eğitim yaklaşan uyarıları."""
    try:
        from bildirim_sistemi import zorunlu_egitim_yaklasan_uyari
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, zorunlu_egitim_yaklasan_uyari)
        logger.info("Zorunlu eğitim yaklaşan uyarısı gönderildi")
        return 1
    except Exception as e:
        logger.error(f"Zorunlu eğitim uyarı hatası: {e}")
        return 0
