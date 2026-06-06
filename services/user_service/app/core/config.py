import os


class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://admin:changeme123@postgres_auth:5432/auth_db"
    )
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/2")
    AUTH_SERVICE_URL: str = os.getenv("AUTH_SERVICE_URL", "http://auth_service:8000")
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]


settings = Settings()
