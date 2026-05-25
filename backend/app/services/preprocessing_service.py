"""
Local OpenCV image preprocessing for OCR.

SECURITY: All operations run on the backend server. Processed images are saved
to a local temp directory only — never uploaded to external services.
"""

import logging
import uuid
from pathlib import Path

from app.config import UPLOADS_DIR

logger = logging.getLogger(__name__)

PREPROCESSED_DIR = UPLOADS_DIR / "preprocessed"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def _import_cv2():
    try:
        import cv2
        import numpy as np

        return cv2, np
    except ImportError as exc:
        raise ImportError(
            "OpenCV (cv2) is not installed. Render build must run bash render-build.sh "
            "and verify 'import cv2' succeeds."
        ) from exc


class PreprocessingService:
    def preprocess_image(self, image_path: str | Path) -> Path:
        """
        OpenCV pipeline: grayscale, denoise, contrast, adaptive threshold,
        sharpen, resize for OCR. Falls back to original image if cv2 is missing.
        """
        from app.config import get_settings

        source = Path(image_path)
        if source.suffix.lower() not in IMAGE_EXTENSIONS:
            raise ValueError(f"Not an image file: {source}")

        try:
            cv2, np = _import_cv2()
        except ImportError as exc:
            logger.warning("OpenCV unavailable, using original image: %s", exc)
            return source

        low_memory = get_settings().is_low_memory_deploy

        PREPROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        output_path = PREPROCESSED_DIR / f"{source.stem}_{uuid.uuid4().hex}_enhanced.png"

        image = cv2.imread(str(source))
        if image is None:
            raise ValueError(f"Unable to read image: {source}")

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        if low_memory:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            sharpened = clahe.apply(gray)
            max_dim = 1600
        else:
            denoised = cv2.fastNlMeansDenoising(gray, h=10)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            contrast = clahe.apply(denoised)
            adaptive = cv2.adaptiveThreshold(
                contrast,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                31,
                8,
            )
            sharpen_kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
            sharpened = cv2.filter2D(adaptive, -1, sharpen_kernel)
            max_dim = 2400

        height, width = sharpened.shape[:2]
        scale = min(1.0, max_dim / max(height, width))
        if scale < 1.0:
            sharpened = cv2.resize(
                sharpened,
                (int(width * scale), int(height * scale)),
                interpolation=cv2.INTER_CUBIC,
            )

        cv2.imwrite(str(output_path), sharpened)
        return output_path

    def resolve_ocr_image_path(self, file_path: Path) -> Path:
        """Return preprocessed path for images; original path otherwise."""
        if file_path.suffix.lower() in IMAGE_EXTENSIONS:
            return self.preprocess_image(file_path)
        return file_path


preprocessing_service = PreprocessingService()
