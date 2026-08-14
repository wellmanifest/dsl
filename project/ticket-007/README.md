# Ticket 007: Standardize grammar toolchains and Env DSL composition

- **ID**: ticket-007
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-08-14

## Goal and scope

Define how `wellmanifest/dsl` standardizes parser-toolchain choices without
making a parser library the semantic source of truth. Publish adoption guidance
for Lark, TatSu, textX, pest, nom, nearley, Ohm and ANTLR, expressed through a
conforming Env DSL 1 selection example and tied to the existing manifest,
artifact and conformance model.

Classify the relationship between Env DSL 1 and the Policy/Procedure DSL
embedded in `wellmanifest/new-project/CONTRIBUTING.md`. The analysis must
distinguish language extension, language implementation and composition through
an adapter, and must assess the current `scripts/governance_env.py` behavior
against the normative Env DSL grammar and semantics.

## Acceptance criteria

- [x] AC-01: The user explicitly approved implementation and then requested
  continuation plus repair of revision inconsistencies in composed DSLs.
- [ ] AC-02: The standard separates the canonical grammar and semantic model
  from parser engines, generated parsers, AST adapters and execution runtimes.
- [ ] AC-03: Adoption guidance compares Lark, TatSu, textX, pest, nom, nearley,
  Ohm and ANTLR using verified upstream documentation and gives bounded
  selection criteria for LLM-to-DSL pipelines.
- [ ] AC-04: The guidance contains an Env DSL 1 example that conforms to the
  inspected ABNF and remains inert descriptive data rather than executable
  parser configuration.
- [ ] AC-05: The worked `new-project` profile explicitly records that its
  Policy/Procedure DSL is a separate language which may consume Env DSL data,
  but is neither an Env DSL 1 extension nor an Env DSL 1 implementation.
- [ ] AC-06: The current `governance_env.py` boundary is accurately classified
  as an adapter for the embedded declaration/dotenv contract, with concrete
  incompatibilities that prevent an Env DSL 1 conformance claim.
- [ ] AC-07: Manifest ownership and SHA-256 bindings are updated for every
  changed standard or guidance artifact, and deterministic DSL, governance and
  Docker checks pass.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)

## Authorization

The materialized plan stopped in `WAIT_FOR_APPROVAL`. The user's later
instructions explicitly said to execute, fix the identified inconsistencies
and continue. This records `SESSION_EXECUTION_AUTHORIZATION` for the bounded
three-file implementation; it is not trusted merge approval.

## Non-goals

- Do not modify `wellmanifest/env-dsl` or `wellmanifest/new-project`.
- Do not add parser libraries or runtime dependencies.
- Do not define a universal grammar or mandate one parser engine.
- Do not claim that the locally inspected, unpublished Env DSL revision is an
  immutable composed-standard lock.
- Do not make LLM-generated grammar changes self-authorizing.
