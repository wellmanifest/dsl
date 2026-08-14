---
participant-id: agent:codex
participant: codex
role: agent
ticket: ticket-006
---
# Participant: codex (AI agent)

## Understanding

The post-cleanup `dsl-ci` run is green, but both Linux and Windows jobs emit a
Node.js 20 deprecation warning. Run logs bind it to the target repository's
`actions/checkout` v4.2.2 and `actions/setup-python` v5.4.0 pins. The reusable
governance workflow already uses Node.js 24-compatible actions and is outside
this ticket's scope.

## Execution plan

1. Record the one-file infrastructure intent on base
   `fb06a4f1c75f1f19804a846baed0a2b17dc8d15a`.
2. Replace all Linux and Windows checkout/setup-python pins with the exact
   upstream tag commits verified through the GitHub API.
3. Assert that no old pins remain and required job names are unchanged.
4. Run actionlint, deterministic host governance, and networkless Docker
   validation.
5. Publish through a ticket branch and PR for independent exact-head review;
   do not self-approve or merge without the protected boundary.

## Actual changes

- Allocated `ticket-006` through the managed clone-wide allocator in a detached
  worktree, then created `ticket/006-node24-actions`.
- Verified the exact upstream v7 tag commits before recording the implementation
  scope.
- Replaced both Linux and Windows uses of checkout/setup-python with the exact
  verified v7 commits; triggers, permissions, job names, Python 3.12 and all
  validation logic are byte-for-byte unchanged.
- Exact pin assertions, required-check alignment, actionlint, Python compile,
  Ruff, DSL self-test, host governance, Docker build, networkless governance,
  and networkless DSL self-test pass.

## Blockers

- Hosted pull-request evidence and independent exact-head review require a push
  and PR, which are external coordination and remain separately authorized.
