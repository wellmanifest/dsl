# Ticket 011: Adopt new-project 0.20.2 rewritten-merge receipts

- **ID**: ticket-011
- **Owner**: requesting user, represented by the conversation
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-09-01

## Goal and scope

Upgrade the repository-owned governance package from published revision
`a22eb47ca0e7c06ac927d1c0d843eabb798bfadd` (`0.14.0`) to the exact
published revision `e992c86fecb1ca9310dae89172eb6ca31bf5a90e` (`0.20.2`). The
upgrade must install clone-external terminal-receipt resolution so the merged
ticket-010 projection no longer reserves the integration workstream.

This is one atomic standard-adoption transaction. Preserve repository-specific
manifest and required-check extensions, adopt the Worktrees v4 inventory rules
without relocating legacy checkouts, and do not rewrite ticket-010 prose or
create a closure commit.

The governance workstream owns this adoption. Its target extensions add the
exact root `.gitignore` path required by Worktrees v4, declare the existing
legacy governance job during the transition, and pin the adoption-bound Docker
base image. Runtime, schemas, profiles and the existing CI workflow remain
outside this ticket.

## Acceptance criteria

- [x] AC-01: The user's instruction to continue and close all active work
  authorizes this bounded prerequisite remediation.
- [x] AC-02: The adoption lock pins published `0.20.2` at the exact SHA.
- [x] AC-03: A verified external receipt for merged PR #17 releases ticket-010
  without changing repository ticket state.
- [x] AC-04: Host, Docker, package drift and exact-range governance checks pass.
- [ ] AC-05: PR publication is performed only by protected Validator.

## Participants

- Human participant: requesting user, represented by the conversation; no
  `user-*` file was created.
- Agent participant: [ai-codex.md](ai-codex.md)

## Non-goals

- No DSL schema, parser, profile, specification or product-documentation change.
- No repository closure commit and no rewrite of ticket-010.
- No moving, unpublished or locally dirty standard source.
- No deletion, movement or repair of historical worktrees during adoption.

## Validation

- Adoption preflight and post-upgrade drift check: exact published
  `e992c86fecb1ca9310dae89172eb6ca31bf5a90e`, up to date.
- Ticket activity registry: valid; ticket-010 resolves inactive through
  `receipt:github-pr:wellmanifest/dsl:17`.
- Host contract and agent-host gate: PASS; Worktrees v4 plan and filesystem
  validation: PASS.
- DSL `validate`, `standards` and `self-test`: PASS.
- Docker build and networkless image `self-test`: PASS.
- Required-check contract: PASS, including the explicitly declared legacy
  governance job retained until the follow-up infrastructure ticket.
- Standard-pack audit reports seven undeclared packs as advisory findings in
  the configured `audit/baseline` mode; it is not a conformance gate.
