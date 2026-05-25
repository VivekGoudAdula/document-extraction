"""
OCR model warmup — optional at startup (disabled on Render/low-memory hosts).

SECURITY: Models download once locally; inference stays on-server.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

from app.config import get_settings

logger = logging.getLogger(__name__)

_warmup_complete = False
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ocr-warmup")


def _warmup_sync() -> None:
    settings = get_settings()
    if settings.paddle_enabled:
        from app.providers.ocr.paddle_provider import _get_paddle_ocr

        logger.info("Warming up local PaddleOCR...")
        _get_paddle_ocr()
    if settings.trocr_enabled:
        from app.providers.ocr.trocr_provider import _get_trocr_models

        logger.info("Warming up local TrOCR...")
        _get_trocr_models()
    logger.info("Local OCR warmup complete (execution_mode=local).")


async def warmup_ocr_models() -> None:
    """Load OCR models at startup only when enabled (off by default on Render)."""
    global _warmup_complete
    settings = get_settings()
    if not settings.should_warmup_ocr_on_startup:
        logger.info(
            "Skipping OCR startup warmup (low_memory=%s). Models load on first /extract.",
            settings.is_low_memory_deploy,
        )
        return
    if _warmup_complete:
        return

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(_executor, _warmup_sync)
    _warmup_complete = True


def is_warmup_complete() -> bool:
    return _warmup_complete
