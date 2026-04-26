from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
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
    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"]
    )
    SESSION_COOKIE_NAME: str = "aurelia_session"
    SESSION_COOKIE_SECURE: bool = False
    SESSION_COOKIE_SAMESITE: str = "lax"
    SESSION_EXPIRE_MINUTES: int = 60 * 24 * 30
    FIRST_USER_SETUP_TOKEN: str | None = None
    METADATA_OPENLIBRARY_ENABLED: bool = True
    METADATA_GOOGLEBOOKS_ENABLED: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
