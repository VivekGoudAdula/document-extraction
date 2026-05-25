"""
OCR model warmup — optional at startup; background warmup on Render.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

from app.config import get_settings

logger = logging.getLogger(__name__)

_warmup_complete = False
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ocr-warmup")


def _warmup_paddle_sync() -> None:
    from app.providers.ocr.paddle_provider import _get_paddle_ocr

    logger.info("Warming up PaddleOCR (load models into RAM)...")
    _get_paddle_ocr()
    logger.info("PaddleOCR warmup complete.")


async def warmup_ocr_models() -> None:
    """Load OCR models at startup when enabled (off on Render low-memory by default)."""
    global _warmup_complete
    settings = get_settings()
    if not settings.should_warmup_ocr_on_startup:
        return
    if _warmup_complete:
        return

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(_executor, _warmup_paddle_sync)
    _warmup_complete = True


def schedule_background_paddle_warmup() -> None:
    """Fire-and-forget Paddle load after server is listening (Render)."""
    settings = get_settings()
    if not settings.paddle_enabled:
        return
    if settings.trocr_enabled:
        return

    async def _run() -> None:
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(_executor, _warmup_paddle_sync)
        except Exception as exc:
            logger.warning("Background PaddleOCR warmup failed: %s", exc)

    try:
        asyncio.get_running_loop().create_task(_run())
        logger.info("Scheduled background PaddleOCR warmup")
    except RuntimeError:
        logger.warning("Could not schedule PaddleOCR warmup")


def is_warmup_complete() -> bool:
    return _warmup_complete
