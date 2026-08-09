# Project roadmap

- [x] [`ticket-001`](project/ticket-001/README.md) — define the initial DSL
  standard, manifest contract, per-command/error/security documentation, and
  deterministic change/publication gate. Amended scope: `PUBLICATION`.
- [~] [`ticket-003`](project/ticket-003/README.md) — correcting post-merge
  default-branch repository-health validation after bootstrapping the two
  required deterministic CI checks and the pinned Validator hand-off; merged
  through PR #3 as `9e6b3d77fec03ff50931a584c0509f4c99d34d42`.
- [ ] Add domain profiles for intent/evidence, query/result, digital twin,
  operation, authority, verification, and LLM exchange in subsequent scoped
  tickets.
- [ ] Publish reusable adoption guidance and mappings for existing DSL projects.
- [ ] After the documentation/findings contract is merged, wire
  `dsl_check.py gate` into a protected required check and add a local pre-push
  convenience hook; the protected check remains the publication trust root.
