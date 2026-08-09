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
