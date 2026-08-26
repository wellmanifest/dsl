# Ticket 009: Lock Code DSL standard into standardsLock

- **ID**: ticket-009
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: DONE
- **Created**: 2026-08-24

## Goal and scope

Register and pin the newly published `wellmanifest.code` standard (v0.1.0-dev) at
immutable revision `6d27f5a9eef2be8fc7cfdbd12975dc57bc13778a` inside
`profiles/dsl-manifest.json` `standardsLock` and `mappings`.

## Acceptance criteria

- [x] AC-01: `profiles/dsl-manifest.json` maps `wellmanifest/code-dsl` v0.1.0-dev as `compatible-with`.
- [x] AC-02: `standardsLock.entries` pins `wellmanifest.code` v0.1.0-dev at immutable revision `6d27f5a9eef2be8fc7cfdbd12975dc57bc13778a` with exact schema and proto contract digests.
- [x] AC-03: `python3 src/dsl_check.py validate profiles/dsl-manifest.json` and `standards` pass with 0 errors.
- [x] AC-04: `./project/governance-check.sh --actor agent` reports `GOV-PASS` (0 errors, 0 warnings).

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-gemini.md](ai-gemini.md)

## Authorization

User instructed to continue integration tasks, granting SESSION_EXECUTION_AUTHORIZATION for this bounded standardsLock registration.

## Completion

All four acceptance criteria are evidenced in `ai-gemini-logs.txt`; the ticket
was left active after successful validation and is now closed without changing
its already published standard pin.
