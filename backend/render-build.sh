#!/usr/bin/env bash
# Render MUST use this script (or equivalent). Do NOT use requirements.txt on 512MB plans.
set -euo pipefail

pip install --upgrade pip

echo "Removing PaddleOCR 3.x if present..."
pip uninstall -y paddleocr paddlex paddlepaddle 2>/dev/null || true

echo "Installing PaddleOCR 2.7.3 + PaddlePaddle 2.6.2..."
pip install -r requirements-render.txt --no-cache-dir

python scripts/cache_paddle_models.py

python -c "import paddleocr; print('Installed paddleocr', paddleocr.__version__)"
test "$(python -c 'import paddleocr; print(paddleocr.__version__)')" = "2.7.3" || {
  echo "FATAL: expected paddleocr 2.7.3"
  exit 1
}
