from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI

from app.kafka.consumer import NotificationConsumer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

notification_consumer = NotificationConsumer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Notification Service...")
    await notification_consumer.start()
    logger.info("Notification Service started successfully")

    yield

    logger.info("Shutting down Notification Service...")
    await notification_consumer.stop()


app = FastAPI(
    title="Notification Service",
    description="Сервис уведомлений (email, push)",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "notification_service"}
