import json
import logging
from typing import Any
from aiokafka import AIOKafkaProducer
from app.core.config import settings

logger = logging.getLogger(__name__)


class KafkaProducer:
    def __init__(self):
        self._producer: AIOKafkaProducer | None = None

    async def start(self):
        self._producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            acks="all",
            retry_backoff_ms=500,
            request_timeout_ms=30000,
        )
        await self._producer.start()
        logger.info("Kafka producer started")

    async def stop(self):
        if self._producer:
            await self._producer.stop()
            logger.info("Kafka producer stopped")

    async def send(
        self,
        topic: str,
        value: dict[str, Any],
        key: str | None = None
    ):
        if not self._producer:
            raise RuntimeError("Producer not started")
        try:
            await self._producer.send_and_wait(topic, value=value, key=key)
            logger.debug(f"Message sent to topic {topic}: {value}")
        except Exception as e:
            logger.error(f"Failed to send message to {topic}: {e}")
            raise


kafka_producer = KafkaProducer()


async def get_kafka_producer() -> KafkaProducer:
    return kafka_producer
