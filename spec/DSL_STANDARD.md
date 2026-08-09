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

Every manifest MUST declare its complete public command vocabulary in
`documentation.commands`. Command names MUST use uppercase ASCII with optional
digits and underscores. Each command MUST have one exact, case-sensitive page:

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

## 3. Manifest location

The default filename is `dsl-manifest.json`. A monorepo MAY contain multiple
manifests. Their `ownedPaths` MUST NOT overlap for a changed DSL artifact.

All paths are interpreted relative to the repository root, not relative to the
manifest file. Absolute paths and `..` segments are forbidden.

The authoritative JSON Schema is
[`schemas/dsl-manifest.schema.json`](../schemas/dsl-manifest.schema.json).

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
7. exact command, error, and critical help paths, titles, sections, ownership,
   and digests;
8. normalized finding structure and repository/revision binding;
9. presence and evaluability of every required producer;
10. absence of unresolved blocking or security findings.

The `gate` command resolves the gated revision from Git `HEAD`. A protected
Git-free environment MUST pass the exact revision with `--revision`; the
revision value must come from the protected checkout or CI event, never from an
LLM or from the findings producer itself. One `--findings` argument is supplied
for every producer/manifest pair.

Stable diagnostic codes are part of the conformance interface.

## 6. Worked profile: `new-project/CONTRIBUTING.md`

`wellmanifest/new-project/CONTRIBUTING.md` is an embedded declarative
Policy/Procedure DSL and is the first worked profile of this standard.

Its observed document contract declares:

```dsl
DOCUMENT CONTRIBUTING
VERSION 9
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
are the normative human/agent representation; deterministic Python governance
validation is a separate enforcement adapter. Therefore its effect model is
`declarative-policy`, not `controlled-effects`.

At the locally inspected revision, the document contains 23 `dsl` fences and
92 stable lines beginning with `RULE`. Of those declarations, 90 are inside
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
  "version": "9.0.0",
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
    "declaredVersion": "9",
    "canonical": "markdown-embedded",
    "mediaType": "text/markdown",
    "selectors": ["fenced-code:dsl"]
  },
  "ownedPaths": ["CONTRIBUTING.md", "dsl-manifest.json", "docs/**"],
  "artifacts": [
    {
      "path": "CONTRIBUTING.md",
      "role": "normative-source",
      "digest": "sha256:6ce6b04093fd2f059dee3064d33f43648cb9404222c8aa7984b422d693c8214b"
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
    "modelAuthority": "none",
    "strict": true
  },
  "documentation": {
    "commandRoot": "docs",
    "errorRoot": "docs/ERROR",
    "criticalRoot": "docs/CRITICAL",
    "commands": [
      "DOCUMENT", "VERSION", "LANGUAGE", "MODE", "PURPOSE", "POLICY",
      "ENV_FILE", "VARIABLE", "SECRET", "RULE", "TYPE", "WHEN", "DO",
      "REQUIRE", "ALLOW", "FORBID", "ASSERT", "NEXT", "STATE", "TRANSITION"
    ],
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
  "conformance": {
    "levels": ["manifest", "contract", "runtime"],
    "commands": ["./project/governance-check.sh --actor agent"],
    "validExamples": [],
    "invalidExamples": []
  },
  "mappings": []
}
```

This candidate describes the existing language; it does not claim that
`new-project` has already adopted or passed the manifest. Adoption requires a
separate ticket that creates and digest-binds every declared command page,
declares the producer's stable error/critical catalog, adds those pages to
`artifacts`, and recomputes every digest at the accepted repository revision.

## 7. Profile evolution

Domain profiles SHOULD extend the kernel instead of copying it. Initial profile
candidates include:

- source and provenance;
- intent and evidence;
- query and query-result;
- twin definition, observation, and state;
- plan and proposal;
- authority and capability;
- operation and execution;
- verification and receipt;
- LLM exchange request and response.

Each profile remains independently versioned and maps to external standards
where appropriate.
