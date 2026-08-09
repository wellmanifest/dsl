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
6. On the protected default-branch push, switch only the deterministic checks
   to clean repository-health mode; retain exact range binding everywhere
   before merge.

## Actual changes

- The user approved the exact one-workflow scope; implementation moved to
  `IN_PROGRESS / EDIT`.
- Added commit-pinned Linux, Windows, and reusable governance jobs without
  secrets or mutable action references.
- The Linux job derives an explicit changed-file boundary before entering the
  networkless image because the image deliberately contains no `.git` data.
- Required-check alignment, its negative mutation, JSON/metaschema validation,
  Python compilation, local governance, actionlint, Docker build, the
  networkless gate, and `git diff --check` all passed. Publication is ready;
  Windows remains intentionally pending for hosted evidence.
- The first hosted attempt correctly exposed that plan and implementation had
  been combined and that Windows checkout converted managed files to CRLF. The
  replacement branch now has a plan-only parent commit and configures LF before
  checkout; no gate or digest verification was weakened.
- PR #1 then proved that replaying exact-range governance after merge is
  invalid: `origin/main` has necessarily advanced to the merge commit. The
  corrective design uses repository-health validation only for a push to the
  protected default branch; all pre-merge executions stay exact-range bound.

## Blockers

- None. `validator-agent` now has a dedicated `wellmanifest/dsl` profile and
  GitHub App `checks:read`; independent approval is still required for the
  corrective PR head.
