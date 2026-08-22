---
name: catalog-privacy-ops
description: Trace and plan a privacy operation from DataHub context
argument-hint: "[privacy request, seed dataset, or case reference]"
---

# DataHub Privacy Operations

Use the Skill tool to invoke the full `datahub-privacy-ops` skill:

```
Skill tool:
  skill: "datahub-skills:datahub-privacy-ops"
```

**User's request:** $ARGUMENTS

The skill uses DataHub metadata to discover a bounded PII footprint, preserve legal holds and
unknown policy as explicit exceptions, and prepare an approval-bound dry-run plan. It never claims
that DataHub deleted source-system rows. DataHub evidence write-back requires a separate approval
and fresh-session read-back.

If no arguments are provided, ask for an opaque case ID and one or more seed dataset names or URNs.
