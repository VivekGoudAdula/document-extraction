import uuid
from pathlib import Path

import aiofiles
from fastapi import UploadFile

from app.config import ALLOWED_EXTENSIONS, UPLOADS_DIR
from app.utils.exceptions import InvalidFileTypeError


def validate_upload_file(filename: str | None, content_type: str | None) -> str:
    if not filename:
        raise InvalidFileTypeError("Filename is required.")

    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise InvalidFileTypeError(
            f"File extension '{extension}' is not allowed. "
            f"Allowed extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}."
        )

    return extension


def generate_unique_filename(original_filename: str) -> str:
    extension = Path(original_filename).suffix.lower()
    stem = Path(original_filename).stem[:80] or "document"
    return f"{stem}_{uuid.uuid4().hex}{extension}"


async def save_upload_file(upload_file: UploadFile, destination_name: str | None = None) -> Path:
    validate_upload_file(upload_file.filename, upload_file.content_type)

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

    stored_name = destination_name or generate_unique_filename(upload_file.filename)
    file_path = UPLOADS_DIR / stored_name

    async with aiofiles.open(file_path, "wb") as out_file:
        while chunk := await upload_file.read(1024 * 1024):
            await out_file.write(chunk)

    await upload_file.seek(0)
    return file_path
