from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

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

    openai_api_key: str
    openai_endpoint: str | None = None
    openai_api_version: str = "2024-12-01-preview"
    openai_gpt_deployment: str | None = None
    openai_model: str = "gpt-4o"

    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db_name: str = "document_extraction"
    mongo_collection_name: str = "extractions"
    cors_origins: str = "*"

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
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
