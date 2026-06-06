from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.user import (
    UserProfileCreateSchema,
    UserProfileUpdateSchema,
    UserProfileResponseSchema
)
from app.services.user_service import UserService
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)


@router.get("/me", response_model=UserProfileResponseSchema)
async def get_my_profile(
    current_user: dict = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
):
    return await service.get_profile(current_user["user_id"])


@router.post("/me", response_model=UserProfileResponseSchema, status_code=201)
async def create_my_profile(
    data: UserProfileCreateSchema,
    current_user: dict = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
):
    return await service.create_profile(current_user["user_id"], current_user["username"], data)


@router.patch("/me", response_model=UserProfileResponseSchema)
async def update_my_profile(
    data: UserProfileUpdateSchema,
    current_user: dict = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
):
    return await service.update_profile(current_user["user_id"], data)


@router.get("/{username}", response_model=UserProfileResponseSchema)
async def get_profile_by_username(
    username: str,
    service: UserService = Depends(get_user_service)
):
    return await service.get_profile_by_username(username)
