# ADR 0002: Provider-agnostic LLM layer via an OpenAI-compatible adapter

- **Status:** Accepted
- **Date:** 2026-06-25

## Context

NeanderPrompt must work with *any* AI — Claude, GPT, Gemini, GLM, DeepSeek,
Kimi, Grok, Qwen, Llama, and whatever ships next. Writing a bespoke SDK adapter
per vendor would be a maintenance sink.

## Decision

1. Define one narrow interface, `LLMProvider.complete()` (`services/llm/base.py`).
2. Observe that most vendors (DeepSeek, GLM/Z.AI, Kimi/Moonshot, Grok/xAI,
   Qwen/DashScope, and OpenAI itself) expose an **OpenAI-compatible** Chat
   Completions API. A single `OpenAICompatibleProvider` covers all of them — only
   `base_url`, `model` and the API key env var change.
3. Keep models as data in `core/model_registry.py`. Adding a model = one
   `ModelCard`. Anthropic and Google get native adapters (different wire format).

Model ids reflect the mid-2026 frontier (cross-checked against the LM Arena /
Chatbot Arena leaderboard) and are treated as editable defaults.

## Consequences

- Supporting a new OpenAI-compatible vendor is a one-line registry entry.
- The rest of the codebase (RAG, judge, drift) never imports a vendor SDK.
- "Antigravity" and similar agentic *clients* are integrated as consumers of
  models, not as `ModelCard`s.

## Alternatives considered

- **One SDK adapter per vendor:** rejected — high maintenance, little benefit
  given API convergence.
- **A heavy framework (LangChain, etc.):** rejected — too much surface area for a
  tool whose value is the *loop*, not the plumbing.
