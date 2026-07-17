from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["config"])


@router.get("/config")
async def get_config():
    return {"yandex_maps_api_key": settings.YANDEX_MAPS_API_KEY}
