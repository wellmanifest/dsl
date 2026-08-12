# Project roadmap

- [x] [`ticket-001`](project/ticket-001/README.md) — define the initial DSL
  standard, manifest contract, per-command/error/security documentation, and
  deterministic change/publication gate; merged through PR #1 as
  `a8b4e7ab8d68e36a4457e5c1fd267e707f0b6852`.
- [x] [`ticket-003`](project/ticket-003/README.md) — bootstrapped the two
  required deterministic CI checks and pinned Validator hand-off, then fixed
  protected post-merge repository-health validation in PR #4; verified on
  `main` by run `31321405881`.
- [x] [`ticket-005`](project/ticket-005/README.md) — add domain profiles for
  typed source, intent/evidence, query/result, digital twin, operation,
  authority, verification and LLM exchange; dogfood the manifest and add a
  cross-standard lock plus proportional publication tiers.
- [ ] Add POA to `standardsLock` only after its updated v1 contract is committed
  at an immutable revision and its exact contract digest can be verified.
- [ ] Publish reusable adoption guidance and mappings for existing DSL projects.
- [ ] After the documentation/findings contract is merged, wire
  `dsl_check.py gate` into a protected required check and add a local pre-push
  convenience hook; the protected check remains the publication trust root.
