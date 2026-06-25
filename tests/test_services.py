"""Decision Registry, Knowledge Decay, Anti-AI Drift and Genome."""
from __future__ import annotations

import datetime as dt

from services.decay import scan_for_decay
from services.decisions import list_decisions, record_decision
from services.drift import compare
from services.genome import build_graph
from services.llm.echo import EchoProvider
from services.rag.store import add_knowledge


def test_decision_registry_roundtrip(session):
    record_decision(session, question="Why FastAPI?", choice="FastAPI",
                    rationale="Async + OpenAI docs out of the box.",
                    alternatives=["Flask", "Node"])
    decisions = list_decisions(session)
    assert decisions[0].choice == "FastAPI"
    assert "Node" in decisions[0].alternatives


def test_decay_flags_stale_knowledge(session):
    row = add_knowledge(session, title="Old note", content="legacy")
    # Backdate last_used beyond the window.
    row.last_used_at = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=400)
    session.commit()

    stale = scan_for_decay(session, max_age_days=365)
    assert len(stale) == 1
    assert stale[0].status == "review"


def test_drift_consensus(session):
    # Two providers agree, one diverges -> consensus picks the agreeing answer.
    class Fixed(EchoProvider):
        def __init__(self, text):
            self._text = text
        def complete(self, messages, *, temperature=0.2):
            from services.llm.base import Completion
            return Completion(text=self._text, model="fixed")

    providers = {
        "a": Fixed("we use postgres for storage"),
        "b": Fixed("we use postgres for storage"),
        "c": Fixed("completely different unrelated answer banana"),
    }
    report = compare("which database?", providers, divergence_threshold=0.3)
    assert "postgres" in report.consensus
    assert "c" in report.diverging


def test_genome_links_by_shared_tags(session):
    a = add_knowledge(session, title="MCP", content="x", tags=["docker", "python"])
    b = add_knowledge(session, title="CI", content="y", tags=["docker"])
    add_knowledge(session, title="Note", content="z", tags=["writing"])

    graph = build_graph(session)
    assert str(b.id) in graph[str(a.id)]  # linked via "docker"
