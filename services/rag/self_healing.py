"""Self-Healing RAG — the closed loop.

    ask -> retrieve -> answer -> judge
                          |          |
                  (low confidence)   |
                          v          |
                     diagnose -> rewrite strategy -> retry
                          |
                  (confidence ok after a heal)
                          v
                 persist winning strategy as a Skill  (learned, permanent)

Everything is logged to ``query_logs`` for closed-loop observability, so a
developer can always answer "why did this query fail, and what fixed it?".

Learned skills are keyed by a query *signature* so that similar future questions
start from the healed strategy instead of repeating the trial-and-error.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.config import get_settings
from models.orm import QueryLog, Skill
from services.llm.base import LLMProvider, Message
from services.rag.diagnose import diagnose
from services.rag.judge import HeuristicJudge
from services.rag.store import retrieve
from services.rag.strategy import RetrievalStrategy
from utils.text import signature

_ANSWER_PROMPT = (
    "You are a knowledge assistant. Answer the QUESTION using only the CONTEXT "
    "below. If the context is insufficient, say so plainly.\n\nCONTEXT:\n{context}"
)


@dataclass
class HealResult:
    answer: str
    confidence: float
    healed: bool
    attempts: int
    diagnosis: str
    trace: list[dict] = field(default_factory=list)
    used_skill: bool = False


class SelfHealingRAG:
    def __init__(self, session: Session, provider: LLMProvider, judge=None) -> None:
        self.session = session
        self.provider = provider
        self.judge = judge or HeuristicJudge()
        self.settings = get_settings()

    # -- public API -------------------------------------------------------
    def ask(self, query: str) -> HealResult:
        threshold = self.settings.confidence_threshold
        strategy, used_skill = self._initial_strategy(query)

        trace: list[dict] = []
        diagnosis_label = ""
        best_answer, best_conf = "", 0.0

        for attempt in range(self.settings.max_heal_attempts + 1):
            chunks = retrieve(self.session, query, strategy)
            answer = self._generate(query, chunks)
            verdict = self.judge.score(query, answer, chunks)

            trace.append({
                "attempt": attempt,
                "strategy": strategy.as_dict(),
                "n_chunks": len(chunks),
                "confidence": verdict.confidence,
                "reason": verdict.reason,
            })

            if verdict.confidence >= best_conf:
                best_answer, best_conf = answer, verdict.confidence

            if verdict.confidence >= threshold:
                healed = attempt > 0
                if healed:
                    self._remember_skill(query, strategy, diagnosis_label)
                self._log(query, answer, verdict.confidence, healed, attempt + 1,
                          diagnosis_label, trace)
                return HealResult(answer, verdict.confidence, healed, attempt + 1,
                                  diagnosis_label, trace, used_skill)

            # Confidence too low -> dispatch the diagnostic subagent.
            d = diagnose(query, chunks, verdict, strategy)
            diagnosis_label = d.label
            trace[-1]["diagnosis"] = d.label
            strategy = d.strategy

        # Exhausted heal attempts: return the best we got, fully logged.
        self._log(query, best_answer, best_conf, False,
                  self.settings.max_heal_attempts + 1, diagnosis_label, trace)
        return HealResult(best_answer, best_conf, False,
                          self.settings.max_heal_attempts + 1, diagnosis_label,
                          trace, used_skill)

    # -- internals --------------------------------------------------------
    def _generate(self, query: str, chunks) -> str:
        context = "\n".join(f"- {c.content}" for c in chunks) or "(no context)"
        out = self.provider.complete([
            Message("system", _ANSWER_PROMPT.format(context=context)),
            Message("user", query),
        ])
        return out.text

    def _initial_strategy(self, query: str) -> tuple[RetrievalStrategy, bool]:
        sig = signature(query)
        skill = self.session.execute(
            select(Skill).where(Skill.pattern == sig)
        ).scalar_one_or_none()
        if skill:
            skill.hits += 1
            self.session.commit()
            return RetrievalStrategy.from_dict(skill.strategy), True
        return RetrievalStrategy(), False

    def _remember_skill(self, query: str, strategy: RetrievalStrategy, label: str) -> None:
        sig = signature(query)
        existing = self.session.execute(
            select(Skill).where(Skill.pattern == sig)
        ).scalar_one_or_none()
        if existing:
            existing.strategy = strategy.as_dict()
            existing.note = f"healed via {label}"
        else:
            self.session.add(Skill(
                pattern=sig, strategy=strategy.as_dict(), note=f"healed via {label}",
            ))
        self.session.commit()

    def _log(self, query, answer, confidence, healed, attempts, diagnosis, trace) -> None:
        self.session.add(QueryLog(
            query=query, answer=answer, model=getattr(self.provider, "name", "?"),
            confidence=confidence, healed=healed, attempts=attempts,
            diagnosis=diagnosis, trace=trace,
        ))
        self.session.commit()
