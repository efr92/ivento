from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.auth import (
    UserRegisterSchema,
    UserLoginSchema,
    TokenSchema,
    RefreshTokenSchema
)
from app.services.auth_service import AuthService
from app.kafka.producer import get_kafka_producer, KafkaProducer

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(
    db: AsyncSession = Depends(get_db),
    kafka: KafkaProducer = Depends(get_kafka_producer)
) -> AuthService:
    return AuthService(db, kafka)


@router.post("/register", response_model=TokenSchema, status_code=201)
async def register(
    data: UserRegisterSchema,
    service: AuthService = Depends(get_auth_service)
):
    return await service.register(data)


@router.post("/login", response_model=TokenSchema)
async def login(
    data: UserLoginSchema,
    service: AuthService = Depends(get_auth_service)
):
    return await service.login(data)


@router.post("/refresh", response_model=TokenSchema)
async def refresh_tokens(
    data: RefreshTokenSchema,
    service: AuthService = Depends(get_auth_service)
):
    return await service.refresh_tokens(data.refresh_token)


@router.get("/verify")
async def verify_token(
    authorization: str = Header(...),
    service: AuthService = Depends(get_auth_service)
):
    token = authorization.replace("Bearer ", "")
    return await service.verify_token(token)
