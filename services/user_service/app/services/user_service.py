import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from app.models.user_profile import UserProfile
from app.schemas.user import (
    UserProfileCreateSchema,
    UserProfileUpdateSchema,
    UserProfileResponseSchema
)
from app.lang.messages import MESSAGES

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_profile(
        self,
        user_id: int,
        username: str,
        data: UserProfileCreateSchema | None = None
    ) -> UserProfileResponseSchema:
        existing = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=MESSAGES["profile_already_exists"]
            )

        profile = UserProfile(user_id=user_id, username=username)
        if data:
            if data.avatar_url:
                profile.avatar_url = data.avatar_url
            if data.bio:
                profile.bio = data.bio
            if data.location:
                profile.location = data.location
            if data.phone:
                profile.phone = data.phone

        self.db.add(profile)
        await self.db.commit()
        await self.db.refresh(profile)
        logger.info(f"Profile created for user {user_id}")
        return UserProfileResponseSchema.model_validate(profile)

    async def get_profile(self, user_id: int) -> UserProfileResponseSchema:
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=MESSAGES["profile_not_found"]
            )
        return UserProfileResponseSchema.model_validate(profile)

    async def update_profile(
        self,
        user_id: int,
        data: UserProfileUpdateSchema
    ) -> UserProfileResponseSchema:
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=MESSAGES["profile_not_found"]
            )

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(profile, field, value)

        await self.db.commit()
        await self.db.refresh(profile)
        return UserProfileResponseSchema.model_validate(profile)

    async def get_profile_by_username(self, username: str) -> UserProfileResponseSchema:
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.username == username)
        )
        profile = result.scalar_one_or_none()
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=MESSAGES["profile_not_found"]
            )
        return UserProfileResponseSchema.model_validate(profile)
