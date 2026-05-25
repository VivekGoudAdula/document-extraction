import json
import re
from typing import Any

from app.utils.exceptions import OpenAIProviderError


def parse_openai_json_response(raw_content: str) -> dict[str, Any] | list[Any]:
    """Safely parse JSON from an OpenAI response, stripping markdown fences if present."""
    if not raw_content or not raw_content.strip():
        raise OpenAIProviderError("OpenAI returned an empty response.")

    content = raw_content.strip()

    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", content, re.IGNORECASE)
    if fence_match:
        content = fence_match.group(1).strip()

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise OpenAIProviderError(
            f"OpenAI response is not valid JSON: {exc.msg}"
        ) from exc

    if not isinstance(parsed, (dict, list)):
        raise OpenAIProviderError("OpenAI response must be a JSON object or array.")

    return parsed


def _plain_text_to_result(text: str) -> dict[str, Any]:
    return {"answer": text.strip()}


def parse_model_output(
    raw_content: str,
    *,
    expect_json: bool = True,
) -> dict[str, Any]:
    """
    Parse LLM output. When expect_json is False, accept plain-text answers
    (used for Azure bypass calls without response_format json_object).
    """
    if not raw_content or not raw_content.strip():
        raise OpenAIProviderError("OpenAI returned an empty response.")

    content = raw_content.strip()

    if content.startswith(("{", "[")):
        try:
            parsed = parse_openai_json_response(content)
            if isinstance(parsed, dict):
                return parsed
            return {"items": parsed}
        except OpenAIProviderError:
            pass

    if expect_json:
        try:
            parsed = parse_openai_json_response(content)
            if isinstance(parsed, dict):
                return parsed
            return {"items": parsed}
        except OpenAIProviderError:
            pass

    return _plain_text_to_result(content)
