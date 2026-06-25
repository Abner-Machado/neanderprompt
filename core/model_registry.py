"""Provider-agnostic model catalog.

NeanderPrompt is meant to work with *any* AI — Claude, GPT, Gemini, GLM,
DeepSeek, Kimi, Grok, Qwen, Llama, Mistral, and whatever ships next. Instead of
hardcoding model names across the codebase, every model lives here as one
editable entry. Adding a new model = appending one ``ModelCard``.

Key design insight (keeps the adapter layer tiny): most providers expose an
**OpenAI-compatible** Chat Completions API. A single ``openai_compatible``
adapter therefore covers DeepSeek, GLM (Z.AI), Kimi (Moonshot), Grok (xAI),
Qwen (Alibaba/DashScope) and most open-weights gateways — only the ``base_url``
and the model id change. Anthropic and Google use their native adapters.

Model ids below reflect the frontier as of mid-2026 (cross-checked against the
LM Arena / Chatbot Arena leaderboard). They are *defaults*, not gospel — update
this file as the field moves. See https://arena.ai/leaderboard and
https://huggingface.co/spaces/lmarena-ai/arena-leaderboard for current names.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ModelCard:
    """One AI model and how to reach it."""

    id: str                       # model id passed to the provider API
    provider: str                 # vendor label, e.g. "deepseek"
    adapter: str                  # which LLMProvider implementation talks to it
    label: str                    # human-friendly name
    context_window: int = 0       # tokens; 0 = unknown/varies
    base_url: str | None = None   # for openai_compatible adapters
    env_key: str | None = None    # env var holding the API key
    open_weights: bool = False
    tags: tuple[str, ...] = field(default_factory=tuple)


# NOTE: "Antigravity" (Google) is an agentic IDE/client, not a model — it
# *consumes* models like Gemini. It is intentionally absent here; integrate it
# as a client, not a ModelCard.
CATALOG: dict[str, ModelCard] = {
    # --- Anthropic (native adapter) ---
    "claude-opus-4-8": ModelCard(
        id="claude-opus-4-8", provider="anthropic", adapter="anthropic",
        label="Claude Opus 4.8", context_window=200_000,
        env_key="ANTHROPIC_API_KEY", tags=("frontier", "reasoning"),
    ),
    "claude-sonnet-4-6": ModelCard(
        id="claude-sonnet-4-6", provider="anthropic", adapter="anthropic",
        label="Claude Sonnet 4.6", context_window=200_000,
        env_key="ANTHROPIC_API_KEY", tags=("balanced",),
    ),
    # --- OpenAI (openai_compatible against the official endpoint) ---
    "gpt-5.5-pro": ModelCard(
        id="gpt-5.5-pro", provider="openai", adapter="openai_compatible",
        label="GPT-5.5 Pro", base_url="https://api.openai.com/v1",
        env_key="OPENAI_API_KEY", tags=("frontier",),
    ),
    # --- Google (native adapter) ---
    "gemini-3.1-pro": ModelCard(
        id="gemini-3.1-pro", provider="google", adapter="gemini",
        label="Gemini 3.1 Pro", context_window=1_000_000,
        env_key="GOOGLE_API_KEY", tags=("frontier", "long-context"),
    ),
    # --- Z.AI / GLM (OpenAI-compatible) ---
    "glm-5": ModelCard(
        id="glm-5", provider="zai", adapter="openai_compatible", label="GLM-5",
        base_url="https://api.z.ai/api/paas/v4", env_key="ZAI_API_KEY",
        tags=("frontier",),
    ),
    # --- DeepSeek (OpenAI-compatible) ---
    "deepseek-v4.1": ModelCard(
        id="deepseek-chat", provider="deepseek", adapter="openai_compatible",
        label="DeepSeek V4.1", base_url="https://api.deepseek.com/v1",
        env_key="DEEPSEEK_API_KEY", open_weights=True, tags=("frontier", "value"),
    ),
    # --- Moonshot / Kimi (OpenAI-compatible) ---
    "kimi-k2": ModelCard(
        id="kimi-k2", provider="moonshot", adapter="openai_compatible",
        label="Kimi K2", base_url="https://api.moonshot.ai/v1",
        env_key="MOONSHOT_API_KEY", tags=("long-context",),
    ),
    # --- xAI / Grok (OpenAI-compatible) ---
    "grok-4": ModelCard(
        id="grok-4", provider="xai", adapter="openai_compatible", label="Grok 4",
        base_url="https://api.x.ai/v1", env_key="XAI_API_KEY", tags=("frontier",),
    ),
    # --- Alibaba / Qwen (OpenAI-compatible via DashScope) ---
    "qwen3-max": ModelCard(
        id="qwen3-max", provider="alibaba", adapter="openai_compatible",
        label="Qwen3 Max",
        base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        env_key="DASHSCOPE_API_KEY", open_weights=True, tags=("open-weights",),
    ),
    # --- Offline deterministic provider: demo + tests, no network/keys ---
    "echo-1": ModelCard(
        id="echo-1", provider="local", adapter="echo", label="Echo (offline)",
        tags=("offline", "deterministic", "testing"),
    ),
}


def get_model(model_id: str) -> ModelCard:
    try:
        return CATALOG[model_id]
    except KeyError as exc:  # pragma: no cover - guard
        raise KeyError(
            f"Unknown model '{model_id}'. Known: {', '.join(sorted(CATALOG))}"
        ) from exc


def list_models() -> list[ModelCard]:
    return list(CATALOG.values())
