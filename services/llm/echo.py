"""Offline, deterministic provider.

No network, no API key. It answers using whatever context it is given, so the
Self-Healing RAG loop can be exercised end-to-end (and unit-tested) without any
external model. Behaviour is intentionally simple and reproducible.
"""
from __future__ import annotations

from services.llm.base import Completion, Message


class EchoProvider:
    name = "echo"

    def __init__(self, model: str = "echo-1") -> None:
        self.model = model

    def complete(self, messages: list[Message], *, temperature: float = 0.2) -> Completion:
        system = next((m.content for m in messages if m.role == "system"), "")
        user = next((m.content for m in reversed(messages) if m.role == "user"), "")

        # If the prompt carries retrieved CONTEXT, "answer" by echoing the most
        # relevant context line back — emulating a grounded RAG answer.
        context = ""
        if "CONTEXT:" in system:
            context = system.split("CONTEXT:", 1)[1].strip()

        if context:
            best = _most_overlapping_line(user, context)
            text = best or context.splitlines()[0]
        else:
            text = f"I don't have grounded context for: {user.strip()}"

        return Completion(text=text, model=self.model, raw={"provider": "echo"})


def _most_overlapping_line(query: str, context: str) -> str:
    q = set(_tokens(query))
    best_line, best_score = "", 0
    for line in context.splitlines():
        score = len(q & set(_tokens(line)))
        if score > best_score:
            best_line, best_score = line.strip(), score
    return best_line


def _tokens(text: str) -> list[str]:
    return [t for t in "".join(c.lower() if c.isalnum() else " " for c in text).split() if t]
