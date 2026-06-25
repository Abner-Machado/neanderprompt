from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.db import get_session
from schemas.api import DecisionIn, DecisionOut
from services.decisions import list_decisions, record_decision

router = APIRouter(prefix="/decisions", tags=["decision-registry"])


@router.post("", response_model=DecisionOut)
def create(payload: DecisionIn, session: Session = Depends(get_session)) -> DecisionOut:
    row = record_decision(session, question=payload.question, choice=payload.choice,
                          rationale=payload.rationale, alternatives=payload.alternatives)
    return DecisionOut(id=row.id, question=row.question, choice=row.choice,
                       rationale=row.rationale, alternatives=row.alternatives)


@router.get("", response_model=list[DecisionOut])
def index(session: Session = Depends(get_session)) -> list[DecisionOut]:
    return [
        DecisionOut(id=r.id, question=r.question, choice=r.choice,
                    rationale=r.rationale, alternatives=r.alternatives)
        for r in list_decisions(session)
    ]
