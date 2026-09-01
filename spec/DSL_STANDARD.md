# Wellmanifest DSL Standard 0.1

Status: pre-stable normative draft
Manifest contract: `wellmanifest.dsl/manifest/v1`

The key words MUST, MUST NOT, REQUIRED, SHALL, SHALL NOT, SHOULD, SHOULD NOT,
RECOMMENDED, MAY, and OPTIONAL are normative when written in uppercase.

## 1. Purpose

This standard makes independently developed domain-specific languages
discoverable, reviewable, reusable, and mechanically governable. It does not
replace their domain semantics with one universal grammar.

A conforming DSL consists of:

1. one canonical semantic representation;
2. a versioned manifest declaring ownership and boundaries;
3. immutable references to every normative contract artifact;
4. explicit compatibility and authority rules;
5. deterministic conformance checks;
6. optional domain profiles and syntax projections.

Transport protocols such as HTTP, MCP, A2A, JSON-RPC, gRPC, NATS, and files are
bindings. They MUST NOT redefine the semantic meaning of a DSL document.

## 2. Conformance language

### 2.1 DSL identity

Every DSL MUST have a stable, globally namespaced `id`. Short names such as
`OQL`, `DQL`, or `EQL` MAY be display names but MUST NOT be global identifiers.

Recommended identifiers use a reverse-domain or repository namespace:

```text
wellmanifest.new-project.contributing
subactor.intent
bioxfoundry.twin
oqlos.hardware-scenario
```

The manifest `version` MUST use Semantic Versioning:

- MAJOR: incompatible syntax, semantic, authority, or canonical-model change;
- MINOR: backward-compatible construct or capability;
- PATCH: compatible clarification or correction.

A native integer or domain version MAY be retained as
`source.declaredVersion`, but it does not replace the manifest SemVer.

### 2.2 Ownership

Every manifest MUST name at least one owner and MUST declare repository-relative
`ownedPaths`. A governed path MUST resolve to exactly one DSL manifest within a
conformance run.

Ownership means responsibility for:

- semantics and compatibility;
- normative artifacts and their digests;
- migration guidance;
- conformance fixtures and diagnostics;
- deprecation and removal decisions.

Importing a profile does not transfer its ownership to the importing project.

### 2.3 Canonical representation

Exactly one representation MUST be declared canonical. Supported canonical
kinds include:

- `json-ast`;
- `protobuf`;
- `text`;
- `markdown-embedded`;
- `other` with an explicit media type.

YAML, TOON, graphical editors, generated code, prompts, and pretty text SHOULD
normally be declared as projections. A projection MUST state its direction and
whether round-tripping is lossless.

For JSON AST documents, canonical semantic hashing SHOULD use RFC 8785 JSON
Canonicalization. Source artifacts are hashed from their exact bytes.

### 2.4 Artifact integrity

Each normative source, schema, grammar, parser contract, serializer contract,
or profile MUST appear in `artifacts` with a digest formatted as:

```text
sha256:<64 lowercase hexadecimal characters>
```

Changing an artifact without updating the manifest digest MUST fail with
`DSL-HASH-001`. An artifact path MUST stay inside the repository and MUST match
one of the manifest's `ownedPaths`.

Generated timestamps, provider names, token counts, durations, and costs MUST
NOT influence a semantic artifact digest.

### 2.5 Provenance

The `source` block identifies the repository, path, optional immutable revision,
native declared version, canonical kind, media type, and selectors for embedded
languages.

An embedded DSL MUST define how its normative fragments are selected. For
Markdown, a selector such as `fenced-code:dsl` identifies fenced code blocks
without treating surrounding explanatory prose as executable syntax.

### 2.6 Semantic state and authority

A manifest MUST select one effect model:

- `descriptive`: represents facts or models and requests no effect;
- `declarative-policy`: declares constraints enforced by a separate trusted
  runtime;
- `propose-only`: may produce candidates but cannot authorize or execute them;
- `controlled-effects`: may describe effectful operations, which require an
  external authority contract.

`controlled-effects` MUST declare `authoritySchema`. The language model, parser,
or DSL document MUST NOT mint its own authority.

The policy for unknown data MUST be explicit. `preserve` is RECOMMENDED for
evidence, queries, digital twins, and LLM interactions; unknown values MUST NOT
be silently guessed.

### 2.7 LLM boundary

The semantic payload of every request sent to an LLM and every response accepted
from an LLM MUST be a document conforming to a named DSL schema. Vendor message
objects are transport wrappers and MAY contain the serialized DSL payload.

The `llm.mode` value declares whether a language itself is an LLM boundary:

