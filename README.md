# wellmanifest/dsl

Governed standards, contracts, and conformance guidance for reusable
domain-specific languages and digital-twin profiles.

The repository is intended to make independently developed DSL projects
interoperable without forcing them into one monolithic language. It will define
a small shared kernel, versioned domain profiles, an LLM exchange boundary, and
deterministic checks applied whenever a DSL is created or changed.

## Current status

Bootstrap and planning. Implementation is tracked by
[`project/ticket-001`](project/ticket-001/README.md) and must remain in
`WAIT_FOR_APPROVAL` until its scope is explicitly accepted.

## Governance

This repository adopts `wellmanifest/new-project` `v0.14.0` by immutable
commit. Read [`AGENTS.md`](AGENTS.md), the active ticket, and
[`TODO.md`](TODO.md) before changing standards or tooling.

Normative contracts will live under `spec/` and `schemas/`. Human guidance will
live under `docs/`, examples under `examples/`, and deterministic conformance
tooling under `src/` and `tests/`.
