"""Decision Registry — record *why* choices were made.

Minimal but real: projects rot when the rationale behind "why FastAPI / why we
dropped Node" is lost. This keeps each decision queryable forever.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.orm import Decision


def record_decision(session: Session, *, question: str, choice: str,
                    rationale: str, alternatives: list[str] | None = None) -> Decision:
    row = Decision(question=question, choice=choice, rationale=rationale,
                   alternatives=alternatives or [])
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def list_decisions(session: Session) -> list[Decision]:
    return list(session.execute(select(Decision).order_by(Decision.created_at.desc())).scalars())