- `none`;
- `input`;
- `output`;
- `bidirectional`.

For `input` and `bidirectional`, `requestSchemas` MUST be non-empty. For `output`
and `bidirectional`, `responseSchemas` MUST be non-empty. `strict` MUST be true.

Every enabled LLM **decision boundary** MUST be `bidirectional` and declare one
of two closed `decisionProtocol` values:

- `dsl-input-output`: the model receives a named request DSL and returns a
  named response DSL; natural language is forbidden;
- `nl-to-dsl-input-output`: a human may supply natural language only inside a
  declared typed source schema, and the runtime translates it to the named
  request DSL before the model decision. The model still returns only the
  named response DSL.

`decisionProtocol=none` is required when `llm.mode=none`. A direct free-text
prompt, an untyped response, or a heuristic fallback that performs an effect is
not a conforming decision boundary.

Natural language is either:

- `forbidden`; or
- `typed-source-only`, carried inside a schema-declared source payload with
  language, media type, provenance, and digest.

When LLM use is enabled, `modelAuthority` MUST be `propose-only`. Runtime-owned
fields include identity, provenance, lifecycle elevation, authority, execution
status, provider audit, and receipts. A malformed response MUST become an
explicit invalid-response artifact; it MUST NOT be silently coerced.

### 2.8 Compatibility and lifecycle

A stable DSL change MUST document whether it is breaking, additive, or a fix.
The manifest declares the required SemVer increment for each category.

The following are breaking unless a profile specifies a stricter rule:

- changing the canonical representation;
- removing or renaming a required construct;
- changing identifier or hash semantics;
- widening model authority;
- changing accepted unknown/null/missing semantics;
- changing an operation from read-only or propose-only to effectful;
- accepting previously rejected ambiguous input;
- removing required provenance or citations.

Deprecated DSLs MUST retain an owner and migration target until their declared
support period ends.

### 2.9 Discoverable commands, errors, and critical issues

Every manifest MUST declare `documentation.vocabularyKind` as `commands` or
`documents`. A command language MUST declare its complete public vocabulary in
`documentation.commands`. A document-only language MAY use an empty command
catalog; its JSON Schema variants and deterministic examples are its
vocabulary. This exception MUST NOT be used to hide a parser or CLI command.

Command names MUST use uppercase ASCII with optional digits and underscores.
Each command MUST have one exact, case-sensitive page:

```text
docs/<COMMAND>.md
```

The page title MUST be `# <COMMAND>` and it MUST contain non-empty `Purpose`,
`Syntax`, `Inputs`, `Outputs`, `Errors`, and `Examples` sections.

Runtime error codes MUST be declared in `documentation.errorCodes` and use the
exact path `docs/ERROR/<CODE>.md`. Security and critical codes MUST be declared
in `documentation.criticalCodes` and use
`docs/CRITICAL/<CODE>.md`. Error pages MUST contain `Meaning`, `Cause`, and
`Resolution`; critical pages MUST contain `Risk`, `Detection`, `Remediation`,
and `Verification`. These pages are normative `documentation` artifacts and
MUST be covered by `ownedPaths` and bound by SHA-256.

Codes MUST use uppercase hyphen-separated identifiers. A code cannot be both an
ordinary error and a critical/security code. Paths are derived from the catalog,
not supplied as aliases, so a diagnostic can always return a direct help path.

The catalog MUST be complete. A representation whose vocabulary cannot be
derived generically MUST provide a deterministic conformance command that
compares its grammar, schema, or parser registry with the manifest catalog.
An LLM assertion that the catalog is complete is not conformance evidence.

### 2.10 Normalized findings and publication policy

Every manifest MUST declare `findingPolicy` for reports conforming to
`wellmanifest.dsl/findings/v1`. At least one security-capable deterministic
producer is required. `securityProducers` MUST be a subset of
`requiredProducers`; `requireEvaluable` and `blockUnresolvedSecurity` MUST be
true, and `blockingSeverities` MUST include `critical`.

The reusable report contract is
`schemas/dsl-manifest.schema.json#/$defs/findingsReport`. It is a closed Draft
2020-12 object and binds:

- producer ID, version, and deterministic adapter;
- repository, exact 40-character revision, and owning manifest path;
- an explicit `evaluable` result and failure reason;
- stable finding ID and code, severity, security classification, source path,
  exact help path, message, and resolution state;
- repository-relative evidence paths with SHA-256 digests.

An unevaluable required producer MUST fail closed. An unresolved finding MUST
block publication when its severity is listed in `blockingSeverities` or it is
classified as security. Creating `docs/CRITICAL/<CODE>.md` makes remediation
discoverable; it never waives or resolves the finding.

