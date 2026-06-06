from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.auth import router as auth_router
from app.db.session import engine
from app.db.base import Base
from app.kafka.producer import kafka_producer
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Auth Service...")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await kafka_producer.start()

    logger.info("Auth Service started successfully")

    yield

    logger.info("Shutting down Auth Service...")
    await kafka_producer.stop()
    await engine.dispose()


app = FastAPI(
    title="Auth Service",
    description="Сервис аутентификации и авторизации",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "auth_service"}
