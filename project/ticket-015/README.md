# Ticket 015: Run profile contracts in host CI

- **ID**: ticket-015
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-09-01

## Goal and scope

Run the execution/recovery profile contract validator in the pinned Linux host
CI step. Compile and lint the validator before execution so syntax, formatting,
semantic fixture failures and cross-document binding regressions all block the
required `test` check.

## Acceptance criteria

- [x] AC-01: GitHub issue #19 and the user's instruction to close all tasks
      authorize this bounded infrastructure follow-up.
- [x] AC-02: Host CI compiles and checks the format and lint of the profile
      contract validator with the existing pinned Ruff installation.
- [x] AC-03: Host CI runs `tests/profile_contract_test.py` after installing the
      existing pinned `jsonschema` dependency.
- [x] AC-04: Actionlint, profile contracts, exact governance and networkless
      Docker checks pass before protected merge.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
