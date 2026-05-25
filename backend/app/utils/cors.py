"""CORS helpers — applied on every response, including errors (not on Render 502 proxy)."""

from fastapi import Request
from starlette.responses import Response

from app.config import get_settings


def cors_headers_for_request(request: Request) -> dict[str, str]:
    settings = get_settings()
    origin = request.headers.get("origin")
    if not origin:
        return {}

    normalized = origin.strip().rstrip("/")
    if settings.is_origin_allowed(normalized):
        headers = {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Vary": "Origin",
        }
        if settings.cors_allow_credentials:
            headers["Access-Control-Allow-Credentials"] = "true"
        return headers

    if not settings.cors_origin_list:
        return {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }

    return {}


def apply_cors_to_response(request: Request, response: Response) -> Response:
    for key, value in cors_headers_for_request(request).items():
        response.headers[key] = value
    return response
