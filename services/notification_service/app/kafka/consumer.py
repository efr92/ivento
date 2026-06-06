import json
import logging
import asyncio
from aiokafka import AIOKafkaConsumer
from app.core.config import settings
from app.services.notification_service import NotificationService
from shared.kafka_topics import KafkaTopics

logger = logging.getLogger(__name__)


class NotificationConsumer:
    def __init__(self):
        self._consumer: AIOKafkaConsumer | None = None
        self._notification_service = NotificationService()

    async def start(self):
        self._consumer = AIOKafkaConsumer(
            KafkaTopics.EVENT_CREATED,
            KafkaTopics.USER_JOINED_EVENT,
            KafkaTopics.USER_LEFT_EVENT,
            KafkaTopics.COMMENT_CREATED,
            KafkaTopics.USER_REGISTERED,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id="notification_service_group",
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset="earliest",
        )
        await self._consumer.start()
        logger.info("Notification consumer started")
        asyncio.create_task(self._consume_loop())

    async def stop(self):
        if self._consumer:
            await self._consumer.stop()

    async def _consume_loop(self):
        async for msg in self._consumer:
            try:
                await self._route_message(msg.topic, msg.value)
            except Exception as e:
                logger.error(f"Error processing notification: {e}")

    async def _route_message(self, topic: str, data: dict):
        handlers = {
            KafkaTopics.USER_REGISTERED: self._notify_welcome,
            KafkaTopics.EVENT_CREATED: self._notify_event_created,
            KafkaTopics.USER_JOINED_EVENT: self._notify_user_joined,
            KafkaTopics.COMMENT_CREATED: self._notify_new_comment,
        }

        handler = handlers.get(topic)
        if handler:
            await handler(data)

    async def _notify_welcome(self, data: dict):
        await self._notification_service.send_email(
            to=data["email"],
            subject="Добро пожаловать в События на карте!",
            body=f"Привет, {data['username']}! Рады видеть вас."
        )

    async def _notify_event_created(self, data: dict):
        logger.info(f"Event created notification: {data['event_id']}")

    async def _notify_user_joined(self, data: dict):
        logger.info(f"User {data['user_id']} joined event {data['event_id']}")

    async def _notify_new_comment(self, data: dict):
        logger.info(f"New comment on event {data['event_id']}")
