---
participant-id: agent:codex
participant: codex
role: agent
ticket: ticket-010
---
# Participant: codex (AI agent)

## Understanding

The Founder explicitly requires DSL for every LLM decision. The implementation
will enforce typed request and response documents at the decision boundary,
while preserving NL only as a typed human-source field before translation.

## Execution plan

1. Extend the closed manifest vocabulary and deterministic checker.
2. Add valid and invalid protocol cases to the dependency-free self-test.
3. Validate governance and publish a reviewable PR.

## Actual changes

- Added the closed `llm.decisionProtocol` vocabulary to the manifest schema.
- Enforced strict bidirectional DSL request/response exchange for enabled LLM decisions.
- Added DSL-only, NL-to-DSL and invalid-protocol self-test cases.
- Reconciled completed ticket-009 lifecycle so its stale workstream reservation
  no longer blocks this independent standard change.

## Blockers

- Awaiting independent review and merge.
