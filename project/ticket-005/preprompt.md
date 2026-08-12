# Ticket preprompt

- **Task ID**: ticket-005
- **Task title**: Add core profiles and standards lock
- **Created**: 2026-08-12T17:31:21Z

Keep executable implementation outside this governance/evidence directory.
Read a human-owned user-*.md file only when one exists.

## Technical directives

- Keep all profile variants closed and bounded; profiles describe data and do
  not grant execution authority.
- Separate streaming telemetry from the terminal typed LLM result.
- Pin composed standards by repository, semantic version, exact Git SHA,
  schema/grammar references and digests.
- Derive the publication tier deterministically from declared risk; an LLM
  finding remains advisory and never lowers the required tier.
