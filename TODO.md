# Project roadmap

## Active ticket

- [ ] [`ticket-004`](project/ticket-004/README.md) — reconcile public status,
  release history, roadmap boundaries, and deterministic plus LLM-enriched
  intent-audit evidence.

## Completed tickets

- [x] [`ticket-001`](project/ticket-001/README.md) — define the initial DSL
  standard, manifest contract, per-command/error/security documentation, and
  deterministic change/publication gate; merged through PR #1 as
  `a8b4e7ab8d68e36a4457e5c1fd267e707f0b6852`.
- [x] [`ticket-003`](project/ticket-003/README.md) — bootstrapped the two
  required deterministic CI checks and pinned Validator hand-off, then fixed
  protected post-merge repository-health validation in PR #4; verified on
  `main` by run `31321405881`.

## Unscheduled roadmap

These items are direction only, not authorization to implement. Each requires a
new, classified ticket with non-overlapping `allowedPaths` before work begins.

- [ ] Add domain profiles for intent/evidence, query/result, digital twin,
  operation, authority, verification, and LLM exchange in subsequent scoped
  tickets.
- [ ] Publish reusable adoption guidance and mappings for existing DSL projects.
- [ ] After the documentation/findings contract is merged, wire
  `dsl_check.py gate` into a protected required check and add a local pre-push
  convenience hook; the protected check remains the publication trust root.
