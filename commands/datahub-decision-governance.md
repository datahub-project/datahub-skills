---
name: datahub-decision-governance
description: Govern an operational decision with DataHub evidence, approval, write-back, and revalidation
argument-hint: "[decision question, comparison, or revalidation request]"
---

# DataHub Decision Governance

Use the Skill tool to invoke the full `datahub-decision-governance` skill:

```
Skill tool:
  skill: "datahub-skills:datahub-decision-governance"
```

**User's request:** $ARGUMENTS

This skill:

1. Resolves the governed DataHub assets
2. Captures schema, ownership, health, and lineage evidence
3. Produces a reproducible recommendation
4. Requires explicit approval before `save_document`
5. Reads back the saved record and preserves prior revisions
6. Revalidates when evidence changes

If no arguments are provided, ask what operational decision should be governed.
