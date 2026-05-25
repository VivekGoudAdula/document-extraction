from typing import Any

from fastapi import UploadFile

from app.utils.file_utils import save_upload_file


class UploadService:
    async def save_file(self, upload_file: UploadFile) -> dict[str, Any]:
        file_path = await save_upload_file(upload_file)
        return {
            "filename": file_path.name,
            "path": str(file_path),
            "message": "File uploaded successfully.",
        }


upload_service = UploadService()
