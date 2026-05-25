from typing import Any, TypedDict


class OCRResult(TypedDict, total=False):
    provider: str
    execution_mode: str
    text: str
    content: str
    tables: list[dict[str, Any]]
    key_values: list[dict[str, Any]]
    confidence: list[dict[str, Any]]
    paragraphs: list[str]
    success: bool
    error: str
