# Ticket 008: Shared DSL command schema pack

- **ID**: ticket-008
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-08-15

## Goal and scope

Extract the command schemas shared identically (modulo `$id` and
DSL-specific URI patterns) by `doql`, `testql`, `vql`, and `nlp2dsl`
into a shared pack under `schemas/commands/` in `wellmanifest/dsl`.

The shared schemas declare the common core (verb, required fields, base
properties). DSL-specific constraints (URI patterns like `^doql://`,
format enums, minLength, optional `file`) remain in the consuming repos
as extensions via `x-adopts` + inline properties.

## SESSION_EXECUTION_AUTHORIZATION

Recorded by `devin` from user message approving Tier 1 with the
condition that semantics must match. Verified: `validate` is 100%
identical; `generate`/`patch`/`query` share a common core with
DSL-specific extensions (URI pattern, format enum, minLength).

## Semantic verification

| Command | Common core | DSL-specific extensions |
|---|---|---|
| `validate` | verb, path | none — 100% identical |
| `generate` | verb, text, out | doql: `text.minLength: 1`; nlp2dsl: `mode` |
| `patch` | verb, target, with_path, file | vql: `target.pattern: ^vql://` |
| `query` | verb, target, file, format | each: `target.pattern: ^<dsl>://`; vql: no `less` in format enum |
| `resolve` | verb, text | doql: optional `file`; both: `text.minLength: 1` |

## Non-adoption decision: VALIDATE

Shared `VALIDATE` is **validate-path** (`verb` + `path`), adopted by
`doql` / `testql` / `vql`.

`nlp2dsl` `VALIDATE` is **validate-workflow** (`workflow_file` /
`workflow` / `check_policy`). Same verb name, different contract — do
**not** force unification or `x-adopts` of the shared path schema.
`diff-dsl` correctly reports this as non-adopted command overlap.

## Acceptance criteria

- [x] AC-01: `schemas/commands/validate.schema.json` created with shared core
- [x] AC-02: `schemas/commands/generate.schema.json` created with shared core
- [x] AC-03: `schemas/commands/patch.schema.json` created with shared core
- [x] AC-04: `schemas/commands/query.schema.json` created with shared core
- [x] AC-05: `dsl_check.py validate` passes
- [ ] AC-06: `governance-check.sh` passes
- [x] AC-07: `schemas/commands/resolve.schema.json` created with shared core

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-devin.md](ai-devin.md)
