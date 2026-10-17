# Ticket 020: Extract git subprocess helper from loop in dsl_check

- **ID**: ticket-020
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-10-17

## Goal and scope

SESSION_EXECUTION_AUTHORIZATION: On 2026-10-17 user authorized fixing PERF-AUDIT findings and aligning `.governance/standard-adoption.json` across wellmanifest repositories.
Extract _run_git_command helper outside the loop in git_paths in src/dsl_check.py and align .governance/standard-adoption.json.

## Acceptance criteria

- [x] AC-01: Extract _run_git_command helper outside the loop in git_paths in src/dsl_check.py and align .governance/standard-adoption.json.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
