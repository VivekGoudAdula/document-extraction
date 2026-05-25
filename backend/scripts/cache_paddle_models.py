"""
Optional: pre-download PaddleOCR 2.x weights at build time.
"""
import os
import sys

os.environ["FLAGS_use_mkldnn"] = "0"

try:
    import numpy as np

    if not np.__version__.startswith("1."):
        print(f"WARN: numpy {np.__version__} may break paddle; want 1.x", file=sys.stderr)

    import paddleocr

    print(f"paddleocr version: {paddleocr.__version__}")
    if not paddleocr.__version__.startswith("2."):
        sys.exit(1)

    import cv2

    print(f"opencv: {cv2.__version__}")

    from paddleocr import PaddleOCR

    PaddleOCR(lang="en", use_angle_cls=False)
    print("PaddleOCR models cached.")
except Exception as exc:
    print(f"Model cache failed: {exc}", file=sys.stderr)
    sys.exit(1)
