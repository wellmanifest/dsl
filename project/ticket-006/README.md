# Ticket 006: Upgrade GitHub Actions to Node 24

- **ID**: ticket-006
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-08-14

## Goal and scope

Replace the two Node.js 20 GitHub Action pins in the target-owned DSL workflow
with immutable Node.js 24-compatible releases. The change is limited to both
Linux and Windows uses of `actions/checkout` and `actions/setup-python`; job
names, triggers, permissions and validation behavior remain unchanged.

## Acceptance criteria

- [x] AC-01: The user's repeated instruction to continue authorizes this
  one-workflow maintenance scope for the current session.
- [ ] AC-02: Every `actions/checkout` use is pinned to verified v7.0.1 commit
  `3d3c42e5aac5ba805825da76410c181273ba90b1`.
- [ ] AC-03: Every `actions/setup-python` use is pinned to verified v7.0.0
  commit `5fda3b95a4ea91299a34e894583c3862153e4b97`.
- [ ] AC-04: Actionlint, governance, deterministic host checks, and
  networkless Docker validation pass without changing required check names.
- [ ] AC-05: Hosted Linux, Windows and reusable governance jobs pass and no
  longer emit the Node.js 20 deprecation warning for these actions.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)

## Authorization

After the clean governance audit, the user repeatedly instructed the agent to
continue. This creates session execution authorization for the bounded
maintenance described above; it is not trusted merge approval and does not
authorize self-review or policy bypass.

## Non-goals

- No modification of the reusable governance standard.
- No job-name, trigger, permission, Python-version, or validation-logic change.
- No dependency, release, branch-protection, or automatic-merge change.
