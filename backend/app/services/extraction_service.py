"""
Document extraction orchestration.

Flow (confidential images stay on-server for OCR):
1. Save upload locally
2. OpenCV preprocess locally
3. Parallel local PaddleOCR + TrOCR
4. Fuse OCR outputs
5. GPT-4o semantic extraction (external API — only non-OCR step)
6. Persist to MongoDB
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import UploadFile

from app.providers.llm.openai_provider import get_openai_provider
from app.providers.mongodb_provider import mongodb_provider
from app.services.ocr_pipeline_service import ocr_pipeline_service
from app.utils.exceptions import DocumentExtractionError, OpenAIProviderError
from app.utils.file_utils import save_upload_file

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


class ExtractionService:
    async def process_extraction(
        self,
        *,
        upload_file: UploadFile,
        extraction_prompt: str,
    ) -> dict[str, Any]:
        file_path = await save_upload_file(upload_file)
        filename = file_path.name

        if file_path.suffix.lower() not in IMAGE_EXTENSIONS:
            raise DocumentExtractionError(
                "Only image uploads are supported (PNG, JPG, JPEG, WEBP)."
            )

        preprocessed_path = ocr_pipeline_service.prepare_for_ocr(file_path)

        fusion_context, paddle_result, trocr_result = (
            await ocr_pipeline_service.build_fusion_context(
                file_path,
                preprocessed_path=preprocessed_path,
            )
        )

        paddle_ok = paddle_result.get("success", False)
        trocr_ok = trocr_result.get("success", False)
        if not paddle_ok and not trocr_ok:
            raise DocumentExtractionError(
                "Local OCR produced no usable text. Check image quality and try again."
            )

        if not fusion_context.strip():
            raise DocumentExtractionError(
                "Local OCR produced no usable text. Check image quality and try again."
            )

        fallback_text = (
            paddle_result.get("text", "")
            or trocr_result.get("text", "")
            or ""
        )

        try:
            ai_response = await get_openai_provider().extract_hybrid_structured(
                fusion_context=fusion_context,
                user_prompt=extraction_prompt,
                image_path=file_path,
                fallback_document_text=fallback_text,
            )
        except OpenAIProviderError:
            raise
        except Exception as exc:
            raise OpenAIProviderError(f"Structured extraction failed: {exc}") from exc

        saved_record = await mongodb_provider.save_hybrid_extraction(
            filename=filename,
            original_prompt=extraction_prompt,
            paddleocr_output=dict(paddle_result),
            trocr_output=dict(trocr_result),
            fusion_context=fusion_context,
            final_ai_response=ai_response,
            extracted_text=fallback_text or fusion_context[:5000],
        )

        created_at = saved_record["created_at"]
        if isinstance(created_at, datetime):
            created_at = created_at.isoformat()

        return {
            "id": saved_record["id"],
            "filename": filename,
            "extracted_text": saved_record.get("extracted_text", ""),
            "user_prompt": extraction_prompt,
            "ai_response": ai_response,
            "created_at": created_at,
            "ocr_execution_mode": "local",
            "pipeline": {
                "preprocessing": preprocessed_path is not None,
                "paddleocr_success": paddle_ok,
                "trocr_success": trocr_ok,
                "fusion_applied": True,
                "vision_used": True,
                "ocr_execution_mode": "local",
            },
            "paddleocr_output": paddle_result,
            "trocr_output": trocr_result,
            "fusion_context": fusion_context,
        }


extraction_service = ExtractionService()
