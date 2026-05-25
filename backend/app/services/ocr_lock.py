"""Serialize OCR on memory-constrained hosts (Render 512MB)."""

import asyncio

from app.config import get_settings

_semaphore: asyncio.Semaphore | None = None


def get_ocr_semaphore() -> asyncio.Semaphore:
    global _semaphore
    if _semaphore is None:
        slots = 1 if get_settings().is_low_memory_deploy else 2
        _semaphore = asyncio.Semaphore(slots)
    return _semaphore
