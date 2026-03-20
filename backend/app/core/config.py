from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    app_name: str = "CyberHub backend"
    app_env: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"
    host: str = "0.0.0.0"
    port: int = 8000

    secret_key: str = "CHANGE_ME"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"

    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "cyberhub"
    postgres_user: str = "cyberhub"
    postgres_password: str = "cyberhub"
    database_url: str | None = None

    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    redis_url: str | None = None

    celery_broker_url: str | None = None
    celery_result_backend: str | None = None

    backend_cors_origins: list[str] = ["https://localhost:3000"]
    ws_heartbeat_interval: int = 30

    log_level: str = "INFO"

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def pars_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value
    
    @property
    def sqlalchemy_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
    
    @property
    def redis_dsn(self) -> str:
        if self.redis_url:
            return self.redis_url
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def celery_broker_dsn(self) -> str:
        if self.celery_broker_url:
            return self.celery_broker_url
        return self.redis_dsn

    @property
    def celery_result_backend_dsn(self) -> str:
        if self.celery_result_backend:
            return self.celery_result_backend
        return f"redis://{self.redis_host}:{self.redis_port}/1"


@lru_cache()
def get_settings() -> Settings:
    """Get application settings."""
    return Settings()

settings = get_settings()    
