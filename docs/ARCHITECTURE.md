# Architecture

## Outcome

`wellmanifest/dsl` is a neutral contract and conformance layer between DSL
owners, projects that reuse their languages, deterministic runtimes, and LLM
adapters. It standardizes how a language is described and governed without
centralizing every domain's semantics.

```mermaid
flowchart LR
    NP[wellmanifest/new-project\nrepository governance]
    DS[wellmanifest/dsl\nDSL contracts]
    DP[Domain DSL repository\nsemantic owner]
    AP[Adopting project]
    CI[Deterministic CI gate]
    PROBE[Deterministic evidence producers]
    LLM[LLM provider adapter]
    RT[Trusted runtime]

    NP -->|ticket, scope, review| DS
    DS -->|manifest schema + dsl_check| DP
    DP -->|versioned profile + manifest| AP
    AP --> CI
    AP --> PROBE
    PROBE -->|wellmanifest.dsl/findings/v1| CI
    CI -->|validated semantic payload| LLM
    LLM -->|strict proposed DSL| CI
    CI -->|authority checked separately| RT
```

## Responsibility boundaries

| Component | Owns | Must not own |
| --- | --- | --- |
| `wellmanifest/new-project` | repository workflow, tickets, bounded changes, review provenance | domain DSL semantics |
| `wellmanifest/dsl` | manifest kernel, cross-language invariants, diagnostics, conformance protocol | every domain grammar |
| Domain DSL repository | grammar/AST, semantics, compatibility, migrations, domain profiles | generic repository governance |
| Adopting project | pinned manifest/profile versions and local bindings | upstream contract redefinition |
| Evidence producer | observations normalized by a deterministic adapter | publication authority or waivers |
| LLM adapter | provider transport and structured-output negotiation | acceptance, authority, execution, receipts |
| Trusted runtime | semantic validation, capability binding, authority, effects, receipts | accepting malformed model output |

Dependency direction is one-way: a domain profile imports the neutral kernel;
the kernel never imports a domain implementation.

## Contract structure

```mermaid
flowchart TB
    M[dsl-manifest.json]
    I[Identity + SemVer]
    O[Owners + ownedPaths]
    S[Canonical source]
    A[Artifacts + sha256]
    P[Projections + mappings]
    E[Effect + authority model]
    L[LLM boundary]
    D[Command + error + critical documentation]
    F[Required findings producers + blocking policy]
    C[Conformance levels + commands]

    M --> I
    M --> O
    M --> S
    M --> A
    M --> P
    M --> E
    M --> L
    M --> D
    M --> F
    M --> C
```

The JSON Schema owns the closed data shape. `dsl_check.py` owns semantic checks
that JSON Schema cannot reliably perform across repository state:

- resolving paths without leaving the repository;
- hashing exact artifact bytes;
- matching artifacts to ownership globs;
- finding multiple manifest owners;
- inspecting Git changes;
- recognizing embedded `dsl` fences;
- enforcing conditional LLM and authority invariants;
- deriving exact case-sensitive help paths and validating page content;
- joining normalized findings to the owning manifest and exact revision;
- failing closed on missing/unevaluable producers and unresolved security.

## Discoverable help and findings boundary

```mermaid
flowchart LR
    CAT[Manifest catalogs]
    CMD[docs/COMMAND.md]
    ERR[docs/ERROR/CODE.md]
    CRIT[docs/CRITICAL/CODE.md]
    TP[twin-probes or another detector]
    AD[Deterministic adapter]
    FR[findings/v1 report]
    G[Protected dsl_check gate]
    PUB{Publish?}

    CAT --> CMD
    CAT --> ERR
    CAT --> CRIT
    TP --> AD --> FR --> G
    CMD --> G
    ERR --> G
    CRIT --> G
    G -->|all required evidence evaluable and no open blocker| PUB
    G -->|missing docs/evidence or open security| BLOCK[Block]
```

The manifest, not a detector, defines the stable command/error/security
vocabulary. A detector finding joins to that vocabulary through its exact
`helpPath`. Its evidence joins to repository files through relative paths and
SHA-256 values. The report also binds the owning manifest and gated Git SHA.

