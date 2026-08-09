# Project roadmap

- [x] [`ticket-001`](project/ticket-001/README.md) — define the initial DSL
  standard, manifest contract, per-command/error/security documentation, and
  deterministic change/publication gate. Amended scope: `PUBLICATION`.
- [x] [`ticket-003`](project/ticket-003/README.md) — bootstrapped the two
  required deterministic CI checks and pinned Validator hand-off, then fixed
  protected post-merge repository-health validation in PR #4; verified on
  `main` by run `31321405881`.
- [ ] Add domain profiles for intent/evidence, query/result, digital twin,
  operation, authority, verification, and LLM exchange in subsequent scoped
  tickets.
- [ ] Publish reusable adoption guidance and mappings for existing DSL projects.
- [ ] After the documentation/findings contract is merged, wire
  `dsl_check.py gate` into a protected required check and add a local pre-push
  convenience hook; the protected check remains the publication trust root.
