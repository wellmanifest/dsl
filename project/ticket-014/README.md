# Ticket 014: Define execution recovery profiles

- **ID**: ticket-014
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-09-01

## Goal and scope

Define closed execution and recovery document profiles for one accepted
delivery plan, bounded work-slice splitting, deterministic session recovery,
observed remote rebinding and typed tool action request/results. Supply valid
and invalid fixtures plus a deterministic validator for graph and
cross-document bindings.

## Acceptance criteria

- [x] AC-01: GitHub issue #19 and the user's instruction to continue and close
      all tasks authorize this bounded implementation.
- [x] AC-02: The accepted delivery plan compiles to a bounded acyclic slice
      graph; split request/results preserve plan and dependency bindings.
- [x] AC-03: Checkpoint, resume observation/decision and remote
      observation/rebind profiles bind immutable facts without granting
      authority or selecting credentials.
- [x] AC-04: Typed tool request/results bind the same capability ID, typed
      artifacts, declared effects and terminal receipts.
- [x] AC-05: Draft 2020-12 metaschema, valid/invalid fixtures, DSL
      validate/standards/self-test, exact governance and Docker checks pass.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
