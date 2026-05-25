"""
Local PaddleOCR provider — layout-heavy documents, forms, invoices, screenshots.

SECURITY: PaddleOCR runs entirely on this server. No cloud OCR API calls.
"""

import asyncio
import logging
import os
from pathlib import Path

from app.models.ocr_models import OCRResult
from app.providers.ocr.base import OCRProvider

logger = logging.getLogger(__name__)

EXECUTION_MODE = "local"

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}

_paddle_ocr = None


def _get_paddle_ocr():
    global _paddle_ocr
    if _paddle_ocr is None:
        os.environ.setdefault("FLAGS_use_mkldnn", "0")
        os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
        from paddleocr import PaddleOCR

        try:
            _paddle_ocr = PaddleOCR(
                lang="en",
                use_textline_orientation=True,
            )
        except TypeError:
            _paddle_ocr = PaddleOCR(lang="en")
    return _paddle_ocr


def _sort_lines_by_layout(lines: list[tuple[float, str, float]]) -> list[str]:
    if not lines:
        return []
    lines.sort(key=lambda item: (round(item[0] / 12), item[2]))
    return [text for _, text, _ in lines]


def _parse_paddle_v2(raw: list) -> tuple[str, list[dict[str, float | str]]]:
    layout_lines: list[tuple[float, str, float]] = []
    confidence_entries: list[dict[str, float | str]] = []

    for page in raw or []:
        if not page:
            continue
        for item in page:
            if not item or len(item) < 2:
                continue
            box, text_info = item[0], item[1]
            if isinstance(text_info, (list, tuple)) and len(text_info) >= 2:
                text, conf = str(text_info[0]), float(text_info[1])
            else:
                text, conf = str(text_info), 0.0
            text = text.strip()
            if not text:
                continue
            y_center = sum(point[1] for point in box) / max(len(box), 1)
            x_min = min(point[0] for point in box)
            layout_lines.append((y_center, text, x_min))
            confidence_entries.append({"text": text, "confidence": conf})

    ordered = _sort_lines_by_layout(layout_lines)
    return "\n".join(ordered).strip(), confidence_entries


def _parse_paddle_v3(results: list) -> tuple[str, list[dict[str, float | str]]]:
    layout_lines: list[tuple[float, str, float]] = []
    confidence_entries: list[dict[str, float | str]] = []

    for result in results or []:
        data = result if isinstance(result, dict) else getattr(result, "json", None)
        if data is None and hasattr(result, "keys"):
            data = dict(result)
        if not isinstance(data, dict):
            continue

        texts = data.get("rec_texts") or data.get("texts") or []
        scores = data.get("rec_scores") or data.get("scores") or []
        polys = data.get("dt_polys") or data.get("rec_polys") or data.get("boxes") or []

        for index, text in enumerate(texts):
            text = str(text).strip()
            if not text:
                continue
            conf = float(scores[index]) if index < len(scores) else 0.0
            y_center, x_min = float(index), float(index)
            if index < len(polys) and polys[index]:
                poly = polys[index]
                y_center = sum(point[1] for point in poly) / max(len(poly), 1)
                x_min = min(point[0] for point in poly)
            layout_lines.append((y_center, text, x_min))
            confidence_entries.append({"text": text, "confidence": conf})

    ordered = _sort_lines_by_layout(layout_lines)
    return "\n".join(ordered).strip(), confidence_entries


class PaddleOCRProvider(OCRProvider):
    def _extract_sync(self, file_path: Path) -> OCRResult:
        if file_path.suffix.lower() not in IMAGE_EXTENSIONS:
            return {
                "provider": "paddleocr",
                "execution_mode": EXECUTION_MODE,
                "text": "",
                "confidence": [],
                "success": False,
                "error": f"Unsupported file type: {file_path.suffix}",
            }

        try:
            ocr = _get_paddle_ocr()
            if hasattr(ocr, "predict"):
                raw = ocr.predict(str(file_path))
                full_text, confidence_entries = _parse_paddle_v3(list(raw))
            else:
                raw = ocr.ocr(str(file_path), cls=True)
                full_text, confidence_entries = _parse_paddle_v2(raw)

            if full_text:
                return {
                    "provider": "paddleocr",
                    "execution_mode": EXECUTION_MODE,
                    "text": full_text,
                    "confidence": confidence_entries,
                    "success": True,
                    "error": "",
                }
        except Exception as exc:
            logger.warning("PaddleOCR failed for %s: %s", file_path, exc)

        return {
            "provider": "paddleocr",
            "execution_mode": EXECUTION_MODE,
            "text": "",
            "confidence": [],
            "success": False,
            "error": "PaddleOCR produced no text or raised an error",
        }

    async def extract_text(self, file_path: str | Path) -> OCRResult:
        path = Path(file_path)
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._extract_sync, path)


paddle_provider = PaddleOCRProvider()
