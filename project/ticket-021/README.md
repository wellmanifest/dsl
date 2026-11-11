# Ticket 021: Modularize dsl_check under 500 lines and harden JSON, symlink, and Git gates

- **ID**: ticket-021
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: PUBLICATION
- **Created**: 2026-11-11

## Goal and scope

SESSION_EXECUTION_AUTHORIZATION: On 2026-11-11 user authorized auditing, fixing bugs, modularizing Python modules under 500 lines, and hardening conformance across `wellmanifest/*` standard repositories.

Modularize the monolithic `src/dsl_check.py` (2,412 lines) into focused `< 500`-line modules (`src/dsl_primitives.py`, `src/dsl_sections.py`, `src/dsl_policy.py`, `src/dsl_manifest.py`, `src/dsl_findings.py`, `src/dsl_selftest.py`, and CLI/re-export facade `src/dsl_check.py`), harden duplicate JSON key, control-character path, symlink escape, URI whitespace, and Git revision option-injection checks, expose `unittest`/`pytest` discovery in `tests/profile_contract_test.py`, and update `profiles/dsl-manifest.json` owned paths and artifact digests.

## Acceptance criteria

- [x] AC-01: Decompose `src/dsl_check.py` into `< 500`-line single-responsibility modules under `src/` while preserving full CLI and symbol re-export compatibility.
- [x] AC-02: Reject duplicate JSON object keys, control-character relative paths, symlink escapes in help pages, target manifests, sensitive-path probing, and findings reports, whitespace/control characters in URIs, and leading-dash Git revision arguments (`DSL-GIT-001`).
- [x] AC-03: Refresh `profiles/dsl-manifest.json` SHA-256 artifact digests and `ownedPaths`, add `unittest`/`pytest` test discovery to `tests/profile_contract_test.py`, and pass `ruff`, `self-test`, `validate`, `standards`, `pytest`, Docker, and governance checks.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
