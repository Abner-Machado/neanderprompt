"""Application settings.

Reads from environment variables (and an optional `.env` file). The default
database is SQLite so the project runs and is testable with zero external
services. In production, set ``DATABASE_URL`` to a PostgreSQL DSN and the same
code runs unchanged (we go through SQLAlchemy).
"""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "NeanderPrompt"
    debug: bool = False

    # SQLite by default -> runs anywhere, no Docker required.
    # Production example: postgresql+psycopg://user:pass@localhost:5432/neanderprompt
    database_url: str = Field(default="sqlite:///./neanderprompt.db")

    # Self-Healing RAG knobs.
    confidence_threshold: float = 0.6
    max_heal_attempts: int = 2

    # Default provider used when no API keys are configured. "echo" is a fully
    # offline, deterministic provider so the demo and tests need no network.
    default_provider: str = "echo"
    default_model: str = "echo-1"


@lru_cache
def get_settings() -> Settings:
    return Settings()
