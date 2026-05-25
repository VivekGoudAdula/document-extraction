"""
Run during Render BUILD to download PaddleOCR 2.x weights once into the image.
"""
import os
import sys

os.environ.setdefault("FLAGS_use_mkldnn", "0")

import paddleocr

version = paddleocr.__version__
print(f"paddleocr version: {version}")

if not version.startswith("2."):
    print(
        "FATAL: PaddleOCR 3.x is installed. Render build must use requirements-render.txt "
        "and render-build.sh — NOT requirements.txt.",
        file=sys.stderr,
    )
    sys.exit(1)

from paddleocr import PaddleOCR

PaddleOCR(lang="en", use_angle_cls=False)
print("PaddleOCR 2.x models cached successfully.")
