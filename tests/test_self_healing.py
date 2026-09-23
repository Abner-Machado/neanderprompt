"""The flagship test: the loop heals a failing query and learns a Skill.

Scenario: the default retrieval strategy is too strict (its ``min_score`` filters
out the only relevant document), so the first attempt retrieves nothing and the
judge returns low confidence. The diagnostic subagent detects "no_documents",
loosens the strategy, retries successfully — and the winning strategy is saved
as a reusable Skill. A second, similar query then reuses that Skill with no
healing needed.
"""
from __future__ import annotations

from sqlalchemy import select

from models.orm import QueryLog, Skill
from services.llm.echo import EchoProvider
from services.rag.store import add_knowledge
from services.rag.self_healing import SelfHealingRAG

# Modest lexical overlap with the query: above the healed min_score (0.05) but
# below the default (0.1), so the default strategy filters it and healing rescues it.
_DOC = (
    "FastAPI was selected as the web layer. It provides async endpoints, "
    "dependency injection, pydantic validation and automatically generated "
    "openapi documentation for every published service across our backend stack "
    "running in production."
)
_QUERY = "Why choose FastAPI framework?"


def _engine(session):
    return SelfHealingRAG(session, provider=EchoProvider())


def test_loop_heals_and_learns(session):
    add_knowledge(session, title="Backend choice", content=_DOC, tags=["backend"])

    result = _engine(session).ask(_QUERY)

    # It recovered: confidence cleared the threshold...
    assert result.confidence >= 0.6
    # ...but only after at least one heal (the first attempt failed).
    assert result.healed is True
    assert result.attempts >= 2
    assert result.diagnosis == "no_documents"
    # The trace shows the confidence climbing — closed-loop observability.
    assert result.trace[0]["confidence"] < result.trace[-1]["confidence"]

    # The winning strategy was persisted as a Skill.
    skills = session.execute(select(Skill)).scalars().all()
    assert len(skills) == 1
    assert skills[0].strategy["min_score"] < 0.1

    # And the whole thing was logged.
    logs = session.execute(select(QueryLog)).scalars().all()
    assert len(logs) == 1
    assert logs[0].healed is True


def test_learned_skill_is_reused_without_healing(session):
    add_knowledge(session, title="Backend choice", content=_DOC, tags=["backend"])
    engine = _engine(session)

    first = engine.ask(_QUERY)
    assert first.healed is True

    # Same query signature -> the learned Skill is applied up front, no heal.
    second = engine.ask("Why choose the FastAPI framework here?")
    assert second.used_skill is True
    assert second.healed is False
    assert second.attempts == 1
    assert second.confidence >= 0.6


def test_unanswerable_query_fails_gracefully(session):
    add_knowledge(session, title="Unrelated", content="The cat sat on the mat.")

    result = _engine(session).ask("Explain quantum chromodynamics in detail.")

    assert result.healed is False
    assert result.confidence < 0.6
    # Still fully logged, so a developer can see *why* it failed.
    logs = session.execute(select(QueryLog)).scalars().all()
    assert len(logs) == 1
    assert len(logs[0].trace) >= 1


def test_answering_keeps_knowledge_out_of_decay(session):
    """Knowledge that grounds an accepted answer counts as used.

    Before this, ``last_used_at`` was only ever set on insert, so a document
    answering questions every day was still flagged for review a year later.
    """
    import datetime as dt

    from services.decay import scan_for_decay

    row = add_knowledge(session, title="Backend choice", content=_DOC, tags=["backend"])
    row.last_used_at = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=800)
    session.commit()

    result = _engine(session).ask(_QUERY)
    assert result.confidence >= 0.6

    assert scan_for_decay(session, max_age_days=365) == []
    assert row.status == "active"


def test_reused_skill_refreshes_last_used(session):
    import datetime as dt

    add_knowledge(session, title="Backend choice", content=_DOC, tags=["backend"])
    _engine(session).ask(_QUERY)
    skill = session.execute(select(Skill)).scalar_one()
    old = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=800)
    skill.last_used_at = old
    session.commit()

    _engine(session).ask(_QUERY)

    last = skill.last_used_at
    if last.tzinfo is None:
        last = last.replace(tzinfo=dt.timezone.utc)
    assert last > old + dt.timedelta(days=700)
