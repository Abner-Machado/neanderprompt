"""Request/response models for the HTTP API."""
from __future__ import annotations

from pydantic import BaseModel, Field


class KnowledgeIn(BaseModel):
    title: str
    content: str
    source: str = "manual"
    tags: list[str] = Field(default_factory=list)


class KnowledgeOut(BaseModel):
    id: int
    title: str
    status: str


class AskIn(BaseModel):
    query: str
    model: str | None = None  # registry id; defaults to settings.default_model


class AskOut(BaseModel):
    answer: str
    confidence: float
    healed: bool
    attempts: int
    diagnosis: str
    used_skill: bool
    trace: list[dict]


class DecisionIn(BaseModel):
    question: str
    choice: str
    rationale: str
    alternatives: list[str] = Field(default_factory=list)


class DecisionOut(BaseModel):
    id: int
    question: str
    choice: str
    rationale: str
    alternatives: list[str]
