# Ticket 024: Harden dsl_primitives JSON overflow/surrogates, ancestor symlinks, URI segments, and regex anchors

- **ID**: ticket-024
- **Owner**: tom
- **Status**: DONE
- **Workflow state**: DONE
- **Created**: 2026-11-11

## Goal and scope

SESSION_EXECUTION_AUTHORIZATION: On 2026-11-11 user authorized auditing, fixing security and conformance bugs, and optimizing across `wellmanifest/*` standard repositories.

Harden `src/dsl_primitives.py` by anchoring all 11 identifier/digest/revision/URI regexes and Windows drive-letter detection with `\A...\Z`, rejecting `10**400` integer overflow, 4300+ digit JSON integers, and lone UTF-16 surrogates across `is_string`, `_enforce_json_depth`, and `strict_json_loads`, passing `allow_nan=False` in `Report.render("json")`, enforcing positive integer `max_bytes`, bounded `os.read` chunks, and relative + deep absolute symlink-ancestor rejection in `_open_regular_fd` and `read_regular_bytes`, hardening `uri_is_valid` against `urlparse` `ValueError`, `.` dot-segments, and empty colon-delimited opaque segments, updating `profiles/dsl-manifest.json` digests, and reconciling merged `ticket-023` status to `DONE`.

## Acceptance criteria

- [x] AC-01: Anchor regex patterns with `\A...\Z`, reject `10**400` JSON integer overflow, 4300+ digit integers, and lone UTF-16 surrogates across `is_string`, `_enforce_json_depth`, and `strict_json_loads`, and pass `allow_nan=False` in `Report.render`.
- [x] AC-02: Enforce positive integer `max_bytes`, bounded `os.read`, and relative + deep absolute symlink-ancestor rejection in `_open_regular_fd` / `read_regular_bytes`, and reject malformed IPv6 URIs, `.` dot-segments, and empty colon-delimited opaque segments in `uri_is_valid`, keeping all `src/*.py` strictly `< 500` lines.
- [x] AC-03: Expand `tests/test_dsl_hardening.py`, update `profiles/dsl-manifest.json` SHA-256 digests, reconcile merged `project/ticket-023/README.md` to `DONE`, and pass `ruff`, `self-test`, `validate`, `standards`, `pytest`, `wellman check`, and governance checks.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
