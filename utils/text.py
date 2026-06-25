"""Small, dependency-free text helpers.

Deliberately simple lexical tooling: enough to make retrieval and the heuristic
judge work offline and deterministically. Swap in real embeddings later behind
the same functions (see docs/roadmap.md).
"""
from __future__ import annotations

import re

_TOKEN = re.compile(r"[a-z0-9]+")
_STOP = {
    "the", "a", "an", "of", "to", "in", "is", "are", "and", "or", "for", "on",
    "with", "why", "how", "what", "do", "we", "use", "using", "did", "does",
}


def tokens(text: str) -> list[str]:
    return [t for t in _TOKEN.findall(text.lower()) if t not in _STOP]


def token_set(text: str) -> set[str]:
    return set(tokens(text))


def jaccard(a: str, b: str) -> float:
    """Lexical overlap in [0, 1]."""
    ta, tb = token_set(a), token_set(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def signature(query: str, n: int = 3) -> str:
    """A stable fingerprint of a query's salient tokens.

    Used as the key under which a learned Skill is stored/looked up, so that
    *similar* queries reuse the same healed strategy. We keep the ``n`` longest
    tokens (longer ~= more specific), which is robust to short filler words a
    paraphrase might add or drop ("here", "the", "would").
    """
    salient = sorted(set(tokens(query)), key=lambda t: (-len(t), t))[:n]
    return "|".join(sorted(salient))
