<p align="center">
  <img src="docs/banner.png" alt="NeanderPrompt — turning experience into knowledge" width="100%">
</p>

<h1 align="center">NeanderPrompt</h1>

<p align="center">
  <strong>Infrastructure for preserving, evolving and sharing knowledge — human and artificial.</strong><br>
  <em>Tools come and go. The knowledge they produce shouldn't.</em>
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-0.110%2B-009688?logo=fastapi&logoColor=white">
  <img alt="PostgreSQL" src="https://img.shields.io/badge/PostgreSQL-optional-336791?logo=postgresql&logoColor=white">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-green">
  <img alt="Tests" src="https://img.shields.io/badge/tests-11%20passing-brightgreen">
</p>

---

## What this is

NeanderPrompt is **not** a prompt collection, an MCP list, or an automation dump.

It is a system for treating knowledge as a first-class, versionable, evolving
asset — capturing not just *what* was created, but *why*, *how it evolved*, and
*what results it produced*. Human experience and AI output collaborate and
compound instead of evaporating when the next tool arrives.

> The knowledge that isn't shared is lost. Let's turn knowledge into legacy.

It is **model-agnostic by design**: Claude, GPT, Gemini, GLM, DeepSeek, Kimi,
Grok, Qwen, Llama — current or future — all plug in through one interface. (See
[why and how](docs/adr/0002-provider-agnostic-via-openai-compatible.md).)

---

## Quickstart (60 seconds, no Docker, no API keys)

```bash
git clone https://github.com/BjornBigornaDev/neanderprompt.git && cd neanderprompt
python -m venv .venv
source .venv/bin/activate          # macOS / Linux
# .venv\Scripts\activate           # Windows (PowerShell)
pip install -r requirements.txt

# See the Self-Healing RAG loop heal a failing query and learn a Skill:
PYTHONPATH=. python examples/demo.py

# Run the test suite (fully offline, in-memory):
pytest -q

# Run the API:
uvicorn app.main:app --reload     # http://localhost:8000/docs
```

The defaults use SQLite and an offline deterministic model, so everything runs
anywhere. PostgreSQL + Docker is available for production (`docker compose up`),
but never required for development.

---

## The flagship: Self-Healing RAG ✅

**The problem every RAG developer knows:** an answer comes back wrong and you
have no idea why — bad chunking? embedding miss? the reranker dropped the right
document? So you tweak blindly and retry. Forever.

**What NeanderPrompt does instead** — a closed observability loop:

```
ask ─► retrieve ─► answer ─► judge (LLM-as-judge)
                               │ low confidence?
                               ▼
                   diagnostic subagent
        (no_documents | low_relevance | weak_synthesis)
                               │
              rewrites the retrieval strategy ─► retries
                               │ healed?
                               ▼
             saves the winning strategy as a SKILL (permanent)
```

Every attempt is logged with its strategy, chunk count, confidence and
diagnosis — so "why did this fail, and what fixed it?" is always answerable. And
when a fix works, it's **learned**: the next similar query reuses it for free.

Real output from `examples/demo.py`:

```
Q1: Why choose FastAPI framework?
  attempt 0: conf=0.00 chunks=0 min_score=0.05 no_documents
  attempt 1: conf=0.71 chunks=1 min_score=0.00 -
  -> healed=True confidence=0.71 diagnosis=no_documents

Q2: similar question -> should reuse the learned Skill, no healing
  -> used_skill=True healed=False attempts=1 confidence=0.709
```

Details: [docs/self-healing-rag.md](docs/self-healing-rag.md).

---

## The six pillars

NeanderPrompt ships **one pillar fully live and tested**, and the rest as honest,
designed foundations — real interfaces and tables, minimal logic, a clear path
([roadmap](docs/roadmap.md)). A working closed loop beats six half-features.

