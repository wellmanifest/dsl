---
participant-id: agent:gemini
participant: gemini
role: agent
ticket: ticket-009
---
# Participant: gemini (AI agent)

## Understanding

Register `wellmanifest.code` standard into `profiles/dsl-manifest.json` `standardsLock` and `mappings` following the closure and merge of `wellmanifest/code-dsl#5`.

## Execution plan

1. Update `profiles/dsl-manifest.json` to include `wellmanifest/code-dsl` mapping and `wellmanifest.code` standardsLock pin.
2. Validate with `dsl_check.py` validate, standards and self-test.
3. Validate with `governance-check.sh`.
