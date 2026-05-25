"""
Pre-download PaddleOCR 2.x weights during Render BUILD (~16MB total).
Without this, the first /extract downloads models from the internet (2–5+ minutes).
"""
import os
import sys
from pathlib import Path

os.environ["FLAGS_use_mkldnn"] = "0"
# Render build/runtime home — models baked into the deploy image
os.environ.setdefault("HOME", "/opt/render")
PADDLE_HOME = Path(os.environ["HOME"]) / ".paddleocr"


def main() -> None:
    import numpy as np

    assert np.__version__.startswith("1."), f"numpy must be 1.x, got {np.__version__}"

    import cv2

    print(f"opencv: {cv2.__version__}")

    import paddleocr

    version = paddleocr.__version__
    print(f"paddleocr version: {version}")
    if not version.startswith("2."):
        print(f"FATAL: expected paddleocr 2.x, got {version}", file=sys.stderr)
        sys.exit(1)

    from paddleocr import PaddleOCR

    print("Downloading PaddleOCR models (one-time at build)...")
    PaddleOCR(
        lang="en",
        use_angle_cls=False,
        show_log=False,
        det_limit_side_len=640,
        rec_batch_num=1,
    )
    print(f"PaddleOCR models cached under {PADDLE_HOME}")
    if not PADDLE_HOME.exists():
        sys.exit("PaddleOCR cache directory missing after init")
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"FATAL model cache: {exc}", file=sys.stderr)
        sys.exit(1)
