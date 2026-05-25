import base64
from pathlib import Path

IMAGE_MEDIA_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


def encode_image_base64(file_path: Path) -> tuple[str, str] | None:
    """Return (base64_data, media_type) for vision models."""
    suffix = file_path.suffix.lower()
    media_type = IMAGE_MEDIA_TYPES.get(suffix)
    if not media_type:
        return None

    data = base64.b64encode(file_path.read_bytes()).decode("utf-8")
    return data, media_type
