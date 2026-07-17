import json
import os


class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://admin:changeme123@postgres_events:5432/events_db"
    )
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/1")
    AUTH_SERVICE_URL: str = os.getenv("AUTH_SERVICE_URL", "http://auth_service:8000")
    YANDEX_MAPS_API_KEY: str = os.getenv("YANDEX_MAPS_API_KEY", "")

    @property
    def ALLOWED_ORIGINS(self) -> list[str]:
        raw = os.getenv("ALLOWED_ORIGINS", '["http://localhost:3000"]')
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return ["http://localhost:3000"]


settings = Settings()
