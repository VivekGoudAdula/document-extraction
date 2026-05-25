# Security & Data Confidentiality

## OCR — fully local

| Requirement | Implementation |
|-------------|----------------|
| Images stay on infrastructure | Saved under `backend/uploads/`; preprocessed copies under `backend/uploads/preprocessed/` |
| No external OCR APIs | Azure Document Intelligence, Google Vision, AWS Textract, and HuggingFace **Inference API** are **not** used |
| Local inference | **PaddleOCR** and **TrOCR** (`microsoft/trocr-base-handwritten`) run on the FastAPI server |
| Model download | HuggingFace `from_pretrained` and PaddleOCR init download weights **once** to local cache; thereafter inference is offline-capable |
| Parallel execution | `asyncio.gather` runs both engines locally in parallel |
| Startup cache | Models warm up once in application lifespan (not per request) |

## Semantic extraction — external (current)

| Component | Network |
|-----------|---------|
| GPT-4o structured extraction | OpenAI.com or **Azure OpenAI** (your deployment) |
| Optional vision | Original image may be sent as base64 to GPT-4o for correction — **not** to any OCR vendor |

To keep images entirely off third parties, disable vision in `OpenAIProvider._build_hybrid_messages` (text-only mode using fusion context).

## Future — local LLM

`app/providers/llm/base.py` defines `LLMProvider` so OpenAI can be swapped for self-hosted Llama, Qwen, Mistral, or Gemma without changing the OCR pipeline.

## MongoDB record

Each extraction stores `ocr_execution_mode: "local"` plus raw `paddleocr_output`, `trocr_output`, and `fusion_context`.

## What we do not use

- Azure Document Intelligence (OCR)
- Google Cloud Vision OCR
- AWS Textract
- HuggingFace hosted inference endpoints
- Any HTTP OCR microservice for document text
