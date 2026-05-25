"""
Abstract LLM provider interface.

OCR runs fully locally (PaddleOCR + TrOCR). Semantic extraction may use an
external API today (OpenAI GPT-4o) or a self-hosted model later (Llama, Qwen,
Mistral, Gemma) by implementing LLMProvider.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class LLMProvider(ABC):
    @abstractmethod
    async def extract_structured(
        self,
        *,
        fusion_context: str,
        user_prompt: str,
        image_path: Path | None = None,
        fallback_document_text: str = "",
    ) -> dict[str, Any] | list[Any]:
        """Return structured JSON from OCR fusion context and user instructions."""
        pass
