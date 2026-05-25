#!/usr/bin/env bash
# Render: Root Directory = backend, Build Command = bash render-build.sh
set -euo pipefail

export FLAGS_use_mkldnn=0
ROOT="$(cd "$(dirname "$0")" && pwd)"
CONSTRAINTS="${ROOT}/constraints-render.txt"

pip install --upgrade pip

echo "=== Clean conflicting packages ==="
pip uninstall -y paddleocr paddlex paddlepaddle \
  opencv-python opencv-contrib-python 2>/dev/null || true

echo "=== Install app dependencies (NumPy 1.x constrained) ==="
pip install -r "${ROOT}/requirements-render.txt" -c "${CONSTRAINTS}" --no-cache-dir

echo "=== Ensure single OpenCV headless + NumPy 1.x ==="
pip uninstall -y opencv-python opencv-contrib-python 2>/dev/null || true
pip install "numpy>=1.24.0,<2.0.0" --no-cache-dir --force-reinstall
pip install opencv-python-headless==4.6.0.66 --no-cache-dir --force-reinstall

echo "=== Verify (build fails if cv2 missing) ==="
python -c "import numpy; assert numpy.__version__.startswith('1.'), numpy.__version__"
python -c "import cv2; print('cv2 OK', cv2.__version__)"
python -c "import paddleocr; v=paddleocr.__version__; print('paddleocr', v); assert v.startswith('2.7.')"

echo "=== Optional model cache ==="
python "${ROOT}/scripts/cache_paddle_models.py" || echo "WARN: model pre-cache skipped"

echo "=== Build OK ==="
