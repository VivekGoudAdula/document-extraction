"""
Local TrOCR provider — handwritten and difficult text recognition.

SECURITY: Uses VisionEncoderDecoderModel.from_pretrained() to cache weights
locally. Inference runs on this server only. No HuggingFace Inference API.
"""

import asyncio
import logging
from pathlib import Path

from app.models.ocr_models import OCRResult
from app.providers.ocr.base import OCRProvider

logger = logging.getLogger(__name__)

EXECUTION_MODE = "local"

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}

TROCR_MODEL_ID = "microsoft/trocr-base-handwritten"

_trocr_processor = None
_trocr_model = None


def _get_trocr_models():
    global _trocr_processor, _trocr_model
    if _trocr_model is None:
        import torch
        from transformers import TrOCRProcessor, VisionEncoderDecoderModel

        _trocr_processor = TrOCRProcessor.from_pretrained(TROCR_MODEL_ID)
        _trocr_model = VisionEncoderDecoderModel.from_pretrained(TROCR_MODEL_ID)
        _trocr_model.eval()
        if torch.cuda.is_available():
            _trocr_model = _trocr_model.to("cuda")
    return _trocr_processor, _trocr_model


class TrOCRProvider(OCRProvider):
    def _extract_sync(self, file_path: Path) -> OCRResult:
        if file_path.suffix.lower() not in IMAGE_EXTENSIONS:
            return {
                "provider": "trocr",
                "execution_mode": EXECUTION_MODE,
                "text": "",
                "success": False,
                "error": f"Unsupported file type: {file_path.suffix}",
            }

        try:
            import torch
            from PIL import Image

            processor, model = _get_trocr_models()
            image = Image.open(file_path).convert("RGB")

            pixel_values = processor(images=image, return_tensors="pt").pixel_values
            if next(model.parameters()).is_cuda:
                pixel_values = pixel_values.to("cuda")

            with torch.no_grad():
                generated_ids = model.generate(pixel_values, max_new_tokens=512)

            text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            text = text.strip()

            return {
                "provider": "trocr",
                "execution_mode": EXECUTION_MODE,
                "text": text,
                "success": bool(text),
                "error": "" if text else "No text detected",
            }
        except Exception as exc:
            logger.exception("TrOCR failed for %s", file_path)
            return {
                "provider": "trocr",
                "execution_mode": EXECUTION_MODE,
                "text": "",
                "success": False,
                "error": str(exc),
            }

    async def extract_text(self, file_path: str | Path) -> OCRResult:
        path = Path(file_path)
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._extract_sync, path)


trocr_provider = TrOCRProvider()
