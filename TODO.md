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
  `ifuri-validator-agent` approved and merged
  `94fe47e4440f45f1295476af2b1bbda6296a0152`.
- [ ] [`ticket-006`](project/ticket-006/README.md) — upgrade the target-owned
  checkout and Python setup actions to immutable Node.js 24-compatible pins
  without changing the required-check contract.
- [ ] [`ticket-007`](project/ticket-007/README.md) — standardize parser
  toolchains as replaceable DSL implementation profiles, document them through
  a conforming Env DSL 1 example, and classify the `new-project` contributor
  DSL as a separate policy language composed through an adapter.
- [ ] Add POA to `standardsLock` only after its updated v1 contract is committed
  at an immutable revision and its exact contract digest can be verified.
- [ ] Publish reusable adoption guidance and mappings for existing DSL projects.
- [ ] After the documentation/findings contract is merged, wire
  `dsl_check.py gate` into a protected required check and add a local pre-push
  convenience hook; the protected check remains the publication trust root.
