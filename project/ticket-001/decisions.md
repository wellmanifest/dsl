# Publication decisions

```dsl
DECISION D-001-0001
TICKET ticket-001
HEAD_SHA d51a1c900e59963483d0bbfe050623092eb60fff
CORRELATION_ID wellmanifest-dsl-ticket-001-publication
ACTOR agent:codex
APPLIED_RULE C-PUBLISH-003
INPUT user_authorization = "kontynuuj , publikuj"
INPUT remote_default_branch = "absent_before_bootstrap"
INPUT implementation_file_count = 5
INPUT bootstrap_implementation_file_count = 0
INPUT expected_verdict_from_rule = "APPROVE"
VERDICT APPROVE AUTHORITY DETERMINISTIC
REJECTED DIRECT_PUSH_IMPLEMENTATION BECAUSE IMPLEMENTATION_REQUIRES_PULL_REQUEST
ASSERT VERDICT_AUTHORITY != "ADVISORY"
ASSERT IMPLEMENTATION_BASE_SHA == "d51a1c900e59963483d0bbfe050623092eb60fff"
```

## D-001-0002 — Documentation and security finding gate

- **Status**: accepted by the human instruction `kontynuuj` on 2026-08-09.
- **Command help path**: `docs/<UPPERCASE_COMMAND>.md`.
- **Error help path**: `docs/ERROR/<CODE>.md`.
- **Critical help path**: `docs/CRITICAL/<CODE>.md`.
- **Evidence examples**: `subactor.twin-probes` and
  `subactor.autonom-cycle/v1`, normalized through a deterministic adapter.
- **Trust root**: protected deterministic DSL gate.
- **Rejected**: probe as authority; probes emit evidence only.
- **Rejected**: documentation as a waiver; unresolved critical findings still
  block publication.
- **Scope**: the implementation file set remains the previous five files.
