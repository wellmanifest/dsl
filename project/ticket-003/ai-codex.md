---
participant-id: agent:codex
participant: codex
role: agent
ticket: ticket-003
---
# Participant: codex (AI agent)

## Understanding

PR #1 has no hosted checks, no review, and an unprotected default branch.
Validator-agent correctly refuses to review a repository with no configured
required checks. The standard ticket cannot add a sixth implementation file,
so CI must be bootstrapped in a separate infrastructure ticket based on main.

## Execution plan

1. Add one commit-pinned workflow with the reusable governance job and exact
   `test` / `windows-governance` required job names.
2. Make Linux and Windows compute the immutable PR base/head and run target
   governance without trusting model output or repository secrets.
3. Run DSL self-tests conditionally so this bootstrap passes on current `main`
   and validates ticket-001 after that branch incorporates the bootstrap.
4. Validate required-check name alignment, action pinning, workflow syntax,
   local governance, and networkless Docker behavior.
5. Publish only through its own branch/PR; do not merge or self-approve.

## Actual changes

- The user approved the exact one-workflow scope; implementation moved to
  `IN_PROGRESS / EDIT`.

## Blockers

- `validator-agent` still needs a separate allowlist/profile change for
  `wellmanifest/dsl` after these hosted checks exist.
