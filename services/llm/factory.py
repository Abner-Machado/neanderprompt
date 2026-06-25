"""Resolve a model id into a ready-to-use provider instance."""
from __future__ import annotations

from core.model_registry import ModelCard, get_model
from services.llm.base import LLMProvider
from services.llm.echo import EchoProvider
from services.llm.openai_compatible import OpenAICompatibleProvider


def build_provider(model_id: str) -> LLMProvider:
    card: ModelCard = get_model(model_id)

    if card.adapter == "echo":
        return EchoProvider(model=card.id)

    if card.adapter == "openai_compatible":
        assert card.base_url, f"{card.id} needs a base_url"
        return OpenAICompatibleProvider(model=card.id, base_url=card.base_url, env_key=card.env_key)

    # Native adapters for Anthropic and Gemini are scaffolded but not yet wired
    # (see docs/roadmap.md). They follow the same LLMProvider contract.
    if card.adapter in {"anthropic", "gemini"}:
        raise NotImplementedError(
            f"Adapter '{card.adapter}' is on the roadmap. "
            f"Use an openai_compatible model or 'echo-1' for now."
        )

    raise ValueError(f"Unknown adapter '{card.adapter}' for model '{model_id}'.")
