"""
OpenAI GPT-4o semantic extraction provider.

SECURITY BOUNDARY:
- OCR (PaddleOCR + TrOCR) runs fully locally on this server.
- Uploaded images are NOT sent to any external OCR API.
- Only this layer may call an external API (OpenAI/Azure OpenAI) for structured
  JSON extraction from fused local OCR text (+ optional vision on the image).

Future: replace OpenAIProvider with a local LLMProvider (Llama, Qwen, Mistral).
"""

from pathlib import Path
from typing import Any

from openai import APIStatusError, AsyncAzureOpenAI, AsyncOpenAI, RateLimitError

from app.config import get_settings
from app.utils.exceptions import OpenAIProviderError
from app.utils.image_encoding import encode_image_base64
from app.utils.json_parser import parse_openai_json_response

MAX_CONTEXT_CHARS = 24_000

HYBRID_EXTRACTION_PROMPT = """You are an enterprise-grade intelligent document extraction engine.

OCR was performed locally using:
- PaddleOCR (layout, forms, printed text)
- TrOCR (handwriting, difficult regions)

Your task:
- understand semantic meaning
- correct OCR mistakes using context and the image when provided
- extract structured information
- preserve layout meaning

Prefer TrOCR lines for handwriting; prefer PaddleOCR for tables, forms, and layout.

Return ONLY valid JSON.

User Request:
{user_prompt}

OCR CONTEXT:
{combined_context}

Requirements:
- never hallucinate
- never explain
- clean JSON only"""


def _truncate(text: str) -> str:
    text = text.strip()
    if len(text) > MAX_CONTEXT_CHARS:
        return text[:MAX_CONTEXT_CHARS] + "\n[Truncated.]"
    return text


def _format_openai_error(exc: RateLimitError | APIStatusError) -> str:
    status = getattr(exc, "status_code", None)
    body = getattr(exc, "body", None) or {}
    if isinstance(body, dict):
        err = body.get("error") or {}
        message = err.get("message")
        code = err.get("code") or err.get("type")

        if status == 401 or code == "invalid_api_key":
            settings = get_settings()
            if settings.use_azure_openai:
                return (
                    "Azure OpenAI rejected the API key. Check OPENAI_API_KEY, "
                    "OPENAI_ENDPOINT, and OPENAI_GPT_DEPLOYMENT in backend/.env."
                )
            return (
                "OpenAI.com rejected the API key. Use a key from "
                "https://platform.openai.com/api-keys and leave OPENAI_ENDPOINT unset."
            )

        if code == "insufficient_quota":
            return "API quota exceeded. Check Azure deployment quota or OpenAI billing."

        if message:
            return f"OpenAI API error: {message}"

    return f"OpenAI API error ({status or 'unknown'}): {exc}"


class OpenAIProvider:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.openai_api_key.strip():
            raise OpenAIProviderError(
                "OPENAI_API_KEY is not set. Add it in Render → Environment."
            )
        self._use_azure = settings.use_azure_openai

        if self._use_azure:
            self._client = AsyncAzureOpenAI(
                azure_endpoint=settings.azure_endpoint,
                api_key=settings.openai_api_key,
                api_version=settings.openai_api_version,
            )
        else:
            self._client = AsyncOpenAI(api_key=settings.openai_api_key)

        try:
            self._model = settings.chat_model
        except ValueError as exc:
            raise OpenAIProviderError(str(exc)) from exc

    async def _complete(self, messages: list[dict[str, Any]]) -> str:
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=0.1,
                response_format={"type": "json_object"},
            )
        except RateLimitError as exc:
            raise OpenAIProviderError(_format_openai_error(exc)) from exc
        except APIStatusError as exc:
            raise OpenAIProviderError(_format_openai_error(exc)) from exc

        raw = response.choices[0].message.content
        if raw is None:
            raise OpenAIProviderError("OpenAI returned no content.")
        return raw

    def _build_hybrid_messages(
        self,
        *,
        fusion_context: str,
        user_prompt: str,
        image_path: Path | None,
    ) -> list[dict[str, Any]]:
        prompt_text = HYBRID_EXTRACTION_PROMPT.format(
            user_prompt=user_prompt.strip(),
            combined_context=_truncate(fusion_context),
        )

        if image_path:
            encoded = encode_image_base64(image_path)
            if encoded:
                b64_data, media_type = encoded
                return [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt_text},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{media_type};base64,{b64_data}"
                                },
                            },
                        ],
                    }
                ]

        return [{"role": "user", "content": prompt_text}]

    async def extract_hybrid_structured(
        self,
        *,
        fusion_context: str,
        user_prompt: str,
        image_path: Path | None = None,
        fallback_document_text: str = "",
    ) -> dict[str, Any] | list[Any]:
        if not fusion_context.strip() and not fallback_document_text.strip():
            raise OpenAIProviderError("No OCR context available for extraction.")
        if not user_prompt.strip():
            raise OpenAIProviderError("Extraction prompt cannot be empty.")

        context = fusion_context.strip() or fallback_document_text
        messages = self._build_hybrid_messages(
            fusion_context=context,
            user_prompt=user_prompt,
            image_path=image_path,
        )

        try:
            raw = await self._complete(messages)
            return parse_openai_json_response(raw)
        except OpenAIProviderError:
            raise
        except Exception as exc:
            raise OpenAIProviderError(f"OpenAI request failed: {exc}") from exc


_provider: OpenAIProvider | None = None


def get_openai_provider() -> OpenAIProvider:
    global _provider
    if _provider is None:
        _provider = OpenAIProvider()
    return _provider


def reset_openai_provider() -> None:
    global _provider
    _provider = None
