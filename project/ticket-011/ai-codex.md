---
participant-id: agent:codex
participant: codex
role: agent
ticket: ticket-011
---
# Participant: codex (AI agent)

## Understanding

The old adopted package treats repository ticket status as terminal truth. PR
#17 is already protectedly merged, but its required `IN_PROGRESS / PUBLICATION`
projection therefore blocks the next integration ticket. `new-project 0.20.2`
contains the managed, clone-external terminal receipt resolver and a published
immutable package, so an exact upgrade is the bounded remediation. Its newer
worktree layout is inventory-only for existing legacy checkouts; this task does
not move or delete them.

## Execution plan

1. Run a write-free adoption preflight for the exact published source SHA.
2. Review all managed changes and preserve target-owned extensions.
3. Apply the explicit upgrade, record PR #17's terminal receipt outside Git,
   and prove ticket-010 resolves as inactive.
4. Run package drift, host, Docker and exact-range governance checks.
5. Publish only through protected Validator and retain no closure-only delta.

## Actual changes

- Adopted the complete managed `new-project 0.20.2` package at its published
  merge SHA while preserving DSL-owned manifest and required-check extensions.
- Activated the host contract and verified the Worktrees v4 canonical path.
- Pinned the adoption-bound Docker base by immutable digest and explicitly
  represented the existing legacy governance job in the transition contract.
- Recorded the protected PR #17 terminal receipt outside Git; ticket-010 now
  resolves inactive without changing its historical projection.

## Blockers

- None.
