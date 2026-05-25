#!/usr/bin/env bash
# Render build — run from backend/ as: bash render-build.sh
set -euo pipefail

export FLAGS_use_mkldnn=0

pip install --upgrade pip

echo "=== Remove PaddleOCR 3.x / duplicate OpenCV if present ==="
pip uninstall -y paddleocr paddlex paddlepaddle opencv-python opencv-contrib-python 2>/dev/null || true

echo "=== Install Render stack (PaddleOCR 2.7.3) ==="
pip install -r requirements-render.txt --no-cache-dir

echo "=== Keep only one OpenCV (headless) ==="
pip uninstall -y opencv-python opencv-contrib-python 2>/dev/null || true
pip install opencv-python-headless==4.6.0.66 --no-cache-dir

echo "=== Verify paddleocr version ==="
python -c "
import paddleocr
v = paddleocr.__version__
print('paddleocr version:', v)
assert v.startswith('2.'), f'Expected 2.x, got {v}'
"

echo "=== Optional model cache (non-fatal — segfault on some hosts) ==="
if python scripts/cache_paddle_models.py; then
  echo "OCR models pre-cached at build time."
else
  echo "WARN: Model pre-cache skipped; models load on first /extract request."
fi

echo "=== Build OK ==="
