---
participant-id: agent:codex
participant: codex
role: agent
ticket: ticket-001
---
# Participant: codex (AI agent)

## Understanding

The repository must become the neutral, reusable source of standards for
creating and changing DSLs. It should work like `wellmanifest/new-project`:
projects adopt a versioned contract, declare their local ownership and
artifacts, and run a deterministic gate that blocks ungoverned or stale DSL
changes.

The standard must support a family of DSL profiles rather than merge every
domain into one grammar. Every semantic request sent to an LLM and every
semantic response returned by it must reference a strict DSL contract. The LLM
remains propose-only; runtime-owned authority, execution, acceptance, and
receipts are outside the model response.

No human identity is inferred. Interactive approval is required from
`unresolved:human` before implementation.

## Execution plan

1. Define normative RFC-style requirements in `spec/DSL_STANDARD.md`.
2. Define the closed `wellmanifest.dsl/manifest/v1` JSON Schema.
3. Implement a Python standard-library validator with stable diagnostics,
   repository confinement, hash verification, and changed-artifact ownership.
4. Document component ownership, adoption, and control flow using Mermaid.
5. Run validator self-tests and governance checks in Docker; review the exact
   five-file implementation diff against `intent.json`.

## Actual changes

- Adopted `wellmanifest/new-project` `v0.14.0` governance into the new target.
- Created repository bootstrap files and this planning ticket.
- Created the public `wellmanifest/dsl` GitHub repository and enabled automatic
  deletion of merged ticket branches; it has no commits or pull requests yet.
- At the planning checkpoint, created no standard implementation files.
- Added the normative DSL standard with a worked manifest for the embedded
  `new-project/CONTRIBUTING.md` Policy/Procedure DSL.
- Added a strict Draft 2020-12 manifest schema.
- Added a dependency-free validator for structure, paths, hashes, ownership,
  changed artifacts, authority, and LLM boundaries.
- Added architecture and logic-flow diagrams for creation, changes, LLM use,
  and repository-local adoption.
- Kept the implementation at exactly five files and added no runtime
  dependency.

## Interactive authorization

- 2026-08-09: the user instructed `kontynuuj` and required the DSL embedded in
  `wellmanifest/new-project/CONTRIBUTING.md` to be covered as the initial
  standard example. The approved implementation remains within the existing
  five-file boundary; this authorization is not trusted merge evidence.
- 2026-08-09: the user instructed `kontynuuj, publikuj`, authorizing commit,
  push, ticket-branch publication, and creation of a pull request. Independent
  current-head merge approval is still required.

## Risks

- A monolithic DSL would couple unrelated domains; profiles must remain
  independently versioned.
- JSON Schema alone cannot enforce semantic hashes, authority boundaries, or
  changed-file ownership; deterministic semantic validation is required.
- Short names such as OQL, DQL, and EQL are overloaded; globally stable schema
  identifiers must be namespaced.
- Provider-native structured output can still be malformed; validation must
  fail closed and record an invalid response rather than silently coerce it.
- The generic adopted governance budget cannot classify an initial schema as an
  existing public-interface change. During bootstrap its target-owned
  `publicInterfacePaths` is empty; DSL compatibility is delegated to the
  domain-aware `dsl_check` introduced by this ticket.

## Blockers

- Compose cannot allocate a new Docker network because the host address pools
  are exhausted. Validation uses the same built image with `--network none`;
  no test requires network access.
- No implementation blocker remains. The non-implementation bootstrap is
  published on `main` at `d51a1c900e59963483d0bbfe050623092eb60fff`.
  Merge remains blocked until independent trusted approval targets the current
  pull-request HEAD.

## Acceptance evidence

- AC-01: `spec/DSL_STANDARD.md` sections 1-7.
- AC-02: `schemas/dsl-manifest.schema.json`; Draft 2020-12 metaschema passed.
- AC-03/AC-04: `src/dsl_check.py`; networkless self-test and Ruff passed.
- AC-05: `docs/ARCHITECTURE.md` and `docs/LOGIC_FLOW.md`.
- AC-06: Docker image build and explicit five-path governance check passed.

## Response required

- `unresolved:human`: approve or amend the understanding, five-file scope,
  acceptance criteria, and machine intent.
