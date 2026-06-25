# Roadmap

NeanderPrompt ships one pillar **live** and the rest as honest, designed
foundations (real interfaces, real tables, minimal logic, clear next steps).
This is deliberate: a working closed loop beats six half-features.

## Status

| Pillar | Status | Where |
|--------|--------|-------|
| **Self-Healing RAG** | ✅ Live & tested | `services/rag/` |
| **Decision Registry** | ✅ Live | `services/decisions.py` |
| **Knowledge Decay Prevention** | ✅ Minimal (age-based flag) | `services/decay.py` |
| **Anti-AI Drift** (multi-model consensus) | ✅ Minimal (lexical consensus) | `services/drift.py` |
| **Knowledge Genome** (DNA graph) | 🚧 Designed stub (tag graph) | `services/genome.py` |
| **Life Knowledge Layer** | 🚧 Schema ready (`LifeLesson` table) | `models/orm.py` |

## Next

### Retrieval
- Replace lexical retrieval with embeddings (pgvector) behind `store.py`.
- Hybrid retrieval (BM25 + vectors) and a real cross-encoder reranker; surface
  reranker drops to the diagnostic subagent.

### Judge & diagnosis
- Wire `LLMJudge` by default in production; calibrate the threshold.
- Model-backed diagnostic subagent (let an LLM propose the strategy rewrite,
  validated against the deterministic rules as a safety net).

### Providers
- Native `anthropic` and `gemini` adapters (registry entries already exist).
- Streaming + token/cost accounting per provider.

### Decay
- Dead-dependency detection, "technology changed" signals, auto-revalidation by
  re-running the asset through the self-healing loop.

### Genome
- Extract components from content (not just tags), weighted edges, dead-cluster
  detection; back it with a real graph store.

### Life Knowledge Layer
- API + retrieval over `LifeLesson` (failures/learnings as versionable assets),
  blended into RAG context so lived experience informs answers.
