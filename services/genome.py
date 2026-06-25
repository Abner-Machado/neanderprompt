"""Knowledge Genome — give every asset a "DNA" and find hidden links.

DESIGN STUB (see docs/roadmap.md). The thesis: each piece of knowledge is made
of components (e.g. an MCP = automation + VPS + Python + Docker + Claude).
Modelled as a graph, the system surfaces non-obvious connections ("everything
that depends on Docker", "what breaks if Python 3.14 is dropped").

This module ships the *contract* and a trivial tag-overlap graph so the API and
tests have something to call; the real graph store (e.g. networkx today,
Postgres/pgvector or a graph DB later) is future work.
"""
from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy.orm import Session

from models.orm import Knowledge


def build_graph(session: Session) -> dict[str, list[str]]:
    """Return adjacency by shared tags: knowledge_id -> [related knowledge_ids].

    Trivial first implementation. Roadmap: weight edges, extract components from
    content, and detect dead-dependency clusters.
    """
    from sqlalchemy import select

    rows = session.execute(select(Knowledge)).scalars().all()
    graph: dict[str, list[str]] = {}
    for a in rows:
        related = [
            str(b.id) for b in rows
            if b.id != a.id and _shares(a.tags, b.tags)
        ]
        graph[str(a.id)] = related
    return graph


def _shares(a: Iterable[str] | None, b: Iterable[str] | None) -> bool:
    return bool(set(a or []) & set(b or []))
