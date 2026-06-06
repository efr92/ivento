from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.events import router as events_router
from app.db.session import engine
from app.db.base import Base
from app.kafka.producer import kafka_producer
from app.kafka.consumer import KafkaConsumer
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

kafka_consumer = KafkaConsumer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Event Service...")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await kafka_producer.start()
    await kafka_consumer.start()

    logger.info("Event Service started successfully")

    yield

    logger.info("Shutting down Event Service...")
    await kafka_producer.stop()
    await kafka_consumer.stop()
    await engine.dispose()


app = FastAPI(
    title="Event Service",
    description="Сервис управления событиями на карте",
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

app.include_router(events_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "event_service"}
