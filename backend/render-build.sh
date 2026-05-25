#!/usr/bin/env bash
# Render: Root Directory = backend, Build Command = bash render-build.sh
set -euo pipefail

export FLAGS_use_mkldnn=0
ROOT="$(cd "$(dirname "$0")" && pwd)"
CONSTRAINTS="${ROOT}/constraints-render.txt"

pip install --upgrade pip

echo "=== Clean conflicting packages ==="
pip uninstall -y paddleocr paddlex paddlepaddle \
  opencv-python opencv-contrib-python opencv-python-headless 2>/dev/null || true

echo "=== Pin NumPy 1.x first (required by PaddlePaddle) ==="
pip install "numpy>=1.24.0,<2.0.0" --no-cache-dir

echo "=== Install app deps (constraints keep NumPy 1.x) ==="
pip install -r "${ROOT}/requirements-render.txt" -c "${CONSTRAINTS}" --no-cache-dir

echo "=== Drop GUI OpenCV wheels; keep headless only ==="
pip uninstall -y opencv-python opencv-contrib-python 2>/dev/null || true

echo "=== Install headless OpenCV WITHOUT deps (never upgrade NumPy) ==="
pip install opencv-python-headless==4.6.0.66 --no-deps --no-cache-dir --force-reinstall

echo "=== Force NumPy 1.x again if anything pulled 2.x ==="
pip install "numpy>=1.24.0,<2.0.0" --no-cache-dir --force-reinstall

echo "=== Verify (build fails on mismatch) ==="
python <<'PY'
import numpy
import cv2
import paddleocr

assert numpy.__version__.startswith("1."), f"numpy must be 1.x, got {numpy.__version__}"
assert paddleocr.__version__.startswith("2.7."), paddleocr.__version__
print("numpy", numpy.__version__)
print("cv2", cv2.__version__)
print("paddleocr", paddleocr.__version__)
PY

echo "=== Pre-download PaddleOCR models into backend/.paddleocr (required) ==="
export HOME="${ROOT}"
python "${ROOT}/scripts/cache_paddle_models.py"
test -d "${ROOT}/.paddleocr/whl/det/en/en_PP-OCRv3_det_infer"
test -d "${ROOT}/.paddleocr/whl/rec/en/en_PP-OCRv4_rec_infer"
du -sh "${ROOT}/.paddleocr"

echo "=== Build OK ==="
