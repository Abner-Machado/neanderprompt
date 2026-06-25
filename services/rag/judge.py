"""LLM-as-judge confidence scoring.

Two interchangeable judges behind one ``score`` signature:

* ``HeuristicJudge`` — offline, deterministic. Confidence = how well the answer
  is grounded in the retrieved context (and that any context was retrieved at
  all). Used by default and in tests; no network.
* ``LLMJudge`` — asks a configured model to rate groundedness 0-1. Use in
  production by passing a real provider.

Both return a ``Verdict`` so the self-healing engine treats them identically.
"""
from __future__ import annotations

from dataclasses import dataclass

from services.llm.base import LLMProvider, Message
from services.rag.store import Chunk
from utils.text import jaccard


@dataclass
class Verdict:
    confidence: float  # 0..1
    reason: str


class HeuristicJudge:
    def score(self, query: str, answer: str, chunks: list[Chunk]) -> Verdict:
        if not chunks:
            return Verdict(0.0, "no context retrieved")
        if not answer.strip() or answer.lower().startswith("i don't have"):
            return Verdict(0.1, "answer not grounded in context")
        context = " ".join(c.content for c in chunks)
        grounded = jaccard(answer, context)
        relevant = max(c.score for c in chunks)
        # Groundedness (is the answer actually supported by retrieved text?) is
        # the stronger RAG signal, so it carries more weight than raw relevance.
        confidence = round(0.7 * grounded + 0.3 * relevant, 3)
        return Verdict(confidence, f"grounded={grounded:.2f} top_chunk={relevant:.2f}")


class LLMJudge:
    _PROMPT = (
        "You are a strict RAG evaluator. Given a QUESTION, the retrieved CONTEXT "
        "and a candidate ANSWER, reply with a single float 0..1 = how well the "
        "answer is supported by the context. Reply with only the number."
    )

    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    def score(self, query: str, answer: str, chunks: list[Chunk]) -> Verdict:
        context = "\n".join(f"- {c.content}" for c in chunks) or "(none)"
        out = self.provider.complete([
            Message("system", self._PROMPT),
            Message("user", f"QUESTION: {query}\nCONTEXT:\n{context}\nANSWER: {answer}"),
        ])
        try:
            value = float(out.text.strip().split()[0])
        except (ValueError, IndexError):
            value = 0.0
        return Verdict(max(0.0, min(1.0, value)), "llm-judge")
