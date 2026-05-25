"""
Local OpenCV image preprocessing for OCR.

SECURITY: All operations run on the backend server. Processed images are saved
to a local temp directory only — never uploaded to external services.
"""

import uuid
from pathlib import Path

import cv2
import numpy as np

from app.config import UPLOADS_DIR
PREPROCESSED_DIR = UPLOADS_DIR / "preprocessed"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


class PreprocessingService:
    def preprocess_image(self, image_path: str | Path) -> Path:
        """
        OpenCV pipeline: grayscale, denoise, contrast, adaptive threshold,
        sharpen, resize for OCR.
        """
        source = Path(image_path)
        if source.suffix.lower() not in IMAGE_EXTENSIONS:
            raise ValueError(f"Not an image file: {source}")

        PREPROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        output_path = PREPROCESSED_DIR / f"{source.stem}_{uuid.uuid4().hex}_enhanced.png"

        image = cv2.imread(str(source))
        if image is None:
            raise ValueError(f"Unable to read image: {source}")

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
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

        height, width = sharpened.shape[:2]
        max_dim = 2400
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
