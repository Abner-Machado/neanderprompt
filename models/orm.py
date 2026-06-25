"""Database models.

These tables encode NeanderPrompt's thesis: knowledge is an asset that must be
captured, kept fresh, and reused. ``Skill`` is what the Self-Healing RAG loop
writes back when it discovers a retrieval strategy that works — institutional
memory, learned automatically.
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy import JSON, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


class Base(DeclarativeBase):
    pass


class Knowledge(Base):
    """A unit of preserved knowledge (note, snippet, MCP, workflow, doc...)."""

    __tablename__ = "knowledge"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(300))
    content: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(200), default="manual")
    tags: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    # Knowledge Decay Prevention reads this to flag stale assets.
    last_used_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active|review|obsolete


class Skill(Base):
    """A retrieval/answer strategy the system learned and made permanent."""

    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pattern: Mapped[str] = mapped_column(String(300), index=True)  # query signature it applies to
    strategy: Mapped[dict] = mapped_column(JSON, default=dict)     # the winning RetrievalStrategy
    note: Mapped[str] = mapped_column(Text, default="")
    hits: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    last_used_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class QueryLog(Base):
    """Closed-loop observability: every query, what happened, and whether we healed it."""

    __tablename__ = "query_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    query: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text, default="")
    model: Mapped[str] = mapped_column(String(80), default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    healed: Mapped[bool] = mapped_column(default=False)
    attempts: Mapped[int] = mapped_column(Integer, default=1)
    diagnosis: Mapped[str] = mapped_column(String(80), default="")
    trace: Mapped[list] = mapped_column(JSON, default=list)  # per-attempt steps
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Decision(Base):
    """Decision Registry: why we chose X over Y. Projects die without this."""

    __tablename__ = "decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    question: Mapped[str] = mapped_column(Text)           # "Why FastAPI?"
    choice: Mapped[str] = mapped_column(String(200))      # "FastAPI"
    rationale: Mapped[str] = mapped_column(Text)
    alternatives: Mapped[list] = mapped_column(JSON, default=list)  # ["Node", "Flask"]
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class LifeLesson(Base):
    """Life Knowledge Layer: failures and learnings as versionable assets."""

    __tablename__ = "life_lessons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(300))
    year: Mapped[int] = mapped_column(Integer)
    cause: Mapped[list] = mapped_column(JSON, default=list)
    lesson: Mapped[list] = mapped_column(JSON, default=list)
    impact: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
