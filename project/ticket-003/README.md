# Ticket 003: Bootstrap reusable DSL CI and Validator hand-off

- **ID**: ticket-003
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-08-09

## Goal and scope

Add the smallest target-owned CI bootstrap that breaks the current publication
deadlock without weakening review policy. One workflow will expose the exact
required check names `test` and `windows-governance`, call the immutable
`wellmanifest/new-project` governance workflow, and validate both the bootstrap
branch and ticket-001 once it is refreshed from `main`.

The workflow remains useful without repository-side GitHub configuration:
deterministic checks require no secrets, Actions are commit-pinned, and the
trusted App login is a public literal rather than a repository variable. Local
execution remains `./project.sh` plus the networkless Docker commands; GitHub
Actions is an additional protected evidence boundary, not the only entrypoint.

## Acceptance criteria

- [x] AC-01: The human approves one implementation file,
  `.github/workflows/ci.yml`, on the infrastructure workstream.
- [ ] AC-02: Job names exactly match `.governance/required-checks.json`:
  `test` and `windows-governance`.
- [ ] AC-03: Linux validates JSON contracts, Python syntax, Ruff, the DSL
  self-test when present, governance for the exact base/head, and a networkless
  Docker run.
- [ ] AC-04: Windows validates the managed PowerShell/Python governance
  entrypoints for the exact pull-request base/head.
- [ ] AC-05: The pinned reusable governance workflow accepts only an independent
  current-head human or `ifuri-validator-agent[bot]` review.
- [ ] AC-06: Workflow lint, local governance, Docker, and a mutation asserting
  both required job names pass before publication.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)

## Dependency and merge order

This bootstrap is intentionally based on `main`, not on ticket-001. It may be
reviewed and merged first. Ticket-001 must then incorporate the new `main`,
rerun both hosted checks, and obtain a fresh Validator review for its new exact
head before merge.

## Approval

On 2026-08-09 the user answered `tak` to the exact one-workflow plan and asked
for automated execution through the independent `subactor/*-agent` roles. This
authorizes `EDIT` inside the declared scope; it does not authorize self-review
or bypassing exact-head approval.

## Non-goals

- No change to the five implementation files owned by ticket-001.
- No branch protection mutation or self-approval.
- No secret, package publication, release, or automatic merge.
- No validator-agent repository modification in this ticket.
