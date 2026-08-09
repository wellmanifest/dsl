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

1. Extend the normative standard with derived help paths, mandatory page
   content, normalized probe findings and publication-blocking rules.
2. Extend the closed `wellmanifest.dsl/manifest/v1` schema with documentation,
   finding-policy and reusable `wellmanifest.dsl/findings/v1` definitions.
3. Extend the dependency-free validator to validate pages and provide a `gate`
   command consuming normalized reports from tools such as twin-probes.
4. Update architecture and logic flows to separate evidence producers from the
   trusted publication decision and make help links deterministic.
5. Add mutation-style self-tests for missing/miscased/incomplete pages,
   unevaluable probes and unresolved/resolved critical findings.
6. Run schema, Ruff, Mermaid, governance and networkless Docker checks; review
   the exact same five implementation paths against the amended intent.
7. Prepare separate follow-up tickets for a protected required check and local
   pre-push hook; do not pretend that a callable validator alone is remote
   enforcement.

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
- Received a new human requirement for per-command/error/security pages,
  schema-backed probe findings and a publication block, then received approval.
- Added strict documentation catalogs, exact page derivation and content/hash
  checks, the closed `findings/v1` contract, and the revision-bound `gate`
  command without adding runtime dependencies or implementation paths.
- Added mutation tests for filename case, incomplete pages, missing/unevaluable
  producers, and unresolved/resolved security findings.
- Incorporated the independently approved CI bootstrap from `main`, retained
  the exact five implementation paths, and rebound delivery to merge-base
  `9e6b3d77fec03ff50931a584c0509f4c99d34d42` before fresh validation.

## Interactive authorization

- 2026-08-09: the user instructed `kontynuuj` and required the DSL embedded in
  `wellmanifest/new-project/CONTRIBUTING.md` to be covered as the initial
  standard example. The approved implementation remains within the existing
  five-file boundary; this authorization is not trusted merge evidence.
- 2026-08-09: the user instructed `kontynuuj, publikuj`, authorizing commit,
  push, ticket-branch publication, and creation of a pull request. Independent
  current-head merge approval is still required.
- 2026-08-09: the user required uppercase command help pages, error and critical
  code pages, probe-based security detection and contracts modeled after
  `subactor/contracts/schemas`. Because this changes the PR contract, the ticket
  returned to `WAIT_FOR_APPROVAL` before implementation.
- 2026-08-09: the user instructed `kontynuuj`, approving the amended five-file
  contract. The ticket moved to `IN_PROGRESS / EDIT`.

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

- Merge remains blocked until independent trusted approval targets the amended
  current pull-request HEAD.

## Acceptance evidence

- AC-01: `spec/DSL_STANDARD.md` sections 1-7.
- AC-02: `schemas/dsl-manifest.schema.json`; Draft 2020-12 metaschema passed.
- AC-03/AC-04: `src/dsl_check.py`; networkless self-test and Ruff passed.
- AC-05: `docs/ARCHITECTURE.md` and `docs/LOGIC_FLOW.md`.
- AC-06: Docker image build and explicit five-path governance check passed.
- AC-07/AC-08: strict documentation schema plus filename/content/artifact
  mutation tests passed.
- AC-09/AC-10: findings schema sample and publication gate mutations passed.
- AC-11: evidence-producer/trust-root boundaries are normative and diagrammed.
- AC-12: metaschema, Ruff, self-test, Mermaid rendering, governance, Docker
  build, and networkless Docker checks passed.

## Response required

- No implementation clarification is required. Independent trusted review is
  required before merge.
