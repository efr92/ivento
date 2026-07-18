from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.auth import UserRegisterSchema, UserLoginSchema, TokenSchema
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)
from app.kafka.producer import KafkaProducer
from app.lang.messages import MESSAGES
from shared.kafka_topics import KafkaTopics
import json


class AuthService:
    def __init__(self, db: AsyncSession, kafka_producer: KafkaProducer):
        self.db = db
        self.kafka = kafka_producer

    async def register(self, data: UserRegisterSchema) -> TokenSchema:
        existing = await self.db.execute(
            select(User).where(
                (User.email == data.email) | (User.username == data.username)
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=MESSAGES["user_already_exists"]
            )

        user = User(
            email=data.email,
            username=data.username,
            hashed_password=hash_password(data.password)
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        await self.kafka.send(
            topic=KafkaTopics.USER_REGISTERED,
            value={
                "user_id": user.id,
                "email": user.email,
                "username": user.username
            },
            key=str(user.id)
        )

        return TokenSchema(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id)
        )

    async def login(self, data: UserLoginSchema) -> TokenSchema:
        result = await self.db.execute(
            select(User).where(User.email == data.email)
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=MESSAGES["incorrect_email_or_password"]
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=MESSAGES["account_disabled"]
            )

        return TokenSchema(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id)
        )

    async def refresh_tokens(self, refresh_token: str) -> TokenSchema:
        try:
            payload = decode_token(refresh_token)
            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=MESSAGES["invalid_token_type"]
                )
            user_id = int(payload["sub"])
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=MESSAGES["invalid_refresh_token"]
            )

        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=MESSAGES["user_not_found_or_inactive"]
            )

        return TokenSchema(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id)
        )

    async def verify_token(self, token: str) -> dict:
        try:
            payload = decode_token(token)
            if payload.get("type") != "access":
                raise ValueError(MESSAGES["not_access_token"])

            result = await self.db.execute(
                select(User).where(User.id == int(payload["sub"]))
            )
            user = result.scalar_one_or_none()

            if not user or not user.is_active:
                raise ValueError(MESSAGES["user_not_found"])

            return {
                "user_id": user.id,
                "email": user.email,
                "username": user.username
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e)
            )
