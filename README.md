# wellmanifest/dsl

Governed standards, contracts, and conformance guidance for reusable
domain-specific languages and digital-twin profiles.

The repository is intended to make independently developed DSL projects
interoperable without forcing them into one monolithic language. It will define
a small shared kernel, versioned domain profiles, an LLM exchange boundary, and
deterministic checks applied whenever a DSL is created or changed.

## Current status

The reusable DSL baseline is implemented as version `0.1.0-dev`.
[`ticket-001`](project/ticket-001/README.md) delivered the normative standard,
schema, validator, and architecture documentation; [`ticket-003`](project/ticket-003/README.md)
added the protected Linux and Windows CI checks. Both tickets are complete and
the current `main` passes governance and DSL self-tests.

Domain profiles, adoption mappings, and production use of `dsl_check.py gate`
remain explicitly unscheduled roadmap work. Each requires its own bounded
ticket before implementation.

## Governance

This repository adopts `wellmanifest/new-project` `v0.14.0` by immutable
commit. Read [`AGENTS.md`](AGENTS.md), [`TODO.md`](TODO.md), and the matching
active ticket, when one exists, before changing standards or tooling.

Normative contracts live under `spec/` and `schemas/`. Human guidance lives
under `docs/`; deterministic conformance tooling lives under `src/` and
`tests/`. Future examples and domain profiles must be introduced through their
own governed tickets.
