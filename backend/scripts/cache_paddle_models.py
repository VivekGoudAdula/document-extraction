"""
Pre-download PaddleOCR 2.x det+rec weights during Render BUILD (~16MB).
Cached under backend/.paddleocr/ (HOME=backend dir) so runtime does not download.
"""
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["HOME"] = str(BACKEND_DIR)

PADDLE_HOME = BACKEND_DIR / ".paddleocr"


def main() -> None:
    import numpy as np

    assert np.__version__.startswith("1."), f"numpy must be 1.x, got {np.__version__}"

    import cv2

    print(f"HOME={os.environ['HOME']}")
    print(f"opencv: {cv2.__version__}")

    import paddleocr

    version = paddleocr.__version__
    print(f"paddleocr version: {version}")
    if not version.startswith("2."):
        print(f"FATAL: expected paddleocr 2.x, got {version}", file=sys.stderr)
        sys.exit(1)

    from paddleocr import PaddleOCR

    print("Downloading PaddleOCR det+rec models (build step)...")
    PaddleOCR(
        lang="en",
        use_angle_cls=False,
        show_log=False,
        det_limit_side_len=512,
        rec_batch_num=1,
        cpu_threads=2,
    )

    det = PADDLE_HOME / "whl" / "det" / "en" / "en_PP-OCRv3_det_infer"
    rec = PADDLE_HOME / "whl" / "rec" / "en" / "en_PP-OCRv4_rec_infer"
    if not det.is_dir() or not rec.is_dir():
        print(f"FATAL: missing cached models under {PADDLE_HOME}", file=sys.stderr)
        sys.exit(1)

    print(f"OK: det={det}")
    print(f"OK: rec={rec}")
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"FATAL model cache: {exc}", file=sys.stderr)
        sys.exit(1)
