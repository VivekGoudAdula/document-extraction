from fastapi import APIRouter

from app.routes.extract import router as extract_router
from app.routes.upload import router as upload_router

api_router = APIRouter()
api_router.include_router(upload_router)
api_router.include_router(extract_router)
