from fastapi import APIRouter, File, UploadFile

from app.services.upload_service import upload_service

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("")
async def upload_file(file: UploadFile = File(...)):
    """Accept PDF, PNG, JPG, JPEG and save locally in /uploads."""
    return await upload_service.save_file(file)
