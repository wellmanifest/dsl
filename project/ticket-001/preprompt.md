# Ticket preprompt

- **Task ID**: ticket-001
- **Task title**: Establish reusable DSL standards and conformance gate
- **Created**: 2026-08-09T11:07:29Z

Keep executable implementation outside this governance/evidence directory.
Read a human-owned user-*.md file only when one exists.

## Technical directives

- Adopt `wellmanifest/new-project` from the immutable revision recorded in
  `.governance/manifest.lock.json`.
- Use JSON Schema draft 2020-12 for the canonical manifest contract.
- Keep the validator dependency-free and fail closed with stable diagnostic
  codes.
- Treat JSON as the canonical machine representation; YAML, TOON, Protobuf, and
  textual DSL syntaxes may be declared as projections or bindings.
- Require every semantic LLM request and response to name a strict DSL schema;
  provider protocols remain transport adapters.
- Preserve the separation between proposal, authority, execution, and receipt.
- Do not copy domain contracts from source projects into the kernel.

## Reference projects

- `wellmanifest/new-project`
- `tom-sapletta-com/onlyDSL`
- `tom-sapletta-com/dodsl`
- `subactor/todo2code`
- `bioxfoundry/twin-dsl`
- `if-uri/urirun`
- `oqlos/oql`, `oqlos/testql`, `subactor/eql`, `subactor/autonom`
- `semcod/planfile`
