"""Anti-AI Drift — consensus across multiple models.

When several AIs answer the same question they disagree (Claude says A, DeepSeek
says B, ...). This computes a lightweight consensus + a confidence score from
lexical agreement, so you can see where models converge and where they diverge,
instead of trusting one blindly.

Real (model-backed) usage: pass providers built from the registry. Offline:
pass the echo provider for each to exercise the logic deterministically.
"""
from __future__ import annotations

from dataclasses import dataclass

from services.llm.base import LLMProvider, Message
from utils.text import jaccard


@dataclass
class DriftReport:
    answers: dict[str, str]   # model name -> answer
    consensus: str            # the answer most agreed-with by the others
    agreement: float          # 0..1 mean pairwise lexical agreement
    diverging: list[str]      # models whose answer is an outlier


def compare(question: str, providers: dict[str, LLMProvider],
            *, divergence_threshold: float = 0.3) -> DriftReport:
    answers = {
        name: p.complete([Message("user", question)]).text
        for name, p in providers.items()
    }
    names = list(answers)

    # Each model's centrality = mean agreement with every other model.
    centrality: dict[str, float] = {}
    for a in names:
        others = [jaccard(answers[a], answers[b]) for b in names if b != a]
        centrality[a] = sum(others) / len(others) if others else 1.0

    consensus_model = max(centrality, key=centrality.get) if names else ""
    agreement = round(sum(centrality.values()) / len(centrality), 3) if centrality else 0.0
    diverging = [n for n, c in centrality.items() if c < divergence_threshold]

    return DriftReport(answers, answers.get(consensus_model, ""), agreement, diverging)
