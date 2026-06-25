from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.config import get_settings
from core.db import get_session
from schemas.api import AskIn, AskOut
from services.llm.factory import build_provider
from services.rag.self_healing import SelfHealingRAG

router = APIRouter(prefix="/rag", tags=["self-healing-rag"])


@router.post("/ask", response_model=AskOut)
def ask(payload: AskIn, session: Session = Depends(get_session)) -> AskOut:
    model_id = payload.model or get_settings().default_model
    engine = SelfHealingRAG(session, provider=build_provider(model_id))
    result = engine.ask(payload.query)
    return AskOut(
        answer=result.answer, confidence=result.confidence, healed=result.healed,
        attempts=result.attempts, diagnosis=result.diagnosis,
        used_skill=result.used_skill, trace=result.trace,
    )
