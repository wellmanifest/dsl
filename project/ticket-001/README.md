# Ticket 001: Establish reusable DSL standards and conformance gate

- **ID**: ticket-001
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-08-09

## Goal and scope

Create the first usable release of the shared DSL standard. The change will
define the normative requirements for every governed DSL, a strict manifest
contract, deterministic validation, and visual documentation of adoption and
LLM-boundary flows.

This ticket is intentionally limited to five implementation files. Reusable
fixtures, CI workflows, domain profiles, SDKs, and migrations belong to later
tickets after the kernel contract is accepted.

The normative standard and architecture documentation will include the
rule-oriented DSL embedded in `wellmanifest/new-project/CONTRIBUTING.md` as the
first worked profile. This ticket describes and validates its contract shape;
adopting a manifest inside `new-project` remains a separate repository-local
change.

## Acceptance criteria

- [x] AC-01: The normative standard defines ownership, purpose, canonical
  representation, identifiers, versioning, hashes, provenance, lifecycle,
  authority, LLM boundaries, compatibility, and conformance obligations.
- [x] AC-02: A strict JSON Schema defines `wellmanifest.dsl/manifest/v1` and
  rejects unknown or incomplete manifest fields.
- [x] AC-03: A dependency-free validator checks manifests, repository-local
  references, artifact SHA-256 values, unique ownership, and conditional LLM
  input/output contracts.
- [x] AC-04: The validator can detect changed DSL artifacts that are unclaimed
  or whose recorded hash is stale and provides stable diagnostic codes.
- [x] AC-05: Architecture and logic-flow documents contain Mermaid diagrams and
  explain adoption by new and existing projects.
- [x] AC-06: Governance validation and the validator self-test pass in the
  declared Docker environment.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)

## Non-goals

- Migrating onlyDSL, doDSL, todo2code, twin-dsl, OQL, EQL, TestQL, URI-run, or
  Planfile in this ticket.
- Defining every domain profile in the initial change.
- Treating LLM output as approval, authority, evidence, or execution receipt.
- Publishing or merging without the repository review boundary.

## Validation evidence

- Draft 2020-12 metaschema: PASS.
- Worked `new-project/CONTRIBUTING.md` manifest, digest, and semantics: PASS.
- Dependency-free validator self-test: PASS.
- Ruff: PASS.
- Markdown links, secrets, and absolute-path scans: PASS.
- Docker image build: PASS.
- Networkless Docker governance check: PASS.

## Publication decision

The local implementation is complete and validated. On 2026-08-09 the user
explicitly authorized continuation and publication. Commit
`d51a1c900e59963483d0bbfe050623092eb60fff` established the previously missing
`main` using bootstrap and governance files only. The five implementation
files are bound to that base and are published only through this ticket branch
and its pull request.
