# Ticket 022: Harden dsl_check finite JSON, depth, regular-file bounds, and unhashable enum guards

- **ID**: ticket-022
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: MERGED
- **Created**: 2026-11-11

## Goal and scope

SESSION_EXECUTION_AUTHORIZATION: On 2026-11-11 user authorized auditing, fixing bugs, modularizing Python modules under 500 lines, and hardening conformance across `wellmanifest/*` standard repositories.

Harden `src/dsl_primitives.py`, `src/dsl_manifest.py`, `src/dsl_sections.py`, `src/dsl_policy.py`, and `src/dsl_findings.py` against non-finite JSON (`NaN`, `Infinity`, `1e999`), deep JSON nesting (`MAX_JSON_DEPTH = 64`), FIFO/non-regular file hangs (`O_NOFOLLOW | O_NONBLOCK`, `S_ISREG`, size bounds), non-string dictionary keys, non-dict `resolution` / `source` crashes, and `TypeError: unhashable type` crashes on untrusted enum fields and `conformance.levels`, while deduplicating `findings_object` and `string_set` so every module stays strictly `< 500` lines.

## Acceptance criteria

- [x] AC-01: Reject `NaN`, `Infinity`, `-Infinity`, float overflow (`1e999`), nesting `> 64`, non-string dict keys, and non-regular / oversized files in `strict_json_loads`, `unique`, `check_object`, `read_regular_utf8`, and `sha256`.
- [x] AC-02: Replace unsafe enum set membership and `required_publication_tier` / `gate_findings` untrusted collection accesses with `str_choice`, `string_set`, and `isinstance(..., dict)` guards across `dsl_manifest.py`, `dsl_sections.py`, `dsl_policy.py`, and `dsl_findings.py`, keeping every `src/*.py` strictly `< 500` lines.
- [x] AC-03: Add regression tests in `tests/test_dsl_hardening.py`, refresh `profiles/dsl-manifest.json` owned paths and SHA-256 digests, mark merged `ticket-021` `DONE`, and pass `ruff`, `self-test`, `validate`, `standards`, `pytest`, `wellman check`, and governance checks.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
