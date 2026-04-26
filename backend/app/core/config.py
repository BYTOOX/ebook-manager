from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Aurelia"
    APP_ENV: str = "development"
    APP_URL: str = "http://localhost:3000"
    API_URL: str = "http://localhost:8000"
    DATABASE_URL: str = "postgresql+psycopg://aurelia:aurelia@localhost:5432/aurelia"
    SECRET_KEY: str = "change-me-in-production"
    LIBRARY_PATH: Path = Path("/data/library")
    INCOMING_PATH: Path = Path("/data/library/incoming")
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    SESSION_COOKIE_NAME: str = "aurelia_session"
    SESSION_COOKIE_SECURE: bool = False
    SESSION_COOKIE_SAMESITE: str = "lax"
    SESSION_EXPIRE_MINUTES: int = 60 * 24 * 30
    FIRST_USER_SETUP_TOKEN: str | None = None
    MAX_UPLOAD_SIZE_MB: int = 200
    METADATA_OPENLIBRARY_ENABLED: bool = True
    METADATA_GOOGLEBOOKS_ENABLED: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
