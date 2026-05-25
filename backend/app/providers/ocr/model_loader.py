"""
OCR model warmup — loads PaddleOCR and TrOCR once at application startup.

SECURITY: Models are downloaded from HuggingFace/Paddle hubs only during initial
setup (from_pretrained / PaddleOCR init). All inference runs locally on the server.
Uploaded images are never sent to external OCR APIs.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

_warmup_complete = False
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="ocr-warmup")


def _warmup_sync() -> None:
    from app.providers.ocr.paddle_provider import _get_paddle_ocr
    from app.providers.ocr.trocr_provider import _get_trocr_models

    logger.info("Warming up local PaddleOCR model...")
    _get_paddle_ocr()
    logger.info("Warming up local TrOCR model (microsoft/trocr-base-handwritten)...")
    _get_trocr_models()
    logger.info("Local OCR models ready (execution_mode=local).")


async def warmup_ocr_models() -> None:
    """Load OCR models once at startup; safe to call multiple times."""
    global _warmup_complete
    if _warmup_complete:
        return

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(_executor, _warmup_sync)
    _warmup_complete = True


def is_warmup_complete() -> bool:
    return _warmup_complete
