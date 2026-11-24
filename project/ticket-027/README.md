# Ticket 027: Plan DSL artifact digest refresh

- **ID**: ticket-027
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-11-24

## Goal and scope

Implement a read-only DSL command that reports guarded digest replacements for
one manifest. On MaskFleet #424 the command reproduced the two manually verified
changes in the exact planned adoption tree. PLF-9347 tracks this change.

## Acceptance criteria

- [x] AC-01: An unchanged manifest produces an empty patch. For stale digests,
  patch tests bind the artifact path and old digest before each replacement.
  Validation still fails for stale digests, and an unavailable artifact yields
  an error report. The command leaves the manifest bytes intact.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.

<!-- ticket-radar:start -->
## Ticket Radar

Initial planned-scope estimate; advisory only, not execution or merge approval.

| Measure | Initial assessment |
| --- | --- |
| Impact score | 56/100 |
| Complexity | M |
| Estimated effort | 57 min |
| Planning budget | 30 min |
| Split recommended | yes |

Diagnostics: RADAR-ACCEPTANCE-MISSING, RADAR-BUDGET-EXCEEDED.
<!-- ticket-radar:end -->
