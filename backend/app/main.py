import logging
from contextlib import asynccontextmanager

import app.paddle_env  # noqa: F401 — set HOME for Paddle cache before OCR imports

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from app.config import UPLOADS_DIR, get_settings
from app.providers.mongodb_provider import mongodb_provider
from app.routes import api_router
from app.utils.cors import apply_cors_to_response, cors_headers_for_request
from app.utils.exceptions import AppException

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    from app.providers.llm.openai_provider import reset_openai_provider
    from app.providers.ocr.model_loader import warmup_ocr_models

    get_settings.cache_clear()
    reset_openai_provider()
    settings = get_settings()
    llm_host = (
        settings.azure_endpoint
        if settings.use_azure_openai
        else "api.openai.com"
    )

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

    mongo_ok = await mongodb_provider.connect()
    if not mongo_ok:
        logger.warning(
            "Starting without MongoDB — configure MONGO_URI (MongoDB Atlas) on Render. "
            "/extract will fail until the database is reachable."
        )

    try:
        await warmup_ocr_models()
    except Exception as exc:
        logger.warning("OCR startup warmup failed: %s", exc)

    ocr_engines = []
    if settings.paddle_enabled:
        ocr_engines.append("paddleocr")
    if settings.trocr_enabled:
        ocr_engines.append("trocr")

    cors_origins = settings.cors_origin_list

    logger.info(
        "API ready | OCR: %s (low_memory=%s) | CORS: %s | LLM: %s @ %s",
        "+".join(ocr_engines) or "none",
        settings.is_low_memory_deploy,
        cors_origins or "(none — set FRONTEND_URL)",
        settings.chat_model,
        llm_host,
    )

    yield
    await mongodb_provider.disconnect()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Intelligent Document Extraction API",
        description=(
            "Enterprise document extraction: local PaddleOCR + TrOCR on-server, "
            "GPT-4o semantic extraction only."
        ),
        version="4.0.0",
        lifespan=lifespan,
    )

    cors_origins = settings.cors_origin_list
    cors_kwargs: dict = {
        "allow_methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["*"],
        "expose_headers": ["*"],
    }
    if settings.is_low_memory_deploy:
        cors_kwargs["allow_origin_regex"] = r"https://([a-z0-9-]+\.)*vercel\.app"
        cors_kwargs["allow_origins"] = cors_origins or []
        cors_kwargs["allow_credentials"] = True
    elif cors_origins:
        cors_kwargs["allow_origins"] = cors_origins
        cors_kwargs["allow_credentials"] = settings.cors_allow_credentials
    else:
        cors_kwargs["allow_origins"] = ["*"]
        cors_kwargs["allow_credentials"] = False

    app.add_middleware(CORSMiddleware, **cors_kwargs)

    @app.middleware("http")
    async def ensure_cors_headers(request: Request, call_next):
        """Guarantee CORS headers on every app response (including 4xx/5xx)."""
        if request.method == "OPTIONS" and request.headers.get("origin"):
            headers = cors_headers_for_request(request)
            if headers:
                headers["Access-Control-Max-Age"] = "86400"
                return Response(status_code=204, headers=headers)

        response = await call_next(request)
        return apply_cors_to_response(request, response)

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
            headers=cors_headers_for_request(request),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        return JSONResponse(
            status_code=422,
            content={"detail": "Request validation failed.", "errors": exc.errors()},
            headers=cors_headers_for_request(request),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected server error occurred.", "error": str(exc)},
            headers=cors_headers_for_request(request),
        )

    @app.get("/health")
    async def health_check():
        settings = get_settings()
        mongo_status = "connected" if mongodb_provider.is_connected else "disconnected"
        ocr_engines = []
        if settings.paddle_enabled:
            ocr_engines.append("paddleocr")
        if settings.trocr_enabled:
            ocr_engines.append("trocr")
        paddle_version = None
        numpy_version = None
        cv2_version = None
        try:
            import numpy as _np

            numpy_version = _np.__version__
        except Exception:
            pass
        try:
            import cv2 as _cv2

            cv2_version = _cv2.__version__
        except Exception:
            pass
        try:
            import paddleocr as _po

            paddle_version = _po.__version__
        except Exception:
            pass

        from app.paddle_env import cached_det_rec_dirs, paddle_cache_root
        from app.providers.ocr.paddle_provider import is_paddle_loaded

        det_dir, rec_dir = cached_det_rec_dirs()

        return {
            "status": "ok" if mongo_status == "connected" else "degraded",
            "pipeline": "opencv-" + "-".join(ocr_engines or ["none"]) + "-gpt4o",
            "ocr_execution_mode": "local",
            "ocr_engines": ocr_engines,
            "paddleocr_version": paddle_version,
            "numpy_version": numpy_version,
            "cv2_version": cv2_version,
            "opencv_ok": cv2_version is not None,
            "paddleocr_ok_for_render": (
                paddle_version.startswith("2.") if paddle_version else None
            ),
            "numpy_ok_for_paddle": (
                numpy_version.startswith("1.") if numpy_version else None
            ),
            "paddleocr_loaded": is_paddle_loaded(),
            "paddle_models_cached": det_dir is not None and rec_dir is not None,
            "paddle_cache_root": str(paddle_cache_root()),
            "low_memory_mode": settings.is_low_memory_deploy,
            "mongodb": mongo_status,
            "mongodb_error": mongodb_provider.last_error
            if mongo_status == "disconnected"
            else None,
            "cors_allowed_origins": settings.cors_origin_list,
            "cors_vercel_allowed": True,
        }

    @app.api_route("/", methods=["GET", "HEAD"])
    async def root():
        return {
            "service": "document-extraction-api",
            "health": "/health",
            "extract": "POST /extract",
        }

    app.include_router(api_router)
    return app


app = create_app()
