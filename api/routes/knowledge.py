from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.db import get_session
from schemas.api import KnowledgeIn, KnowledgeOut
from services.rag.store import add_knowledge

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.post("", response_model=KnowledgeOut)
def create(payload: KnowledgeIn, session: Session = Depends(get_session)) -> KnowledgeOut:
    row = add_knowledge(session, title=payload.title, content=payload.content,
                        source=payload.source, tags=payload.tags)
    return KnowledgeOut(id=row.id, title=row.title, status=row.status)
