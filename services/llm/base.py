"""The single interface every AI model speaks through.

Adding support for a new vendor means writing one class with a ``complete``
method. The rest of NeanderPrompt (RAG, judge, drift, diagnosis) depends only
on this protocol — never on a concrete SDK.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class Message:
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class Completion:
    text: str
    model: str
    raw: dict | None = None


@runtime_checkable
class LLMProvider(Protocol):
    """Minimal contract: turn messages into a completion."""

    name: str

    def complete(self, messages: list[Message], *, temperature: float = 0.2) -> Completion:
        ...
