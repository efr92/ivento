import json
import logging
import asyncio
from aiokafka import AIOKafkaConsumer
from app.core.config import settings
from shared.kafka_topics import KafkaTopics

logger = logging.getLogger(__name__)


class KafkaConsumer:
    def __init__(self):
        self._consumer: AIOKafkaConsumer | None = None
        self._running = False

    async def start(self):
        self._consumer = AIOKafkaConsumer(
            KafkaTopics.USER_REGISTERED,
            KafkaTopics.USER_UPDATED,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id="event_service_group",
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            auto_commit_interval_ms=1000,
        )
        await self._consumer.start()
        self._running = True
        logger.info("Kafka consumer started")
        asyncio.create_task(self._consume_loop())

    async def stop(self):
        self._running = False
        if self._consumer:
            await self._consumer.stop()

    async def _consume_loop(self):
        try:
            async for msg in self._consumer:
                if not self._running:
                    break
                await self._process_message(msg.topic, msg.value)
        except Exception as e:
            logger.error(f"Consumer error: {e}")

    async def _process_message(self, topic: str, value: dict):
        logger.info(f"Processing message from {topic}: {value}")

        handlers = {
            KafkaTopics.USER_REGISTERED: self._handle_user_registered,
            KafkaTopics.USER_UPDATED: self._handle_user_updated,
        }

        handler = handlers.get(topic)
        if handler:
            await handler(value)

    async def _handle_user_registered(self, data: dict):
        logger.info(f"New user registered: {data['user_id']}")

    async def _handle_user_updated(self, data: dict):
        logger.info(f"User updated: {data['user_id']}")
