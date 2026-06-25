"""SQLAlchemy engine/session wiring.

Portable across SQLite (local/tests) and PostgreSQL (production) — the rest of
the codebase never imports a driver directly.
"""
from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from core.config import get_settings

_settings = get_settings()

# check_same_thread is a SQLite-only flag; harmless to compute conditionally.
_connect_args = {"check_same_thread": False} if _settings.database_url.startswith("sqlite") else {}

engine = create_engine(_settings.database_url, connect_args=_connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


def init_db() -> None:
    """Create tables. Real deployments should use migrations (Alembic)."""
    from models import orm  # noqa: F401  (register mappers)

    orm.Base.metadata.create_all(bind=engine)


def get_session() -> Iterator[Session]:
    """FastAPI dependency yielding a scoped session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
