"""
Run during Render BUILD (not runtime) to download PaddleOCR 2.x weights once.
Models are baked into the deploy image so /extract does not download on first request.
"""
import os

os.environ.setdefault("FLAGS_use_mkldnn", "0")

import paddleocr
from paddleocr import PaddleOCR

print(f"paddleocr version: {paddleocr.__version__}")

if paddleocr.__version__.startswith("3."):
    raise SystemExit(
        "ERROR: PaddleOCR 3.x detected. Render build must use requirements-render.txt "
        "(paddleocr==2.7.3), not requirements.txt."
    )

ocr = PaddleOCR(lang="en", use_angle_cls=False)
print("PaddleOCR 2.x models cached for deploy.")