The adapter is deliberately replaceable: `twin-probes`, validator-agent, or a
domain checker can emit their own native format, then normalize it. The
protected `dsl_check gate` remains the only publication decision point. A local
pre-push hook can call the same command for fast feedback but is not a trust
boundary because it can be bypassed.

## Canonical representation and projections

The canonical representation is the semantic source of truth. Text, YAML,
TOON, JSON, Protobuf, or generated SDKs can be projections, but only one
representation is canonical for a given manifest version.

```mermaid
flowchart LR
    CAN[Canonical semantic model]
    TXT[Review text]
    JSON[JSON AST]
    PB[Protobuf binding]
    SDK[Generated SDK]

    CAN -->|declared projection| TXT
    CAN -->|declared projection| JSON
    CAN -->|declared projection| PB
    CAN -->|generated artifact| SDK
    TXT -. lossless only if declared .-> CAN
    JSON -. lossless only if declared .-> CAN
```

This avoids a common failure mode where a textual grammar, JSON Schema, and
runtime parser evolve as three independent sources of truth.

## Initial worked profile: new-project contributor DSL

The DSL embedded in `wellmanifest/new-project/CONTRIBUTING.md` is classified as:

| Property | Standard description |
| --- | --- |
| Stable ID | `wellmanifest.new-project.contributing` |
| Domain | `software-governance` |
| Canonical kind | `markdown-embedded` |
| Selector | `fenced-code:dsl` |
| Native version | `9` |
| Manifest version | `9.0.0` |
| Effect model | `declarative-policy` |
| Unknown policy | `reject` |
| LLM boundary | `none` for the language itself |
| Runtime | deterministic governance validator, not arbitrary DSL execution |

The inspected document has a metadata header and rule blocks with stable IDs.
Its major constructs are `DOCUMENT`, `RULE`, `WHEN`, `DO`, `FORBID`, `ASSERT`,
`NEXT`, `STATE`, and `TRANSITION`. Environment declarations add `ENV_FILE`,
`VARIABLE`, and `SECRET`.

```mermaid
flowchart LR
    MD[CONTRIBUTING.md]
    SEL[fenced-code:dsl selector]
    DSL[Policy/Procedure DSL blocks]
    VAL[governance_check.py]
    RES[Stable GOV diagnostics]

    MD --> SEL
    SEL --> DSL
    DSL -->|normative constraints| VAL
    VAL --> RES
```

The Markdown is the normative source. The validator is an enforcement adapter.
The manifest binds the exact Markdown bytes and declares the adapter as a
conformance command. It does not imply that every `DO` line is a shell command
or that the DSL may execute arbitrary model output.

`CONTRIBUTING.md` can also be supplied as a referenced context artifact inside
an LLM exchange defined by a separate LLM Exchange profile. That use does not
change the contributor DSL's own `llm.mode` from `none`.

## Repository topology

```text
wellmanifest/dsl/
├── spec/                 normative requirements
├── schemas/              strict machine contracts
├── profiles/             future independently versioned profiles
├── examples/             future valid/invalid adoption fixtures
├── src/                  dependency-free deterministic tooling
├── tests/                future cross-project conformance suite
├── docs/                 architecture and adoption guidance
└── project/              repository governance evidence
```

Ticket 001 introduces the standard, schema, validator, and diagrams. A later
ticket will add this repository's own `dsl-manifest.json`, fixtures, and CI so
the standard is governed by its own change gate. A separate ticket in
`wellmanifest/new-project` will adopt a manifest for `CONTRIBUTING.md`; cross-
repository governance evidence must not be stored in this repository.

## Profile family

The neutral kernel is intended to host mappings for profiles such as:

```mermaid
flowchart TB
    K[DSL manifest kernel]
    SRC[Source + provenance]
    INT[Intent + evidence]
    Q[Query + result]
    T[Twin + observation + state]
    PLAN[Plan + proposal]
    AUTH[Authority + capability]
    OP[Operation + execution]
    VER[Verification + receipt]
    LX[LLM exchange]

    K --> SRC
    K --> INT
    K --> Q
    K --> T
    K --> PLAN
    K --> AUTH
    K --> OP
    K --> VER
    K --> LX
```

Profiles may reference one another, but authority, execution, verification, and
accepted state remain distinct responsibilities.
