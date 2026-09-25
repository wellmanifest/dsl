# Ticket 017: Keep DSL discovery within the selected repository

- **ID**: ticket-017
- **Owner**: user
- **Status**: DONE
- **Workflow state**: DONE
- **Created**: 2026-09-07

## Goal and scope

SESSION_EXECUTION_AUTHORIZATION: user requested continuation of the concrete remediation plan for duplicate DSL reports caused by nested worktrees. Repair the upstream discovery boundary, cover it with regressions and publish through the independent Validator. Preserve ordinary package discovery and explicit validation of another checkout.

## Acceptance criteria

- [x] AC-01: Recursive discovery skips nested Git checkouts and reserved worktree/recovery storage.
- [x] AC-02: Ordinary packages and an explicitly selected nested checkout still validate; regression self-tests pass.
- [x] AC-03: Matching checker artifact digest, managed governance and networkless Docker checks pass.
- [ ] AC-04: Protected exact-head review and upstream publication complete before downstream adoption.

## Validation

The discovery regression failed before the fix and passes afterward. Self-tests, Ruff and profile contract tests pass. Against the MaskFleet primary checkout, discovery now reports only its own manifest; duplicate manifests from worktrees and recovery storage disappear. The current upstream checker correctly reports separate missing schema fields in that older consumer, so downstream adoption must compose with its existing ticket-063 migration rather than claim full compatibility.

Managed governance passed with 0 errors and 0 warnings against the exact base and staged file boundary. The Docker image built successfully; self-tests and profile validation passed with network disabled. The checker digest matches the profile artifact. Publication remains pending independent exact-head review.
