"""The diagnostic subagent.

When the judge returns low confidence, this is what gets dispatched: it inspects
*why* the attempt was weak (no documents? irrelevant documents? weak synthesis?)
and returns a mutated ``RetrievalStrategy`` to try next, plus a label for the
log. Rules are deterministic so the loop is debuggable and testable offline; a
model-backed diagnoser can later implement the same ``diagnose`` signature.
"""
from __future__ import annotations

from dataclasses import dataclass

from services.rag.judge import Verdict
from services.rag.store import Chunk
from services.rag.strategy import RetrievalStrategy
from utils.text import tokens


@dataclass
class Diagnosis:
    label: str
    strategy: RetrievalStrategy
    note: str


def diagnose(query: str, chunks: list[Chunk], verdict: Verdict,
             current: RetrievalStrategy) -> Diagnosis:
    salient = tokens(query)

    # 1) Nothing came back -> retrieval was too strict / vocabulary mismatch.
    if not chunks:
        nxt = RetrievalStrategy(
            top_k=current.top_k + 2,
            min_score=max(0.0, current.min_score - 0.05),
            expand_terms=salient,
        )
        return Diagnosis("no_documents", nxt, "widened recall: lower threshold + expand terms")

    top = max(c.score for c in chunks)

    # 2) Documents came back but none are really relevant -> expand the query.
    if top < 0.15:
        nxt = RetrievalStrategy(
            top_k=current.top_k + 2,
            min_score=max(0.0, current.min_score - 0.03),
            expand_terms=sorted(set(current.expand_terms) | set(salient)),
        )
        return Diagnosis("low_relevance", nxt, "expanded query terms to improve match")

    # 3) Relevant docs exist but the answer didn't use them -> feed more context.
    nxt = RetrievalStrategy(
        top_k=current.top_k + 3,
        min_score=current.min_score,
        expand_terms=current.expand_terms,
    )
    return Diagnosis("weak_synthesis", nxt, "increased context window for grounding")
