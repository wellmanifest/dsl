# Grammar toolchains as replaceable implementation profiles

The language contract comes first: canonical grammar, normative semantics,
closed AST/IR Schema, fixtures and stable diagnostics. A parser engine is a
replaceable implementation profile and never an authority boundary.

## Selection matrix

| Runtime | Tool | Contract fit | Prefer when |
| --- | --- | --- | --- |
| Python | [Lark](https://lark-parser.readthedocs.io/en/stable/parsers.html) | EBNF, LALR(1), Earley and standalone LALR generation | LALR for bounded throughput; Earley only when intentional grammar generality and ambiguity evidence are required |
| Python | [TatSu](https://tatsu.readthedocs.io/en/stable/intro.html) | EBNF input, PEG/Packrat parser, runtime compilation or generated Python | grammar must be compiled from a reviewed artifact in Python and ordered-choice semantics are acceptable |
| Python | [textX](https://textx.github.io/textX/grammar.html) | PEG grammar plus generated object meta-model | the canonical AST closely matches a domain object graph and reference resolution is central |
| Rust | [pest](https://pest.rs/book/grammars/grammars.html) | separate PEG grammar compiled with the service | a readable, statically bound text grammar and Rust runtime are desired |
| Rust | [nom](https://docs.rs/nom/latest/nom/) | parser combinators, streaming and zero-copy-oriented APIs | low-level or binary/streaming syntax needs hand-controlled parsers; it is not a grammar-file interchange format |
| JS/TS | [nearley](https://nearley.js.org/docs/grammar) | Earley grammar compiled by `nearleyc`, streaming parser | browser/Node parsing needs general CFG support and ambiguity is measured and rejected or resolved deterministically |
| JS/TS | [Ohm](https://github.com/ohmjs/ohm) | PEG language with grammar inheritance and semantic actions kept separate | web tooling benefits from grammar extension, visualization and modular semantics |
| multi-runtime | [ANTLR](https://www.antlr.org/about.html) | one grammar generates parse trees and visitors for several target runtimes | the same syntax must have independently tested clients in several supported languages |

Do not select only by syntax coverage. Record parser algorithm, worst-case
input limits, ambiguity policy, generated-code reproducibility, error mapping,
canonical AST adapter and the exact conformance suite in the owning manifest.
`nom` is intentionally classified as an implementation profile rather than a
grammar DSL.

## LLM to DSL boundary

The safe pipeline is:

```text
normative grammar + closed Schema + safe GBNF
                    |
                    v
LLM candidate -> deterministic parser -> canonical AST/IR -> semantic checks
                                                           |
                                                           v
                                                    propose-only POA plan
                                                           |
                                              independent effect authority
```

For high-throughput generation, prefer an unambiguous grammar with a bounded
linear parser profile (for example LALR(1) or a reviewed PEG). Cache compiled
grammars by the normative artifact digest. Earley/general CFG profiles require
explicit ambiguity and resource limits. A model-generated grammar is a source
proposal: validate it as data, compare its accepted language and fixtures, and
review it before it can replace a pinned artifact.

GBNF SHOULD expose only the safe candidate subset and its output MUST also pass
the closed JSON Schema. MCP MAY expose `get-schema`, `get-grammar`, `validate`
and `normalize` operations. An effectful POA command MUST remain a separate
operation with separate authority; neither a successful parse nor MCP tool
availability grants that authority.

## Env DSL selection example

Env DSL can carry inert, portable implementation choices. This is valid Env
DSL 1 data, not executable parser configuration:

```env
ENV_DSL_VERSION=1
ENV_DSL_NAMESPACE=WELLMANIFEST_PARSER_PROFILE
ENV_DSL_ENVIRONMENT=BASE
PARSER_RUNTIME=PYTHON
PARSER_ENGINE=LARK
PARSER_ALGORITHM=LALR
LLM_OUTPUT_CONSTRAINED=TRUE
CANONICAL_AST_REQUIRED=TRUE
```

A consumer validates and layers this document with the Env DSL runtime, then a
typed adapter maps the values to a known parser registry. Unknown engine names
are rejected. The adapter never imports a module named by arbitrary input and
never reads ambient variables absent from the explicit layered context.

## `new-project` composition

The DSL in `new-project/CONTRIBUTING.md` is `wellmanifest.policy/v1`, a
separate declarative-policy language standardized by `policy-dsl`. It consumes
an explicit environment context through an adapter:

```text
Env DSL 1 -> validated constant map -> typed adapter -> Policy DSL evaluator
```

It is not an Env DSL extension: Env DSL 1 has a closed record grammar that
does not admit `RULE`, `WHEN`, `DO`, arrays, quoted values or state transitions.
It is not an Env DSL implementation either. The current
`scripts/governance_env.py` contract accepts compatibility dotenv declarations,
quoted values, secrets and process-environment precedence, and does not require
Env DSL headers or implement Env DSL expressions and layering. It may remain a
backward-compatible adapter, but it MUST NOT claim Env DSL conformance until a
separate strict mode implements the full ABNF, semantics and shared fixtures.

