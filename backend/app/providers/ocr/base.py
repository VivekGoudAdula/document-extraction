from abc import ABC, abstractmethod
from pathlib import Path

from app.models.ocr_models import OCRResult


class OCRProvider(ABC):
    """
    Abstract OCR provider interface.

    All implementations must run inference locally on the backend server.
    Uploaded images must never be sent to third-party OCR APIs.
    """

    @abstractmethod
    async def extract_text(self, file_path: str | Path) -> OCRResult:
        """Extract text/structure from a document path."""
        pass
