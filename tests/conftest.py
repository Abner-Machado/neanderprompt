from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.orm import Base


@pytest.fixture
def engine():
    # In-memory SQLite shared across connections (StaticPool) -> fast, isolated.
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def session(engine):
    Session = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    s = Session()
    try:
        yield s
    finally:
        s.close()


@pytest.fixture
def client(engine):
    """FastAPI TestClient wired to the in-memory engine."""
    from fastapi.testclient import TestClient

    from app.main import create_app
    from core.db import get_session

    Session = sessionmaker(bind=engine, expire_on_commit=False, future=True)

    def _get_session():
        s = Session()
        try:
            yield s
        finally:
            s.close()

    app = create_app()
    app.dependency_overrides[get_session] = _get_session
    # Skip startup init_db (it would target the file DB); tables already exist.
    with TestClient(app) as c:
        yield c
