# Ticket 009: Lock Code DSL standard into standardsLock

- **ID**: ticket-009
- **Owner**: unresolved:human
- **Status**: PLAN
- **Workflow state**: WAIT_FOR_APPROVAL
- **Created**: 2026-08-24

## Goal and scope

Register and pin the newly published `wellmanifest.code` standard (v0.1.0-dev) at
immutable revision `6d27f5a9eef2be8fc7cfdbd12975dc57bc13778a` inside
`profiles/dsl-manifest.json` `standardsLock` and `mappings`.

## Acceptance criteria

- [ ] AC-01: `profiles/dsl-manifest.json` maps `wellmanifest/code-dsl` v0.1.0-dev as `compatible-with`.
- [ ] AC-02: `standardsLock.entries` pins `wellmanifest.code` v0.1.0-dev at immutable revision `6d27f5a9eef2be8fc7cfdbd12975dc57bc13778a` with exact schema and proto contract digests.
- [ ] AC-03: `python3 src/dsl_check.py validate profiles/dsl-manifest.json` and `standards` pass with 0 errors.
- [ ] AC-04: `./project/governance-check.sh --actor agent` reports `GOV-PASS` (0 errors, 0 warnings).

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-gemini.md](ai-gemini.md)
