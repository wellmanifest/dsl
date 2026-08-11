# Ticket 004: Reconcile repository status and intent evidence

- **ID**: ticket-004
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: VALIDATION
- **Created**: 2026-08-11

## Goal and scope

Reconcile the public repository status and roadmap with the implementation that
is already merged on `main`, add release traceability to the root changelog, and
record both deterministic and LLM-enriched `todo2code` audits without rewriting
historical ticket evidence.

The change is documentation-only. It does not implement the pending domain
profiles, adoption guide, or protected `dsl_check.py gate` integration. Those
items remain future, separately scoped work.

## Acceptance criteria

- [x] AC-01: `README.md` describes the implemented `0.1.0-dev` baseline rather
  than the obsolete `WAIT_FOR_APPROVAL` state.
- [x] AC-02: `CHANGELOG.md` links the completed standard and CI work to their
  tickets, pull requests, and merge commits.
- [x] AC-03: `TODO.md` separates the active documentation reconciliation from
  unscheduled roadmap items and does not claim that future implementation is
  already authorized.
- [x] AC-04: Historical ticket evidence remains append-only and no human-owned
  participant file is created or edited by the agent.
- [x] AC-05: Governance, Docker self-tests, and deterministic plus six-stage
  LLM `todo2code` reruns complete with all remaining findings classified.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)

## Authorization

The user answered `tak` after reviewing the audit findings and the proposed
two-repository cleanup. This is session execution authorization for the bounded
paths in `intent.json`; it is not trusted merge approval.

## Validation evidence

- Local and networkless Docker governance: PASS (`0 errors, 0 warnings`).
- Networkless DSL self-test: PASS.
- Markdown local-link scan: PASS (26 references).
- `git diff --check`: PASS.
- Deterministic `todo2code` full-history run
  `20260811T155910Z-b630e6c7`: succeeded, graph
  `c67346218fb9ccd77bf3c10eb80948d1dc8d8049d13ab9831ed2f5e50bae12c0`,
  zero blocking diagnostics, and no LLM use.
- Scoped LLM-first run `20260811T163154Z-6eb2ad43`: all six semantic LLM
  stages used `z-ai/glm-5.2`; status `degraded` only because the configured
  documentation budget covered 12 of 19 chunks; no pipeline failure.
- The five LLM-run blocking diagnostics were classified as todo2code
  same-source extraction defects: each pair interpreted identical or
  overlapping lines as opposing independent evidence. They do not establish a
  repository intent conflict and are tracked by todo2code ticket-069.

## Remaining publication state

The bounded change is locally validated. On 2026-08-11 the user separately
authorized its commit and branch push. Pull request creation, trusted review,
and merge remain unfinished and are not authorized by that request.