| Pillar | Idea | Status |
|--------|------|--------|
| **Self-Healing RAG** | Detect low confidence → diagnose → heal → learn a Skill. | ✅ Live & tested |
| **Decision Registry** | Record *why* — "Why FastAPI?", "Why we dropped Node?" Projects die without this. | ✅ Live |
| **Knowledge Decay Prevention** | Flag knowledge unused for too long as `review` / obsolete; detect dead deps. | ✅ Minimal |
| **Anti-AI Drift** | When Claude says A, DeepSeek says B, Gemini says C — compute consensus, divergence, confidence. | ✅ Minimal |
| **Knowledge Genome** | Give each asset a "DNA" (components) and surface hidden connections as a graph. | 🚧 Designed |
| **Life Knowledge Layer** | Failures and lessons (business, finance, marketing) as versionable assets that inform answers. | 🚧 Schema ready |

### Life Knowledge Layer — the heart of it

The point isn't just code. Lived experience is knowledge too:

```yaml
title: Failed to sell a course
year: 2025
cause:   [poor traffic, weak offer]
lesson:  [validate before producing]
impact:  saved 3 future months
```

These become searchable, versionable assets that feed back into answers — so the
system gets wiser, not just bigger.

---

## Works with any AI

Models live as data in [`core/model_registry.py`](core/model_registry.py) — one
entry per model. The key insight: most providers expose an **OpenAI-compatible**
API, so a single adapter covers DeepSeek, GLM (Z.AI), Kimi (Moonshot), Grok
(xAI), Qwen (DashScope) and OpenAI; Anthropic and Google get native adapters.

```python
from services.llm.factory import build_provider
provider = build_provider("deepseek-v4.1")   # or "glm-5", "grok-4", "claude-opus-4-8"...
```

Adding a new AI = appending one `ModelCard`. The offline `echo-1` model needs no
key and powers the demo and tests. Model ids track the mid-2026 frontier
(cross-checked against the [LM Arena leaderboard](https://arena.ai/leaderboard))
and are editable defaults — update them as the field moves.

> Note: agentic *clients* like Google **Antigravity** consume models (e.g.
> Gemini); they integrate as consumers, not as model entries.

---

## Project layout

```
app/         FastAPI entrypoint            models/    SQLAlchemy tables
api/         HTTP routes                   schemas/   Pydantic shapes
core/        config, DB, model registry    utils/     text helpers
services/    the logic (rag/, llm/, ...)   tests/     offline test suite
docs/        architecture, ADRs, roadmap   examples/  runnable demo
```

See [docs/architecture.md](docs/architecture.md).

---

## API

| Method | Path | Purpose |
|--------|------|---------|
| `GET`  | `/health` | Liveness. |
| `GET`  | `/models` | List the model registry. |
| `POST` | `/knowledge` | Store a knowledge asset. |
| `POST` | `/rag/ask` | Ask — runs the self-healing loop, returns answer + trace. |
| `POST` | `/decisions` | Record a decision (Decision Registry). |
| `GET`  | `/decisions` | List recorded decisions. |

Interactive docs at `/docs` when the server is running.

---

## Tech

Python · FastAPI · SQLAlchemy (SQLite → PostgreSQL) · Pydantic · httpx · Docker
(optional) · pytest. No heavyweight LLM framework — the value is the *loop*, not
the plumbing.

---

## Status & contributing

Early but real: the flagship loop works and is tested (11 passing). The
[roadmap](docs/roadmap.md) is explicit about what's live vs. designed.
Contributions welcome — especially embeddings retrieval, native Anthropic/Gemini
adapters, and the Knowledge Genome graph.

## Built with

NeanderPrompt is designed and maintained by a human, with AI as creation support
— fittingly, since the project itself is about humans and AIs producing knowledge
together:

- **Claude** (Anthropic) — architecture, the Self-Healing RAG loop, tests.
- **Codex** (OpenAI) — coding support.

Direction, decisions and review are human. The AIs amplify; they don't decide.

## License

MIT — see [LICENSE](LICENSE).

<p align="center"><em>"We still use primitive tools, but we build the future with them." — NeanderPrompt 🗿</em></p>
