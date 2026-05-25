import asyncio
import logging
from pathlib import Path

from app.models.ocr_models import OCRResult
from app.providers.ocr.base import OCRProvider

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}

_easyocr_reader = None


def _get_easyocr_reader():
    global _easyocr_reader
    if _easyocr_reader is None:
        import easyocr

        _easyocr_reader = easyocr.Reader(["en"], gpu=False, verbose=False)
    return _easyocr_reader


class EasyOCRProvider(OCRProvider):
    def _extract_sync(self, file_path: Path) -> OCRResult:
        if file_path.suffix.lower() not in IMAGE_EXTENSIONS:
            return {
                "provider": "easyocr",
                "text": "",
                "confidence": [],
                "success": False,
                "error": f"Unsupported file type: {file_path.suffix}",
            }

        try:
            reader = _get_easyocr_reader()
            detections = reader.readtext(str(file_path))
        except Exception as exc:
            logger.exception("EasyOCR failed for %s", file_path)
            return {
                "provider": "easyocr",
                "text": "",
                "confidence": [],
                "success": False,
                "error": str(exc),
            }

        lines: list[tuple[float, str, float]] = []
        confidence_entries: list[dict[str, float | str]] = []

        for item in detections:
            if len(item) < 3:
                continue
            box, text, conf = item[0], str(item[1]).strip(), float(item[2])
            if not text:
                continue
            y_center = sum(point[1] for point in box) / max(len(box), 1)
            x_min = min(point[0] for point in box)
            lines.append((y_center, text, x_min))
            confidence_entries.append({"text": text, "confidence": conf})

        lines.sort(key=lambda row: (round(row[0] / 12), row[2]))
        full_text = "\n".join(text for _, text, _ in lines).strip()

        return {
            "provider": "easyocr",
            "text": full_text,
            "confidence": confidence_entries,
            "success": bool(full_text),
            "error": "" if full_text else "No text detected",
        }

    async def extract_text(self, file_path: str | Path) -> OCRResult:
        path = Path(file_path)
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._extract_sync, path)


easyocr_provider = EasyOCRProvider()
