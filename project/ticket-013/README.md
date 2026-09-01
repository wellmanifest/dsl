# Ticket 013: Bind exact revisions into container governance

- **ID**: ticket-013
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-09-01

## Goal and scope

Make the networkless Docker governance step validate the same exact base and
head revisions as the host step. GitHub Actions checks pull-request heads out
in detached mode, so changed-path-only invocation can otherwise resolve the
local `main` branch and report false history findings.

## Acceptance criteria

- [x] AC-01: The user's request to continue and close all tasks authorizes this
      bounded infrastructure fix.
- [ ] AC-02: Range mode passes the resolved `BASE_SHA` and `HEAD_SHA` into the
      networkless container governance process.
- [ ] AC-03: Repository mode retains its explicit bounded changed-file check.
- [ ] AC-04: Detached-head regression, exact-range governance, DSL self-tests
      and the networkless Docker check pass.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
