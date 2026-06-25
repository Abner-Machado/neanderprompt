# Self-Healing RAG

> The frustration this kills: when RAG returns a bad answer, you rarely know
> *why* — bad chunking? embedding miss? the reranker dropped the right doc? You
> tweak blindly and retry. NeanderPrompt closes the loop and makes the failure,
> and the fix, observable and **permanent**.

## The loop

```
ask ─► retrieve ─► answer ─► judge (LLM-as-judge / heuristic)
                                │
                  confidence ≥ threshold? ──► return + log
                                │ no
                                ▼
                   diagnostic subagent
              (no_documents | low_relevance | weak_synthesis)
                                │
                  rewrite retrieval strategy ─► retry
                                │
                  healed successfully?
                                │ yes
                                ▼
                save winning strategy as a SKILL  (learned, permanent)
```

Every attempt is written to `query_logs` with its strategy, chunk count,
confidence and the diagnosis label — closed-loop observability you can query.

## Components

| Piece | File | What it does |
|-------|------|--------------|
| Engine | `services/rag/self_healing.py` | Orchestrates ask → judge → diagnose → retry → learn. |
| Judge | `services/rag/judge.py` | `LLM-as-judge` (production) or `HeuristicJudge` (offline). Scores groundedness + relevance. |
| Diagnostic subagent | `services/rag/diagnose.py` | Classifies the failure and mutates the retrieval strategy. |
| Strategy | `services/rag/strategy.py` | The knobs (top_k, min_score, expanded terms, rewrite) — what gets learned. |
| Store | `services/rag/store.py` | Retrieval (lexical today, embeddings later). |
| Skill | `models/orm.py::Skill` | The learned strategy, keyed by query signature, reused automatically. |

## Diagnoses

- **`no_documents`** — retrieval was too strict / vocabulary mismatch → widen
  recall (lower `min_score`, raise `top_k`, expand terms).
- **`low_relevance`** — docs came back but none really match → expand the query.
- **`weak_synthesis`** — relevant docs exist but the answer ignored them → feed
  more context.

## Why a "Skill"

A heal that worked is institutional memory. Instead of re-running trial-and-error
for every similar question, the winning `RetrievalStrategy` is stored under the
query's *signature* (its salient terms) and applied up front next time. This is
the bridge to NeanderPrompt's thesis: **knowledge — even operational knowledge
about how to retrieve knowledge — should be captured and reused, not lost.**

## Going from offline to real models

The demo uses the deterministic `echo` provider and a heuristic judge so it runs
with no keys. In production:

```python
from services.llm.factory import build_provider
from services.rag.judge import LLMJudge
from services.rag.self_healing import SelfHealingRAG

provider = build_provider("deepseek-v4.1")        # any registry id
engine = SelfHealingRAG(session, provider, judge=LLMJudge(provider))
```

Swap lexical retrieval for embeddings behind `services/rag/store.py` and the loop
is unchanged.
