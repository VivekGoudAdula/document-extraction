"""
Hybrid local OCR pipeline — parallel PaddleOCR + TrOCR with cross-provider fallback.

SECURITY: All OCR inference runs on this server. Images are preprocessed with
OpenCV locally, then passed to local models. No external OCR HTTP calls.
"""

import asyncio
import logging
from pathlib import Path

from app.models.ocr_models import OCRResult
from app.providers.ocr.paddle_provider import paddle_provider
from app.providers.ocr.trocr_provider import trocr_provider
from app.services.fusion_service import fusion_service
from app.services.preprocessing_service import preprocessing_service

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
EXECUTION_MODE = "local"


def _empty_result(provider: str, error: str) -> OCRResult:
    return {
        "provider": provider,
        "execution_mode": EXECUTION_MODE,
        "text": "",
        "confidence": [],
        "success": False,
        "error": error,
    }


def _apply_cross_fallback(
    paddle_result: OCRResult,
    trocr_result: OCRResult,
) -> tuple[OCRResult, OCRResult]:
    """
    If one local engine fails, rely on the other (no cloud OCR).
    """
    paddle_ok = paddle_result.get("success", False)
    trocr_ok = trocr_result.get("success", False)

    if not paddle_ok and trocr_ok:
        logger.info("PaddleOCR failed — using TrOCR output as primary layout source")
        paddle_result = {
            **paddle_result,
            "text": trocr_result.get("text", ""),
            "success": True,
            "fallback_from": "trocr",
            "error": "",
        }
    elif not trocr_ok and paddle_ok:
        logger.info("TrOCR failed — using PaddleOCR output for handwriting regions")
        trocr_result = {
            **trocr_result,
            "text": paddle_result.get("text", ""),
            "success": True,
            "fallback_from": "paddleocr",
            "error": "",
        }

    return paddle_result, trocr_result


class OCRPipelineService:
    async def run_parallel_ocr(
        self,
        file_path: Path,
        *,
        preprocessed_path: Path | None = None,
    ) -> tuple[OCRResult, OCRResult]:
        ocr_path = preprocessed_path or file_path

        results = await asyncio.gather(
            paddle_provider.extract_text(ocr_path),
            trocr_provider.extract_text(ocr_path),
            return_exceptions=True,
        )

        paddle_result = (
            results[0]
            if isinstance(results[0], dict)
            else _empty_result("paddleocr", str(results[0]))
        )
        trocr_result = (
            results[1]
            if isinstance(results[1], dict)
            else _empty_result("trocr", str(results[1]))
        )

        paddle_ok = paddle_result.get("success", False)
        trocr_ok = trocr_result.get("success", False)

        if (not paddle_ok or not trocr_ok) and preprocessed_path and preprocessed_path != file_path:
            logger.info("Retrying failed OCR on original image: %s", file_path.name)
            retry_tasks = []
            retry_labels: list[str] = []
            if not paddle_ok:
                retry_tasks.append(paddle_provider.extract_text(file_path))
                retry_labels.append("paddle")
            if not trocr_ok:
                retry_tasks.append(trocr_provider.extract_text(file_path))
                retry_labels.append("trocr")

            retry_results = await asyncio.gather(*retry_tasks, return_exceptions=True)
            for label, retry in zip(retry_labels, retry_results):
                if not isinstance(retry, dict):
                    continue
                if label == "paddle" and retry.get("success"):
                    paddle_result = retry
                elif label == "trocr" and retry.get("success"):
                    trocr_result = retry

        return _apply_cross_fallback(paddle_result, trocr_result)

    async def build_fusion_context(
        self,
        file_path: Path,
        *,
        preprocessed_path: Path | None = None,
    ) -> tuple[str, OCRResult, OCRResult]:
        paddle_result, trocr_result = await self.run_parallel_ocr(
            file_path,
            preprocessed_path=preprocessed_path,
        )
        fusion_context = fusion_service.build_combined_context(
            paddle_result,
            trocr_result,
        )
        return fusion_context, paddle_result, trocr_result

    def prepare_for_ocr(self, file_path: Path) -> Path | None:
        if file_path.suffix.lower() in IMAGE_EXTENSIONS:
            return preprocessing_service.preprocess_image(file_path)
        return None


ocr_pipeline_service = OCRPipelineService()
