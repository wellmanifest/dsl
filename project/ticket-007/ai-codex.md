---
participant-id: agent:codex
participant: codex
role: agent
ticket: ticket-007
---
# Participant: codex (AI agent)

## Understanding

The request has two coupled documentation outcomes: standardize how parser
toolchains participate in a governed DSL, and use Env DSL 1 to explain a
concrete toolchain-selection policy. The neutral rule should be
"grammar/semantic contract first, parser engine second": Lark, TatSu, textX,
pest, nom, nearley, Ohm and ANTLR are implementation mechanisms or projections,
not language identity or authority boundaries.

The inspected Env DSL 1 grammar accepts only ordered uppercase assignment
records plus comments/trivia. Its semantics make values inert, forbid secrets,
ambient reads and execution, and reserve `*_EXPRESSION` and `*_CONDITION` for a
bounded evaluator. It can therefore describe portable parser-selection inputs,
but cannot directly contain `RULE`, `WHEN`, `DO`, arrays, quoted strings or
state transitions from `new-project/CONTRIBUTING.md`.

The contributor Policy/Procedure DSL is consequently a separate embedded
`declarative-policy` language. Its clean composition is:

1. a conforming Env DSL parser validates and layers inert constants;
2. a typed adapter maps selected values into the Policy/Procedure DSL runtime;
3. the governance runtime evaluates rules and owns every effect/authority
   decision.

It should not be called an Env DSL 1 extension because Env DSL 1 defines a
closed document grammar and compatibility rules. It is not an implementation
either: the current `scripts/governance_env.py` accepts quoted dotenv values,
`export`, secrets and ambient process-environment precedence, and does not
require Env DSL headers or implement its expression/layering semantics. Those
behaviors are valid only as a distinct new-project adapter contract.

Evidence inspected before planning:

- `env-dsl/spec/env-dsl.abnf` and `ENV_DSL.md` at committed revision
  `d946a7a27e07fba9537b146c873d5ddb264e1539`; the repository has no configured
  remote and contains an unrelated modified ticket log, so this ticket will
  neither mutate it nor create a fabricated `standardsLock` entry.
- `new-project/CONTRIBUTING.md` and `scripts/governance_env.py` at local revision
  `0b38f1bdf5c55cad6b54ad54ba89824a9eaeea78`.
- Official project documentation for all proposed parser toolchains; volatile
  package versions will not be made normative recommendations.

## Execution plan

1. Add a normative subsection to `spec/DSL_STANDARD.md` defining the separation
   between canonical grammar, parser implementation, AST normalization,
   semantic validation and governed execution.
2. Replace stale snapshot language in the existing `new-project` worked profile
   with a revision-bound structural analysis and the explicit
   `uses-data-from` composition relationship to Env DSL 1.
3. Add `docs/GRAMMAR_TOOLCHAINS.md` with the verified tool comparison, selection
   guidance, LLM safety constraints, a valid Env DSL 1 example, and a migration
   path for `governance_env.py` that preserves backward compatibility.
4. Bind the changed standard and new guidance in
   `profiles/dsl-manifest.json`, including exact SHA-256 values and ownership.
5. Run self-test, manifest validation, standards validation, governance and
   networkless Docker checks; record raw output in the agent log.

## Actual changes

- Allocated `ticket-007` in a dedicated worktree and bounded the proposed
  three-file documentation/manifest implementation.
- Recorded the user's explicit follow-up approval to execute, repair version
  inconsistencies and continue. The ticket moved to `IN_PROGRESS / EDIT`.
- No standard, documentation, schema, parser or sibling-repository file has
  been changed outside this ticket's three allowed implementation paths.
- Added normative separation of grammar, safe generation projection, parser,
  AST adapter, semantic validation and authority-owning runtime.
- Added the verified toolchain matrix and LLM/GBNF/MCP/POA flow. The Env DSL
  example passed the actual dependency-free Env DSL 1 parser.
- Updated the worked `new-project` composition from stale document revision 9
  to revision 13 and separated it from Policy DSL language v1 and the
  `policy-sh@1` runtime alias.
- Updated the manifest digests and composition metadata. It now pins published
  `new-project 0.18.0` and `POA 0.1.0` contracts exactly; experimental local
  Env DSL and Policy DSL are mappings only, not fabricated immutable locks.
- All deterministic DSL/governance tests and the networkless Docker self-test
  pass. Docker Compose built the image; this host's Compose lacks `run
  --network`, so isolation was verified with explicit `docker run --network
  none` against that image.

## Blockers

- None inside the approved scope; implementation is ready for protected
  publication and exact-head independent review.
