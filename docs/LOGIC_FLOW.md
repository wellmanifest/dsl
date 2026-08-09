# Logic flows

## Creating a DSL

```mermaid
flowchart TD
    A[Define domain problem and non-goals]
    B[Assign stable namespace and owner]
    C[Choose one canonical representation]
    D[Declare effect and unknown policies]
    E{Is this an LLM boundary?}
    F[Declare strict request/response schemas]
    G[Set model authority to propose-only]
    H[Create dsl-manifest.json]
    I[Bind normative artifacts by SHA-256]
    J[Add deterministic conformance commands]
    K[Run dsl_check validate]
    L{Pass?}
    M[Publish pre-stable or versioned DSL]
    N[Fix stable diagnostics]

    A --> B --> C --> D --> E
    E -->|yes| F --> G --> H
    E -->|no| H
    H --> I --> J --> K --> L
    L -->|yes| M
    L -->|no| N --> K
```

Creation fails closed when ownership, source identity, authority, or canonical
representation is unresolved.

## Changing a DSL

```mermaid
sequenceDiagram
    participant Dev as Contributor/agent
    participant Git as Git diff
    participant Gate as dsl_check
    participant Manifest as DSL manifest
    participant Review as Independent review

    Dev->>Git: change grammar/schema/source/profile
    Gate->>Git: read accepted base...head
    Gate->>Manifest: resolve exactly one owner
    Gate->>Manifest: verify artifact path and digest
    alt unclaimed, overlapping, or stale
        Gate-->>Dev: stable DSL-* diagnostic; block
    else structurally and semantically valid
        Gate-->>Review: deterministic conformance evidence
        Review-->>Dev: approve/reject exact head
    end
```

An updated artifact necessarily changes its SHA-256 digest, forcing an explicit
manifest update. This makes silent grammar or schema drift observable even when
the file still parses.

Compatibility classification remains a reviewer decision backed by explicit
rules. A model MAY suggest `major`, `minor`, or `patch`, but cannot approve its
own classification.

## Changed-file ownership algorithm

For each changed path, `dsl_check changes` performs:

1. Discover all `dsl-manifest.json` files.
2. Validate every manifest and its current artifact hashes.
3. Classify the changed file as DSL-sensitive if it:
   - is covered by any manifest `ownedPaths`;
   - is a manifest or `*schema.json`;
   - uses a known grammar/DSL extension;
   - is under a DSL, schema, grammar, or profile directory; or
   - contains a Markdown `dsl` fence.
4. Require exactly one manifest owner.
5. Require the changed file to be digest-bound as an artifact, except for its
   owner manifest itself.

The changed paths normally come from an accepted Git base and exact head. In a
minimal container without Git they may be passed as repeatable
`--changed-file` values by the protected workflow; an LLM must never construct
the authoritative change list.

```mermaid
flowchart TD
    C[Changed file]
    S{DSL-sensitive?}
    O[Match ownedPaths]
    N{Owner count}
    A{Digest-bound artifact or owner manifest?}
    P[Pass ownership gate]
    E1[DSL-OWNER-001]
    E2[DSL-OWNER-002]
    E3[DSL-ARTIFACT-002]

    C --> S
    S -->|no| P
    S -->|yes| O --> N
    N -->|0| E1
    N -->|more than 1| E2
    N -->|1| A
    A -->|no| E3
    A -->|yes| P
```

## LLM request and response flow

```mermaid
sequenceDiagram
    participant Runtime
    participant Schema as DSL schemas
    participant Adapter as Provider adapter
    participant LLM
    participant Authority
    participant Executor

    Runtime->>Schema: build typed request DSL
    Schema-->>Runtime: request valid + semantic hash
    Runtime->>Adapter: serialized DSL payload
    Adapter->>LLM: vendor transport wrapper
    LLM-->>Adapter: structured candidate
    Adapter->>Schema: parse exact response DSL
    alt invalid or ungrounded
        Schema-->>Runtime: InvalidLlmResponseDSL
    else valid proposal
        Schema-->>Runtime: proposed response DSL
        Runtime->>Authority: capability + policy preflight
        alt denied
            Authority-->>Runtime: denial receipt
        else granted
            Authority->>Executor: exact fixed operation binding
            Executor-->>Runtime: execution + verification receipt
        end
    end
```

Natural language can appear only as a typed source payload when allowed by the
manifest. Provider metadata, token counts, costs, timestamps, and raw response
hashes belong to a runtime-owned receipt and cannot alter the semantic result
hash.

## Applying the standard to `new-project/CONTRIBUTING.md`

The current contributor document already contains the language definition and
its semantics. Adoption does not require rewriting those 92 rules.

```mermaid
flowchart TD
    C[Existing CONTRIBUTING.md]
    I[Create repository-local dsl-manifest.json]
    D[Calculate exact source digest]
    B[Bind CONTRIBUTING.md as normative-source]
    V[Declare governance-check command]
    G[Run dsl_check validate]
    H[Run dsl_check changes in PR]

    C --> I --> D --> B --> V --> G --> H
```

The repository-local adoption ticket should:

- use `wellmanifest.new-project.contributing` as the stable ID;
- map native `VERSION 9` to manifest SemVer `9.0.0`;
- declare `markdown-embedded` plus `fenced-code:dsl`;
- bind `CONTRIBUTING.md` by exact SHA-256;
- classify it as `declarative-policy`;
- preserve the existing deterministic governance checker;
- add `dsl_check changes` to the protected PR checks.

The example digest in the normative standard describes the locally inspected
bytes. The adoption ticket MUST recompute it at its accepted Git base and MUST
not copy the example digest blindly.

## Failure behavior

| Code | Meaning |
| --- | --- |
| `DSL-MANIFEST-001` | Invalid, missing, unknown, or inconsistent manifest field. |
| `DSL-PATH-001` | Absolute, parent-traversing, backslash, or escaping path. |
| `DSL-PATH-002` | Referenced repository file does not exist. |
| `DSL-HASH-001` | Artifact bytes no longer match the manifest digest. |
| `DSL-HASH-002` | Digest is not canonical `sha256:<hex>`. |
| `DSL-OWNER-001` | Changed DSL-sensitive file has no manifest owner. |
| `DSL-OWNER-002` | DSL identity or changed file has multiple owners. |
| `DSL-ARTIFACT-001` | Source/artifact is outside its declared contract. |
| `DSL-ARTIFACT-002` | Changed DSL file is owned but not digest-bound. |
| `DSL-COMPAT-001` | Version or lifecycle compatibility declaration is invalid. |
| `DSL-AUTH-001` | Effect and authority declarations conflict. |
| `DSL-LLM-001` | LLM schemas, strictness, NL policy, or model authority is invalid. |
| `DSL-CONFORMANCE-001` | Claimed conformance evidence is missing. |
| `DSL-GIT-001` | Accepted-base/head change set cannot be established. |

Diagnostics are deterministic. Corrective text from an LLM is advisory and
must pass the same gate as a human-authored change.
