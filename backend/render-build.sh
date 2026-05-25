#!/usr/bin/env bash
# Render build — run from backend/ as: bash render-build.sh
set -euo pipefail

export FLAGS_use_mkldnn=0
CONSTRAINTS="$(cd "$(dirname "$0")" && pwd)/constraints-render.txt"

pip install --upgrade pip

echo "=== Clean old Paddle / OpenCV wheels ==="
pip uninstall -y paddleocr paddlex paddlepaddle \
  opencv-python opencv-contrib-python opencv-python-headless 2>/dev/null || true

echo "=== Install with NumPy 1.x constraints ==="
pip install -r requirements-render.txt -c "${CONSTRAINTS}" --no-cache-dir

echo "=== Remove duplicate OpenCV (keep headless only) ==="
pip uninstall -y opencv-python opencv-contrib-python 2>/dev/null || true

echo "=== Re-pin NumPy 1.x ==="
pip install "numpy>=1.24.0,<2.0.0" --no-cache-dir --force-reinstall

echo "=== Restore OpenCV headless (cv2) without upgrading NumPy ==="
pip install opencv-python-headless==4.6.0.66 --no-deps --no-cache-dir --force-reinstall

echo "=== Verify ==="
pip show paddleocr | grep -E '^Version:'
pip show numpy | grep -E '^Version:'
PADDLE_VER=$(pip show paddleocr | awk '/^Version:/{print $2}')
[[ "${PADDLE_VER}" == 2.7.* ]] || { echo "FATAL: bad paddleocr ${PADDLE_VER}"; exit 1; }
python -c "import numpy; v=numpy.__version__; print('numpy', v); assert v.startswith('1.'), v"
python -c "import cv2; print('cv2', cv2.__version__)"

echo "=== Optional model cache (non-fatal) ==="
python scripts/cache_paddle_models.py || echo "WARN: model pre-cache skipped"

echo "=== Build OK ==="
