"""Self-Healing RAG, end to end, with zero external services.

    python examples/demo.py

Uses an in-memory database and the offline "echo" model, so it runs anywhere.
Watch the loop detect a low-confidence answer, diagnose it, heal, and learn a
Skill that a similar later query reuses for free.
"""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.orm import Base
from services.llm.echo import EchoProvider
from services.rag.self_healing import SelfHealingRAG
from services.rag.store import add_knowledge

DOC = (
    "FastAPI was selected as the web layer. It provides async endpoints, "
    "dependency injection, pydantic validation and automatically generated "
    "openapi documentation for every published service across our backend stack "
    "running in production."
)


def main() -> None:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool, future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False, future=True)()

    add_knowledge(session, title="Backend choice", content=DOC, tags=["backend"])
    rag = SelfHealingRAG(session, provider=EchoProvider())

    print("=" * 72)
    print("Q1: Why choose FastAPI framework?")
    r1 = rag.ask("Why choose FastAPI framework?")
    for step in r1.trace:
        print(f"  attempt {step['attempt']}: conf={step['confidence']:.2f} "
              f"chunks={step['n_chunks']} min_score={step['strategy']['min_score']:.2f} "
              f"{step.get('diagnosis', '-')}")
    print(f"  -> answer: {r1.answer.strip()}")
    print(f"  -> healed={r1.healed} confidence={r1.confidence} diagnosis={r1.diagnosis}")

    print("=" * 72)
    print("Q2: similar question -> should reuse the learned Skill, no healing")
    r2 = rag.ask("Why would we choose the FastAPI framework here?")
    print(f"  -> used_skill={r2.used_skill} healed={r2.healed} "
          f"attempts={r2.attempts} confidence={r2.confidence}")
    print("=" * 72)


if __name__ == "__main__":
    main()
