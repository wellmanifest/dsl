# Ticket 010: Require DSL at every LLM decision boundary

- **ID**: ticket-010
- **Owner**: Founder request via Codex conversation
- **Status**: IN_PROGRESS
- **Workflow state**: VALIDATION
- **Created**: 2026-08-26

## Goal and scope

Require every LLM decision boundary to exchange a strict, named DSL request and
response. Natural language is permitted only as a human-originated field inside
the declared input schema and must be translated to the decision DSL before a
model decision is accepted.

This ticket changes the reusable DSL contract and deterministic checker only.
It does not migrate adopters, change provider routing, grant execution
authority, or make a model output trusted.

## Acceptance criteria

- [x] AC-01: Founder approved the scope in the Codex conversation on 2026-08-26.
- [x] AC-02: A manifest declares whether its LLM boundary is DSL-only or NL-to-DSL.
- [x] AC-03: The checker rejects enabled decision boundaries without strict bidirectional DSL schemas.
- [x] AC-04: Self-test covers valid DSL-only, valid NL-to-DSL, and invalid protocol cases.

## Validation evidence

- `python3 src/dsl_check.py self-test` passed.
- `python3 src/dsl_check.py validate profiles/dsl-manifest.json` passed.
- `python3 src/dsl_check.py standards profiles/dsl-manifest.json` passed.
- `./project/governance-check.sh --actor agent` passed with zero errors and warnings.

## Participants

- Human participant: Founder approved the scope through the trusted conversation boundary; no user-* file was created.
- Agent participant: [ai-codex.md](ai-codex.md)
