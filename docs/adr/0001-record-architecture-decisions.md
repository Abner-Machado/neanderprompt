# ADR 0001: Record architecture decisions

- **Status:** Accepted
- **Date:** 2026-06-25

## Context

NeanderPrompt's own thesis is that projects die when the *why* behind decisions
is lost. We should practice it.

## Decision

Every significant architectural choice is recorded as a short ADR in
`docs/adr/`. The same idea is offered to users as a first-class feature — the
**Decision Registry** (`services/decisions.py`).

## Consequences

- New contributors can reconstruct reasoning, not just code.
- The Decision Registry is dogfooded, not theoretical.
