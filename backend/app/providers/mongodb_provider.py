import logging
from datetime import datetime, timezone
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase
from pymongo.errors import ServerSelectionTimeoutError

from app.config import get_settings
from app.utils.exceptions import DatabaseError

logger = logging.getLogger(__name__)

MONGO_CONNECT_TIMEOUT_MS = 5_000


class MongoDBProvider:
    def __init__(self) -> None:
        self._client: AsyncIOMotorClient | None = None
        self._db: AsyncIOMotorDatabase | None = None
        self._collection: AsyncIOMotorCollection | None = None
        self._connected = False
        self._last_error: str | None = None

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def last_error(self) -> str | None:
        return self._last_error

    async def connect(self) -> bool:
        """Connect to MongoDB. Returns False instead of crashing the app on failure."""
        settings = get_settings()
        self._connected = False
        self._last_error = None

        try:
            self._client = AsyncIOMotorClient(
                settings.mongo_uri,
                serverSelectionTimeoutMS=MONGO_CONNECT_TIMEOUT_MS,
                connectTimeoutMS=MONGO_CONNECT_TIMEOUT_MS,
            )
            self._db = self._client[settings.mongo_db_name]
            self._collection = self._db[settings.mongo_collection_name]
            await self._client.admin.command("ping")
            self._connected = True
            logger.info("MongoDB connected (%s)", settings.mongo_db_name)
            return True
        except ServerSelectionTimeoutError as exc:
            self._last_error = str(exc)
            await self._reset_client()
            _log_mongo_failure(settings.mongo_uri, exc)
            return False
        except Exception as exc:
            self._last_error = str(exc)
            await self._reset_client()
            logger.error("MongoDB connection failed: %s", exc)
            return False

    async def _reset_client(self) -> None:
        if self._client is not None:
            self._client.close()
        self._client = None
        self._db = None
        self._collection = None
        self._connected = False

    async def disconnect(self) -> None:
        await self._reset_client()

    async def ensure_connected(self) -> None:
        if self._connected:
            return
        if await self.connect():
            return
        raise DatabaseError(_mongo_setup_message())

    @property
    def collection(self) -> AsyncIOMotorCollection:
        if self._collection is None or not self._connected:
            raise DatabaseError(_mongo_setup_message())
        return self._collection

    async def save_hybrid_extraction(
        self,
        *,
        filename: str,
        original_prompt: str,
        paddleocr_output: dict[str, Any],
        trocr_output: dict[str, Any],
        fusion_context: str,
        final_ai_response: dict[str, Any] | list[Any],
        extracted_text: str = "",
    ) -> dict[str, Any]:
        await self.ensure_connected()

        document = {
            "filename": filename,
            "original_prompt": original_prompt,
            "user_prompt": original_prompt,
            "paddleocr_output": paddleocr_output,
            "trocr_output": trocr_output,
            "fusion_context": fusion_context,
            "final_ai_response": final_ai_response,
            "ai_response": final_ai_response,
            "ocr_execution_mode": "local",
            "extracted_text": extracted_text
            or paddleocr_output.get("text", "")
            or trocr_output.get("text", ""),
            "created_at": datetime.now(timezone.utc),
        }

        try:
            result = await self.collection.insert_one(document)
        except Exception as exc:
            raise DatabaseError(f"Failed to save extraction: {exc}") from exc

        document["_id"] = str(result.inserted_id)
        document["id"] = document["_id"]
        return document


def _mongo_setup_message() -> str:
    return (
        "MongoDB is not available. On Render, set MONGO_URI to a MongoDB Atlas "
        "connection string (not localhost). Example: "
        "mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=majority"
    )


def _log_mongo_failure(mongo_uri: str, exc: Exception) -> None:
    host_hint = (
        "localhost (no MongoDB on Render — use MongoDB Atlas)"
        if "localhost" in mongo_uri or "127.0.0.1" in mongo_uri
        else mongo_uri.split("@")[-1] if "@" in mongo_uri else mongo_uri
    )
    logger.error(
        "MongoDB unreachable at %s (%s). %s",
        host_hint,
        exc,
        _mongo_setup_message(),
    )


mongodb_provider = MongoDBProvider()