Tools such as `subactor/twin-probes` and producers of
`subactor.autonom-cycle/v1` MAY generate evidence. They MUST pass through a
deterministic adapter to the normalized report and remain evidence producers,
not trust roots. Only the protected deterministic gate decides the publication
verdict.

### 2.11 Proportional publication tier

Every manifest MUST declare `publicationPolicy`. The deterministic checker
derives exactly one tier; a repository cannot select a lower or higher tier:

| Tier | Derived condition | Additional required controls |
| --- | --- | --- |
| `basic` | descriptive semantics, no LLM boundary, no runtime claim | deterministic conformance |
| `review` | declarative/propose-only semantics, any LLM boundary, or runtime/LLM conformance | independent review |
| `controlled` | controlled effects | independent review, external authority, runtime isolation |

An LLM finding MAY add evidence or block publication through `findingPolicy`.
It MUST NOT reduce the derived tier or replace its deterministic controls.

### 2.12 Composed-standard lock

A manifest that composes other standards SHOULD include the closed
`wellmanifest.standards-lock/v1` object defined at
`schemas/dsl-manifest.schema.json#/$defs/standardsLock`. Every entry binds a
standard identifier and SemVer to a repository, exact 40-character Git revision
and one or more URI contract references with SHA-256 digests. Tags, branches,
working-tree paths and draft files without an immutable revision are forbidden
as lock substitutes.

The same standard ID and contract reference MUST appear at most once in a lock.
A draft standard is omitted until an immutable revision exists; its absence
must remain a visible integration prerequisite rather than a fabricated pin.

### 2.13 Grammar and parser implementation profiles

A grammar notation or parser library is not the identity of a DSL. A language
MUST keep these layers separately reviewable:

1. canonical grammar and normative semantics;
2. optional generation projection such as request-only GBNF;
3. parser implementation or generated parser;
4. AST adapter producing the canonical, closed model;
5. semantic validation and deterministic conformance;
6. runtime effects behind the declared authority boundary.

ABNF, EBNF, PEG or another grammar may be the normative syntax artifact. A
library-specific grammar MUST be declared as a `grammar`, `parser-contract` or
projection unless it is itself the canonical source. Generated parser code
MUST be reproducible and digest-bound. Replacing Lark with TatSu, pest with
ANTLR, or nearley with Ohm is compatible only when both implementations accept
the same valid fixtures, reject the same invalid fixtures with equivalent
stable diagnostics, and normalize to the same canonical representation.

Runtime grammar compilation is an implementation capability, not authority to
change the language. A grammar proposed by an LLM MUST remain an untrusted
candidate until its own schema/grammar checks, ambiguity and complexity bounds,
conformance suite and independent review pass. GBNF constrains model output; it
does not replace the full parser grammar or the closed output schema. MCP is a
transport for these artifacts and validation operations, not a semantic or
approval layer.

## 3. Manifest location

The default filename is `dsl-manifest.json`. A monorepo MAY contain multiple
manifests. Their `ownedPaths` MUST NOT overlap for a changed DSL artifact.

All paths are interpreted relative to the repository root, not relative to the
manifest file. Absolute paths and `..` segments are forbidden.

The authoritative JSON Schema is
[`schemas/dsl-manifest.schema.json`](../schemas/dsl-manifest.schema.json).
The first reusable document-profile contract is
[`profiles/wellmanifest-profiles.schema.json`](../profiles/wellmanifest-profiles.schema.json).

## 4. Conformance levels

Manifests declare one or more levels:

| Level | Requirement |
| --- | --- |
| `manifest` | Strict schema, paths, ownership, versions, and digests pass. |
| `contract` | Canonical documents and valid/invalid examples are checked. |
| `runtime` | Parser, serializer, and semantic validator behavior is checked. |
| `llm-boundary` | Request/response schemas and propose-only invariants pass. |

A project MUST NOT claim a level for which it has no deterministic command or
evidence. LLM-generated review MAY supplement conformance but MUST NOT be its
trust root.

## 5. Change gate

For every new or changed DSL, CI MUST run:

```bash
python3 src/dsl_check.py validate <manifest-or-repository>
python3 src/dsl_check.py standards <manifest-or-repository>
python3 src/dsl_check.py changes --root . --base <accepted-base> --head <head>
python3 src/dsl_check.py gate --root . --findings <producer-report.json>
```

A Git-aware protected workflow SHOULD use `--base` and `--head`. A networkless
or Git-free validation container MAY receive an already protected, explicit
change set through repeatable `--changed-file <relative-path>` arguments. The
producer of that list remains part of the trusted CI boundary.

