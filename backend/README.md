# Secure Local-OCR Document Extraction API

Pipeline: **OpenCV (local) → parallel PaddleOCR + TrOCR (local) → fusion → GPT-4o → MongoDB**

## Security model

- **OCR**: Runs entirely on this server. Uploaded images are never sent to third-party OCR APIs.
- **LLM**: Only GPT-4o semantic extraction may call OpenAI/Azure OpenAI (configurable later to a local LLM).
- See [SECURITY.md](../SECURITY.md) for the full confidentiality boundary.

## Architecture

```
Frontend → FastAPI → OpenCV (local) → PaddleOCR + TrOCR (local, parallel) → Fusion → GPT-4o → MongoDB
```

## Requirements

- Python 3.10+
- MongoDB
- OpenAI API key (GPT-4o) for semantic extraction only
- Optional: NVIDIA GPU for faster TrOCR

## Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

Copy `.env.example` to `.env`:

```
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4o
# Or Azure OpenAI — see .env.example

MONGO_URI=mongodb://localhost:27017
```

First startup downloads TrOCR and PaddleOCR weights locally (one-time). OCR models are warmed at server start.

Run (from `backend/`):

```powershell
.\run_dev.ps1
```

Or:

```powershell
uvicorn app.main:app --reload --reload-dir app --reload-exclude "venv/*" --host 0.0.0.0 --port 8000
```

## API

- `POST /extract` — multipart: `file` (image), `extraction_prompt`
- `GET /health` — includes `ocr_execution_mode: "local"`

## Supported uploads

PNG, JPG, JPEG, WEBP (scans, forms, screenshots, handwriting, slides).

## Provider layout

```
app/providers/ocr/   — base, paddle_provider, trocr_provider, model_loader
app/providers/llm/   — base (future local LLMs), openai_provider
app/services/        — preprocessing, fusion, extraction, ocr_pipeline
```

## Deploy on Render

1. **Root Directory:** `backend`
2. **Python version:** `3.11.11` (set in Dashboard → Environment → `PYTHON_VERSION`, or use `runtime.txt` in this folder)
3. **Build (512MB Render) — required, NOT requirements.txt:**
   ```bash
   pip install --upgrade pip && pip install -r requirements-render.txt && python scripts/cache_paddle_models.py
   ```
   If logs show `PP-OCRv5_server_det` or `UVDoc`, you are on PaddleOCR 3.x (wrong file) — fix the build command.
4. **Build (local / GPU server):** `pip install -r requirements.txt`
5. **Start:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. **Required env vars on Render:**
   - `MONGO_URI` — **MongoDB Atlas** connection string (`mongodb+srv://...`). `localhost` will not work on Render.
   - `OPENAI_API_KEY` — OpenAI or Azure key
   - `CORS_ORIGINS` — your Vercel frontend URL (e.g. `https://your-app.vercel.app`)

7. In Atlas: Network Access → allow `0.0.0.0/0` (or Render outbound IPs) so Render can connect.
8. **Memory:** Free Render (512MB) cannot load TrOCR + Paddle server models. Use `requirements-render.txt` + `OCR_LOW_MEMORY=true` (Paddle mobile only). Upgrade to **Starter 2GB+** for full Paddle+TrOCR.

Do **not** use Python 3.14 — PaddlePaddle has no wheels for it.

## Not used (by design)

Azure OCR, Google Vision, AWS Textract, HuggingFace Inference API.
