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

## Not used (by design)

Azure OCR, Google Vision, AWS Textract, HuggingFace Inference API.
