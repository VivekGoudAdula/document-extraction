from datetime import datetime, timezone
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase

from app.config import get_settings
from app.utils.exceptions import DatabaseError


class MongoDBProvider:
    def __init__(self) -> None:
        self._client: AsyncIOMotorClient | None = None
        self._db: AsyncIOMotorDatabase | None = None
        self._collection: AsyncIOMotorCollection | None = None

    async def connect(self) -> None:
        settings = get_settings()
        self._client = AsyncIOMotorClient(settings.mongo_uri)
        self._db = self._client[settings.mongo_db_name]
        self._collection = self._db[settings.mongo_collection_name]
        await self._client.admin.command("ping")

    async def disconnect(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
            self._db = None
            self._collection = None

    @property
    def collection(self) -> AsyncIOMotorCollection:
        if self._collection is None:
            raise DatabaseError("MongoDB is not connected.")
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


mongodb_provider = MongoDBProvider()
