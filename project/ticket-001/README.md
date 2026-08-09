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

After publication of the first PR head, the human owner requested and then
approved a stronger documentation and security gate. The amendment stayed
inside the same five implementation paths and now:

- require every declared uppercase DSL command to have the exact help page
  `docs/<COMMAND>.md`;
- require runtime error codes to have `docs/ERROR/<CODE>.md`;
- require security/critical codes to have `docs/CRITICAL/<CODE>.md`;
- define strict manifest fields and a normalized findings contract modeled
  after the closed Draft 2020-12 contracts in `subactor/contracts/schemas`;
- let deterministic tools such as `twin-probes` provide evidence through an
  adapter, while the trusted DSL gate alone decides whether publication blocks;
- reject missing/incomplete documentation, missing or unevaluable required
  probes, and unresolved critical/security findings before publication.

This ticket defines and tests the `dsl_check.py gate` trust boundary. A
follow-up infrastructure ticket will wire that command into a protected required
check, and a governance ticket will add the local pre-push convenience hook.
The remote required check is authoritative because a local hook can be bypassed
with `--no-verify`.

Documentation is not a waiver: documenting a critical finding makes remediation
discoverable but does not permit an unresolved issue to be pushed or merged.

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
- [x] AC-07: The manifest declares an uppercase command catalog and exact
  command/error/critical documentation roots and codes.
- [x] AC-08: The validator derives exact case-sensitive paths, checks required
  headings/content, and emits a direct help path for every documentation error.
- [x] AC-09: A strict `wellmanifest.dsl/findings/v1` contract records producer,
  repository/revision binding, evaluability, joinable paths, severity, security
  classification, resolution and evidence references.
- [x] AC-10: The publication gate consumes normalized finding reports, requires
  configured producers, blocks unevaluable security evidence, and blocks every
  unresolved critical/security finding even when its page exists.
- [x] AC-11: `subactor.autonom-cycle/v1` and `twin-probes` are documented as
  evidence inputs requiring a deterministic adapter, not as trust roots.
- [x] AC-12: Schema metaschema, validator self-tests, Ruff, Mermaid, governance
  and networkless Docker validation pass for the amended five-file scope.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)

## Non-goals

- Migrating onlyDSL, doDSL, todo2code, twin-dsl, OQL, EQL, TestQL, URI-run, or
  Planfile in this ticket.
- Defining every domain profile in the initial change.
- Treating LLM output as approval, authority, evidence, or execution receipt.
- Publishing or merging without the repository review boundary.
- Installing the protected CI check or local pre-push hook in this five-file
  integration ticket; wiring follows after the gate contract is merged.

## Validation evidence

- Draft 2020-12 metaschema: PASS.
- Manifest and normalized-findings schema samples: PASS.
- Dependency-free validator self-test: PASS.
- Ruff: PASS.
- Mermaid CLI rendering of all 12 diagrams: PASS.
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

On 2026-08-09 the user answered `kontynuuj`, explicitly approving the amended
plan above. The amended implementation and validation are complete inside the
existing five-file boundary. Any prior review must target the new exact HEAD
again.