The gate checks:

1. strict manifest structure and conditional fields;
2. repository confinement;
3. artifact existence and SHA-256 binding;
4. unique ownership of changed DSL-sensitive files;
5. presence of changed contract artifacts in the owner manifest;
6. LLM and authority invariants;
7. command/document vocabulary mode plus exact command, error, and critical
   help paths, titles, sections, ownership,
   and digests;
8. the publication tier derived from effects, LLM mode and conformance claims;
9. immutable, unique standard and contract pins when a standards lock exists;
10. normalized finding structure and repository/revision binding;
11. presence and evaluability of every required producer;
12. absence of unresolved blocking or security findings.

The `gate` command resolves the gated revision from Git `HEAD`. A protected
Git-free environment MUST pass the exact revision with `--revision`; the
revision value must come from the protected checkout or CI event, never from an
LLM or from the findings producer itself. One `--findings` argument is supplied
for every producer/manifest pair.

Stable diagnostic codes are part of the conformance interface.

## 6. Worked composition: `new-project/CONTRIBUTING.md`

`wellmanifest/new-project/CONTRIBUTING.md` is an embedded declarative
Policy/Procedure DSL and is the first worked composition of this standard. Its
language contract is `wellmanifest.policy/v1`, with `policy-sh@1` retained as a
runtime compatibility alias. The integer below is the consuming document
revision and MUST NOT be compared to the Policy DSL language major or manifest
SemVer.

Its observed document contract declares:

```dsl
DOCUMENT CONTRIBUTING
VERSION 13
LANGUAGE PL
MODE PROCEDURAL
PURPOSE "proces pracy nad repozytorium"
POLICY "POLICY.md"
```

Its vocabulary contains document metadata, environment declarations, rules,
conditions, actions, prohibitions, assertions, state declarations, and
transitions. The normative blocks use constructs including:

```text
DOCUMENT, VERSION, LANGUAGE, MODE, PURPOSE, POLICY
ENV_FILE, VARIABLE, SECRET
RULE, TYPE, WHEN, DO, REQUIRE, ALLOW, FORBID, ASSERT, NEXT
STATE, TRANSITION
```

The DSL is declarative and is not executed as arbitrary code. Markdown fences
are the normative human/agent representation; `wellmanifest/policy-dsl`
defines their grammar, closed Policy IR, constrained LLM projection and shared
conformance fixtures. Deterministic Python governance validation is a separate
enforcement adapter. Therefore its effect model is `declarative-policy`, not
`controlled-effects`.

Its `ENV_FILE`, `VARIABLE` and `SECRET` records are a legacy compatibility
surface. They are neither an extension nor an implementation of Env DSL 1.
Env DSL has a closed assignment grammar, headers, layering and bounded
expression evaluator. A conforming Env DSL runtime may produce inert values
which a typed adapter supplies to the Policy DSL runtime; neither language
inherits the other's grammar or authority.

At the pinned `new-project` v0.18.0 revision, the document contains 25 `dsl`
fences and 110 stable lines beginning with `RULE`. Of those declarations, 108 are inside
the selected `dsl` fences; `C-CONTEXT-001` and `C-CONTEXT-002` are inside a
`bash` fence and are therefore not selected by `fenced-code:dsl`. This existing
label mismatch is recorded rather than silently broadening the selector to all
shell examples. The following pre-adoption candidate binds those exact source
bytes and declares the required vocabulary and finding policy:

