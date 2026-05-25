#!/usr/bin/env bash
# Render build — run from backend/ as: bash render-build.sh
set -euo pipefail

export FLAGS_use_mkldnn=0

pip install --upgrade pip

echo "=== Remove conflicting packages ==="
pip uninstall -y paddleocr paddlex paddlepaddle opencv-python opencv-contrib-python 2>/dev/null || true

echo "=== Install Render stack ==="
pip install -r requirements-render.txt --no-cache-dir

echo "=== Single OpenCV (headless) ==="
pip uninstall -y opencv-python opencv-contrib-python 2>/dev/null || true
pip install opencv-python-headless==4.6.0.66 --no-cache-dir --force-reinstall

echo "=== Verify versions (pip only — no paddle import at build time) ==="
pip show paddleocr | grep -E '^Version:'
pip show paddlepaddle | grep -E '^Version:'
pip show numpy | grep -E '^Version:'
PADDLE_VER=$(pip show paddleocr | awk '/^Version:/{print $2}')
if [[ "${PADDLE_VER}" != 2.7.* ]]; then
  echo "FATAL: expected paddleocr 2.7.x, got ${PADDLE_VER}"
  exit 1
fi
NUMPY_VER=$(python -c "import numpy; print(numpy.__version__)")
echo "numpy ${NUMPY_VER}"
python -c "import numpy; v=numpy.__version__; assert v.startswith('1.'), f'numpy must be 1.x for paddle, got {v}'"

echo "=== Optional model cache (non-fatal) ==="
python scripts/cache_paddle_models.py || echo "WARN: model pre-cache skipped"

echo "=== Build OK ==="
