"""Knowledge store + retrieval.

Lexical retrieval over the ``knowledge`` table — no vector DB required to run.
The scoring function is isolated so it can be replaced by embeddings/pgvector
later without touching the self-healing loop.
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.orm import Knowledge
from services.rag.strategy import RetrievalStrategy
from utils.text import jaccard


@dataclass
class Chunk:
    knowledge_id: int
    title: str
    content: str
    score: float


def add_knowledge(session: Session, *, title: str, content: str,
                  source: str = "manual", tags: list[str] | None = None) -> Knowledge:
    row = Knowledge(title=title, content=content, source=source, tags=tags or [])
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def retrieve(session: Session, query: str, strategy: RetrievalStrategy) -> list[Chunk]:
    """Score every knowledge row against the (possibly rewritten/expanded) query."""
    effective_query = strategy.rewrite or query
    if strategy.expand_terms:
        effective_query = f"{effective_query} {' '.join(strategy.expand_terms)}"

    rows = session.execute(select(Knowledge)).scalars().all()
    scored: list[Chunk] = []
    for row in rows:
        score = jaccard(effective_query, f"{row.title} {row.content}")
        # Zero lexical overlap is never a retrieval, even if min_score drops to 0
        # during healing — otherwise the loop could "ground" an answer in an
        # entirely unrelated document and report false confidence.
        if score > 0 and score >= strategy.min_score:
            scored.append(Chunk(row.id, row.title, row.content, score))

    scored.sort(key=lambda c: c.score, reverse=True)
    return scored[: strategy.top_k]