```json
{
  "$schema": "https://wellmanifest.dev/schemas/dsl-manifest/v1",
  "schema": "wellmanifest.dsl/manifest/v1",
  "id": "wellmanifest.new-project.contributing",
  "name": "new-project CONTRIBUTING Policy/Procedure DSL",
  "version": "13.0.0",
  "status": "stable",
  "purpose": "Governed contributor and autonomous-agent workflow",
  "domain": "software-governance",
  "owners": [
    {
      "kind": "repository",
      "id": "github:wellmanifest/new-project",
      "responsibilities": ["semantics", "validation", "compatibility"]
    }
  ],
  "source": {
    "repository": "https://github.com/wellmanifest/new-project",
    "path": "CONTRIBUTING.md",
    "declaredVersion": "13",
    "canonical": "markdown-embedded",
    "mediaType": "text/markdown",
    "selectors": ["fenced-code:dsl"]
  },
  "ownedPaths": ["CONTRIBUTING.md", "dsl-manifest.json", "docs/**"],
  "artifacts": [
    {
      "path": "CONTRIBUTING.md",
      "role": "normative-source",
      "digest": "sha256:d39b4ad8ac060f918dd6906ec484cb0e134777c9e17fecc0c4b1b464df50d34b"
    }
  ],
  "namespaces": [
    {"prefix": "new-project", "uri": "https://github.com/wellmanifest/new-project/"}
  ],
  "projections": [],
  "lifecycle": {
    "compatibility": "semver",
    "stability": "stable",
    "breaking": "major",
    "additive": "minor",
    "fix": "patch"
  },
  "semantics": {
    "effectModel": "declarative-policy",
    "unknownPolicy": "reject",
    "authoritySchema": null
  },
  "llm": {
    "mode": "none",
    "requestSchemas": [],
    "responseSchemas": [],
    "naturalLanguage": "typed-source-only",
    "sourceSchema": "wellmanifest.dsl/source/v1",
    "decisionProtocol": "none",
    "modelAuthority": "none",
    "strict": true
  },
  "documentation": {
    "vocabularyKind": "documents",
    "commandRoot": "docs",
    "errorRoot": "docs/ERROR",
    "criticalRoot": "docs/CRITICAL",
    "commands": [],
    "errorCodes": [],
    "criticalCodes": []
  },
  "findingPolicy": {
    "schema": "wellmanifest.dsl/findings/v1",
    "requiredProducers": ["wellmanifest.new-project.governance-check"],
    "securityProducers": ["wellmanifest.new-project.governance-check"],
    "blockingSeverities": ["critical"],
    "requireEvaluable": true,
    "blockUnresolvedSecurity": true
  },
  "publicationPolicy": {
    "declaredTier": "review",
    "deterministic": true,
    "independentReview": true,
    "externalAuthority": false,
    "runtimeIsolation": false
  },
  "conformance": {
    "levels": ["manifest", "contract", "runtime"],
    "commands": ["./project/governance-check.sh --actor agent"],
    "validExamples": [],
    "invalidExamples": []
  },
  "mappings": [
    {
      "standard": "wellmanifest/policy-dsl",
      "version": "0.1.0-dev",
      "relation": "implements",
      "uri": "https://github.com/wellmanifest/policy-dsl"
    },
    {
      "standard": "wellmanifest/env-dsl",
      "version": "0.1.0-dev",
      "relation": "compatible-with",
      "uri": "https://github.com/wellmanifest/env-dsl"
    }
  ]
}
```

This candidate describes the consuming profile; it does not transfer language
ownership away from `policy-dsl` or claim that `new-project` has adopted this
manifest. Adoption requires a target-owned ticket, immutable Policy DSL
revision, exact artifact digests and deterministic carrier validation. The two
policy-shaped rules still labelled as `bash` remain a source-label defect to be
fixed by `new-project`, not a reason to interpret arbitrary shell fences.

## 7. Reusable profile family

Domain profiles SHOULD extend the kernel instead of copying it. The closed
Draft 2020-12 contract in `profiles/wellmanifest-profiles.schema.json` defines:

- source and provenance;
- intent and evidence;
- query and terminal result;
- read-only, freshness-bounded observation;
- operation with multi-dimensional effects;
- external, plan-bound authority;
- verification with immutable evidence;
- terminal LLM exchange audit with application, project, provider, model and
  account profile identity;
- an accepted delivery plan compiled into an acyclic graph of bounded work
  slices, plus propose-only oversized-slice split request/results;
- session checkpoints, read-only resume observations and deterministic
  resume/recover/reject decisions;
- read-only repository/remote/account/fork observations and propose-only
  remote rebind decisions which carry registry IDs rather than credentials or
  invented URI routes; and
- typed tool action request/results bound to one versioned capability ID,
  declared effects, immutable input/output digests and terminal receipts.

Authored query objects intentionally do not select an account, provider or
model. The trusted registry owns that choice; the terminal LLM exchange records
what was actually used. Streaming deltas are telemetry artifacts. A terminal
result remains a separately schema-validated and hash-bound artifact.

Each profile variant is independently named, closed, bounded and versioned.
Schema validity is evidence only: no profile document grants execution
authority by itself.

Delivery-plan slice identifiers MUST be unique, every dependency MUST resolve
inside the accepted plan, and the dependency graph MUST be acyclic. A split
result MUST preserve the request's plan binding and declare the exact
dependency rebinding for its superseded slice. Resume decisions MUST bind a
fresh observation of the referenced checkpoint. Remote decisions MUST repeat
an observed binding and MUST NOT contain credentials or arbitrary transport
URIs. Tool results MUST repeat the request action and capability identifiers.
These joins are deterministic validation rules; an LLM may propose documents
but MUST NOT decide their validity, authority or execution.
