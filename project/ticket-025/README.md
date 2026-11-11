# Ticket 025: Modularize dsl_io and harden symlink traversal, JSON bounds, and control-char checks

- **ID**: ticket-025
- **Owner**: tom
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-11-11

## Goal and scope

SESSION_EXECUTION_AUTHORIZATION: On 2026-11-11 user authorized auditing, fixing security and conformance bugs, and optimizing across `wellmanifest/*` standard repositories.

Extract bounded regular-file I/O, symlink-ancestor verification, strict finite JSON parsing, and SHA-256 hashing into `src/dsl_io.py` (re-exported via sorted `__all__` in `src/dsl_primitives.py`) so all `src/*.py` and `tests/*.py` modules stay well below 500 lines after 88-column `ruff format`. Harden `_has_symlink_ancestor` against relative (`sym_dir/..`, `../sym_dir`) and un-normalized absolute symlink-parent traversal across `read_regular_bytes`, `sha256`, and `validate_findings_report`, bound JSON integer digit counts (`<= 400`) before `int()` conversion in `_parse_bounded_int`, reject ASCII C0/DEL control characters in `is_string` and single-line manifest/findings identifiers and conformance commands via `is_single_line_string`, refresh `profiles/dsl-manifest.json` artifact digests, and reconcile merged `project/ticket-024/README.md` to `DONE`.

## Acceptance criteria

- [x] AC-01: Extract `src/dsl_io.py` and re-export all public/internal helpers from `src/dsl_primitives.py` via sorted `__all__`, keeping every `src/*.py` and `tests/*.py` file strictly `< 500` lines after `ruff format`.
- [x] AC-02: Harden `_has_symlink_ancestor` against relative (`sym_dir/..`, `../sym_dir`) and un-normalized absolute symlink-parent traversal, bound JSON integer digits (`<= 400`) before `int()` conversion, and reject forbidden ASCII C0/DEL control characters and multi-line single-line fields across `dsl_primitives`, `dsl_sections`, and `dsl_findings`.
- [x] AC-03: Expand `tests/test_dsl_hardening.py`, register `src/dsl_io.py` and updated SHA-256 digests in `profiles/dsl-manifest.json`, mark merged `project/ticket-024/README.md` `DONE`, and pass `ruff`, `self-test`, `validate`, `standards`, `pytest`, governance, and `wellman check`.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
