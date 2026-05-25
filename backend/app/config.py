import logging
import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env", override=True)
UPLOADS_DIR = BASE_DIR / "uploads"

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str = ""
    openai_endpoint: str | None = None
    openai_api_version: str = "2024-12-01-preview"
    openai_gpt_deployment: str | None = None
    openai_model: str = "gpt-4o"

    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db_name: str = "document_extraction"
    mongo_collection_name: str = "extractions"
    # Comma-separated allowed browser origins, or "*" for dev.
    cors_origins: str = "*"
    # Optional: your Vercel URL (same value you set on Vercel). Merged into CORS allowlist.
    frontend_url: str | None = None

    # OCR — set OCR_LOW_MEMORY=true on Render (512MB). Disables TrOCR + startup warmup.
    ocr_low_memory: bool = False
    ocr_warmup_on_startup: bool = False
    ocr_enable_paddle: bool = True
    ocr_enable_trocr: bool = True

    @property
    def is_low_memory_deploy(self) -> bool:
        if self.ocr_low_memory:
            return True
        return os.getenv("RENDER", "").lower() in ("true", "1", "yes")

    @property
    def paddle_enabled(self) -> bool:
        return self.ocr_enable_paddle

    @property
    def trocr_enabled(self) -> bool:
        if not self.ocr_enable_trocr:
            return False
        if self.is_low_memory_deploy:
            # TrOCR + PyTorch exceed Render 512MB unless explicitly enabled.
            return os.getenv("OCR_ENABLE_TROCR", "").lower() in ("true", "1", "yes")
        return True

    @property
    def should_warmup_ocr_on_startup(self) -> bool:
        if self.is_low_memory_deploy:
            return False
        return self.ocr_warmup_on_startup

    @property
    def use_azure_openai(self) -> bool:
        return bool(self.openai_endpoint and self.openai_endpoint.strip())

    @property
    def chat_model(self) -> str:
        if self.use_azure_openai:
            if not self.openai_gpt_deployment:
                raise ValueError(
                    "OPENAI_GPT_DEPLOYMENT is required when OPENAI_ENDPOINT is set."
                )
            return self.openai_gpt_deployment
        return self.openai_model

    @property
    def azure_endpoint(self) -> str:
        return (self.openai_endpoint or "").rstrip("/")

    @property
    def cors_origin_list(self) -> list[str]:
        """Explicit origins only in production — never rely on '*' with credentials."""
        origins: list[str] = []

        if self.frontend_url and self.frontend_url.strip():
            origins.append(self.frontend_url.strip().rstrip("/"))

        if self.cors_origins.strip() != "*":
            origins.extend(
                origin.strip().rstrip("/")
                for origin in self.cors_origins.split(",")
                if origin.strip()
            )

        if self.is_low_memory_deploy and not origins:
            logger.warning(
                "FRONTEND_URL or CORS_ORIGINS not set on Render — browser requests will be blocked. "
                "Set FRONTEND_URL=https://document-extraction-ultrion.vercel.app"
            )

        seen: set[str] = set()
        unique: list[str] = []
        for origin in origins:
            if origin not in seen:
                seen.add(origin)
                unique.append(origin)
        return unique

    @property
    def cors_allow_credentials(self) -> bool:
        # Browsers reject Access-Control-Allow-Origin: * with credentials.
        return bool(self.cors_origin_list)

    def is_origin_allowed(self, origin: str | None) -> bool:
        if not origin:
            return False
        normalized = origin.strip().rstrip("/")
        if normalized in self.cors_origin_list:
            return True
        if normalized in (
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ):
            return True
        # Frontend is hosted on Vercel (prod + preview URLs).
        if normalized.endswith(".vercel.app"):
            return True
        return False


@lru_cache
def get_settings() -> Settings:
    return Settings()
