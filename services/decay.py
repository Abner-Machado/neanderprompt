"""Knowledge Decay Prevention.

Stops useful knowledge from silently rotting. A simple, real first pass: flag
assets untouched for longer than ``max_age_days`` as needing review. Future work
(see docs/roadmap.md): dead-dependency detection, "technology changed" signals,
and auto-revalidation via the Self-Healing loop.
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.orm import Knowledge


def scan_for_decay(session: Session, *, max_age_days: int = 365) -> list[Knowledge]:
    """Mark and return knowledge that has gone stale."""
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=max_age_days)
    rows = session.execute(select(Knowledge)).scalars().all()
    stale: list[Knowledge] = []
    for row in rows:
        last_used = row.last_used_at
        if last_used.tzinfo is None:  # SQLite returns naive datetimes
            last_used = last_used.replace(tzinfo=dt.timezone.utc)
        if last_used < cutoff and row.status == "active":
            row.status = "review"
            stale.append(row)
    if stale:
        session.commit()
    return stale
