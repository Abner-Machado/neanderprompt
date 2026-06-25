"""FastAPI application entrypoint.

Run locally (SQLite, no Docker needed):

    uvicorn app.main:app --reload

Then open http://localhost:8000/docs
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.routes import decisions, health, knowledge, rag
from core.config import get_settings
from core.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        description="Infrastructure for preserving, evolving and sharing knowledge.",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.include_router(health.router)
    app.include_router(knowledge.router)
    app.include_router(rag.router)
    app.include_router(decisions.router)
    return app


app = create_app()
