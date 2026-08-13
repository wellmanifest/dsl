---
participant-id: agent:codex
participant: codex
role: agent
ticket: ticket-005
---
# Participant: codex (AI agent)

## Understanding

The DSL standard already defines identity, ownership, canonical artifacts,
authority and LLM boundaries, but it does not yet use its own manifest, publish
the promised domain profiles, pin its sibling standards, or map declared risk
to a proportional publication gate.

## Execution plan

1. Add a closed core profile family for the reusable typed document boundaries.
2. Add a closed cross-standard immutable lock.
3. Dogfood `wellmanifest.dsl/manifest/v1` at the repository root.
4. Add deterministic validation for profile schemas, standards lock and the
   proportional publication-tier matrix.
5. Update the normative standard and run self-test, validation and governance.

## Actual changes

- Ticket allocated through the managed clone-wide allocator after fetch/prune.
- Work isolated on `ticket/005-core-profiles` in a dedicated worktree.
- Explicit user approval recorded as bounded session execution authorization.
- Added nine closed profile variants spanning source, intent/evidence,
  query/result, observation, operation, authority, verification and terminal
  LLM exchange audit.
- Extended the manifest with command/document vocabulary modes, a
  risk-derived publication policy and an embedded immutable standards lock.
- Added aggregate `standards` validation, dogfooded the profile manifest and
  bound every changed normative artifact by SHA-256. The manifest lives below
  `profiles/`, because the adopted governance contract assigns that boundary
  to this ticket's integration workstream.
- Pinned the published `new-project@0.16.2` contract. POA is deliberately not
  locked while its updated contract exists only on a reviewable PR branch and
  has no published immutable revision.
- Revalidated all schema, manifest, standards, self-test and governance checks,
  then moved the ticket to `PUBLICATION`; commit and PR publication are
  authorized, while merge, tag and release remain external.

## Blockers

- None within the recorded intent. Trusted merge and immutable release approval
  remain external to this ticket.

## Acceptance evidence

- Draft 2020-12 metaschema validation passes for the manifest and profile
  schemas.
- `dsl_check.py validate profiles/dsl-manifest.json`, `dsl_check.py standards
  profiles/dsl-manifest.json` and `self-test` pass.
- The self-test rejects stale hashes, unsafe LLM authority, understated
  publication tier and duplicate standard pins.
