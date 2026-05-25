from app.providers.ocr.base import OCRProvider
from app.providers.ocr.paddle_provider import PaddleOCRProvider, paddle_provider
from app.providers.ocr.trocr_provider import TrOCRProvider, trocr_provider

__all__ = [
    "OCRProvider",
    "PaddleOCRProvider",
    "paddle_provider",
    "TrOCRProvider",
    "trocr_provider",
]
