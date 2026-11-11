# Ticket 023: Harden in-repository symlink traversal, regular-file inode stability, and URI scheme bounds

- **ID**: ticket-023
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-11-11

## Goal and scope

SESSION_EXECUTION_AUTHORIZATION: On 2026-11-11 user authorized auditing, fixing security and conformance bugs, and optimizing across `wellmanifest/*` standard repositories.

Reject in-repository symlinks and ancestor symlink directories across `resolve_repository_path`, `validate_manifest`, `load_targets`, `is_dsl_sensitive`, and `validate_findings_report` so symlinks inside the repository cannot bypass `O_NOFOLLOW`; enforce `lstat`+`fstat` inode stability in `_open_regular_fd`; harden `safe_relative`, `_enforce_json_depth`, `\Z`-anchored regexes, and `uri_is_valid`; refresh `profiles/dsl-manifest.json` digests; and reconcile merged `ticket-019`, `ticket-020`, and `ticket-022` statuses to `DONE`.

## Acceptance criteria

- [x] AC-01: Reject in-repository and ancestor symlinks before path resolution in `resolve_nonsymlink_under_root`, `resolve_repository_path`, `validate_manifest`, `load_targets`, `is_dsl_sensitive`, and `validate_findings_report`, and verify `lstat`/`fstat` inode identity in `_open_regular_fd`.
- [x] AC-02: Harden `safe_relative` against empty/dot segments and ASCII DEL, anchor identifier/digest/revision regexes with `\Z`, enforce string keys and finite floats in `_enforce_json_depth`, and reject missing authorities and `..` traversal in `uri_is_valid`, keeping all `src/*.py` strictly `< 500` lines.
- [x] AC-03: Expand `tests/test_dsl_hardening.py`, update `profiles/dsl-manifest.json` SHA-256 digests, reconcile merged `ticket-019`, `ticket-020`, and `ticket-022` `README.md` headers to `DONE`, and pass `ruff`, `self-test`, `validate`, `standards`, `pytest`, `wellman check`, and governance checks.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
