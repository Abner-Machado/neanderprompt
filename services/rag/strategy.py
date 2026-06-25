"""The retrieval strategy — the thing the self-healing loop mutates and learns.

Every knob the diagnostic subagent can turn lives here. A healed strategy that
beats the confidence threshold is serialised (``as_dict``) and stored as a
``Skill`` so future similar queries start from it instead of the default.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class RetrievalStrategy:
    top_k: int = 3                       # how many chunks to retrieve
    min_score: float = 0.05              # drop chunks below this lexical score
    expand_terms: list[str] = field(default_factory=list)  # extra query terms
    rewrite: str | None = None           # full query rewrite, if any

    def as_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict | None) -> "RetrievalStrategy":
        if not data:
            return cls()
        known = {f: data[f] for f in cls().__dict__ if f in data}
        return cls(**known)
