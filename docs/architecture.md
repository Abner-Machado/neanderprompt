# Architecture

NeanderPrompt is a small FastAPI service over a SQLAlchemy data layer. It runs
on SQLite with zero setup and on PostgreSQL in production — the same code, no
driver imports leaking into business logic.

```
                         ┌──────────────────────────────┐
   HTTP (FastAPI)  ────►  │            api/routes         │
                         └───────────────┬──────────────┘
                                         │
                         ┌───────────────▼──────────────┐
                         │           services/           │
                         │  rag/ (self-healing loop)     │
                         │  decisions, decay, drift,     │
                         │  genome, llm/ (providers)     │
                         └───────────────┬──────────────┘
                                         │
                ┌────────────────────────┼────────────────────────┐
                │                         │                        │
        ┌───────▼──────┐        ┌─────────▼────────┐      ┌────────▼───────┐
        │ core/        │        │ models/orm.py    │      │ core/          │
        │ model_registry│       │ (SQLAlchemy)     │      │ db (SQLite/PG) │
        └──────────────┘        └──────────────────┘      └────────────────┘
```

## Folders

| Folder      | Responsibility                                                        |
|-------------|----------------------------------------------------------------------|
| `app/`      | FastAPI entrypoint and wiring.                                        |
| `api/`      | HTTP routes (thin — they call services).                             |
| `core/`     | Settings, DB engine, and the provider-agnostic **model registry**.   |
| `services/` | The actual logic: the self-healing RAG loop, decisions, decay, drift, genome, and the LLM provider adapters. |
| `models/`   | SQLAlchemy ORM tables.                                                |
| `schemas/`  | Pydantic request/response shapes.                                    |
| `utils/`    | Dependency-free text helpers (tokenizing, lexical overlap).          |
| `tests/`    | Pytest suite (runs fully offline, in-memory).                        |
| `examples/` | Runnable demo of the self-healing loop.                              |

## Design principles

- **Provider-agnostic.** Everything talks to models through one `LLMProvider`
  interface; concrete vendors live behind it. See
  [ADR 0002](adr/0002-provider-agnostic-via-openai-compatible.md).
- **Runs offline.** The `echo` provider + lexical retrieval mean the whole
  system (and its tests) work with no API keys and no Docker.
- **Swap-friendly.** Lexical retrieval and the heuristic judge are isolated so
  they can be replaced by embeddings / an LLM judge without touching the loop.
