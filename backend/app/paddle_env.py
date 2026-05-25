"""
PaddleOCR cache location — must run before any paddleocr import.

On Render, store models under the backend directory (baked into the deploy image),
not only under /opt/render (which may differ between build and runtime).
"""

import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent


def configure_paddle_home() -> Path:
    if os.getenv("PADDLE_HOME"):
        return Path(os.environ["PADDLE_HOME"])

    use_app_dir = os.getenv("OCR_LOW_MEMORY", "").lower() in ("true", "1", "yes") or os.getenv(
        "RENDER", ""
    ).lower() in ("true", "1", "yes")

    if use_app_dir:
        os.environ["HOME"] = str(BACKEND_DIR)

    return Path(os.environ.get("HOME", str(BACKEND_DIR)))


def paddle_cache_root() -> Path:
    return configure_paddle_home() / ".paddleocr" / "whl"


def cached_det_rec_dirs() -> tuple[str | None, str | None]:
    """Return det/rec model dirs when present from build-time cache."""
    root = paddle_cache_root()
    det = root / "det" / "en" / "en_PP-OCRv3_det_infer"
    rec = root / "rec" / "en" / "en_PP-OCRv4_rec_infer"
    if det.is_dir() and rec.is_dir():
        return str(det), str(rec)
    return None, None


configure_paddle_home()
