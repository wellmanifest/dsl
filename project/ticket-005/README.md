# Ticket 005: Add core profiles and standards lock

- **ID**: ticket-005
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: DONE
- **Created**: 2026-08-12

## Goal and scope

Publish the first reusable, closed DSL profile family; make this repository
conform to its own manifest contract; add an immutable lock for composing
Wellmanifest standards; and enforce a proportional publication gate derived
from effect, conformance and LLM-boundary risk.

The user's explicit instructions to perform and push the recommended updates
are recorded as `SESSION_EXECUTION_AUTHORIZATION` and ticket-branch/PR
publication authority for the exact paths in `intent.json`. They are not
trusted merge, tag or release approval.

## Acceptance criteria

- [x] AC-01: Scope is explicitly approved in the current session.
- [x] AC-02: `profiles/dsl-manifest.json` validates and binds every normative
  artifact in the integration-owned profile boundary.
- [x] AC-03: A closed profile schema covers source, intent/evidence,
  query/result, observation, operation, authority, verification and LLM
  exchange documents.
- [x] AC-04: A closed standards lock pins published dependencies by immutable
  revision and contract digests; unpublished POA remains an explicit TODO
  instead of receiving a fabricated pin.
- [x] AC-05: Publication tiers are deterministic and proportional to effects,
  claimed conformance and LLM mode.
- [x] AC-06: Self-test, manifest validation, host governance and an isolated
  Docker governance run pass. Compose network creation is blocked by exhausted
  host address pools, so the same image was verified with `--network none` and
  an explicit protected change set.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
