#!/usr/bin/env bash
# Render build script — MUST use this instead of requirements.txt
set -euo pipefail
pip install --upgrade pip
pip install -r requirements-render.txt
python scripts/cache_paddle_models.py
