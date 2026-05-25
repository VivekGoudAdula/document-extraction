import logging

from fastapi import APIRouter, File, Form, UploadFile

from app.services.extraction_service import extraction_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["extract"])


@router.post("/extract")
async def extract_document(
    file: UploadFile = File(...),
    extraction_prompt: str = Form(...),
):
    logger.info("POST /extract received: %s", file.filename)
    """
    Upload an image, run local OCR (PaddleOCR + TrOCR on-server), extract with
    GPT-4o, persist in MongoDB, and return structured JSON.

    OCR never leaves infrastructure; only semantic extraction uses OpenAI.
    """
    return await extraction_service.process_extraction(
        upload_file=file,
        extraction_prompt=extraction_prompt,
    )
