from __future__ import annotations

from fastapi import APIRouter

from core.config import get_settings
from core.model_registry import list_models

router = APIRouter(tags=["meta"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "app": get_settings().app_name}


@router.get("/models")
def models() -> list[dict]:
    return [
        {"id": m.id, "provider": m.provider, "label": m.label,
         "adapter": m.adapter, "open_weights": m.open_weights, "tags": list(m.tags)}
        for m in list_models()
    ]
