"""
Optional: pre-download PaddleOCR 2.x weights at build time.
Exit 0 on success, 1 on failure (render-build.sh treats failure as non-fatal).
"""
import os
import sys

os.environ["FLAGS_use_mkldnn"] = "0"

try:
    import paddleocr

    version = paddleocr.__version__
    print(f"paddleocr version: {version}")

    if not version.startswith("2."):
        print(f"ERROR: expected paddleocr 2.x, got {version}", file=sys.stderr)
        sys.exit(1)

    # Ensure headless cv2 only
    import cv2

    print(f"opencv: {cv2.__version__}")

    from paddleocr import PaddleOCR

    PaddleOCR(lang="en", use_angle_cls=False)
    print("PaddleOCR 2.x models cached successfully.")
except Exception as exc:
    print(f"Model cache failed: {exc}", file=sys.stderr)
    sys.exit(1)
