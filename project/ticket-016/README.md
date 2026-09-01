# Ticket 016: Respect terminal merge receipts in DSL CI

- **ID**: ticket-016
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-09-01

## Goal and scope

Keep exact-range ticket governance on reviewable pull-request, review and
non-default heads. On the protected default branch, consume the terminal merge
receipt and run host/profile/networkless-container tests without replaying the
already merged ticket approval. Apply the same boundary on Linux and Windows.

## Acceptance criteria

- [x] AC-01: GitHub issue #32 and the user's instruction to close all tasks
      authorize this bounded CI correction.
- [x] AC-02: A protected default-branch event runs host, profile and
      networkless-container tests without replaying ticket governance.
- [x] AC-03: Pull-request, review and non-default heads retain exact
      `base..head` governance on Linux, Windows and Docker; no carrier-only
      `project/TICKETS.md` projection remains.
- [x] AC-04: Actionlint, simulated terminal/range boundary checks, exact
      governance and networkless Docker validation pass before protected merge.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
