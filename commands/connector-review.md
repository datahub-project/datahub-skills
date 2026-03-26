---
name: connector-review
description: Review DataHub connector code for standards compliance and quality
argument-hint: "[connector name or path]"
---

# DataHub Connector PR Review

Use the Skill tool to invoke the full `datahub-connector-pr-review` skill:

```
Skill tool:
  skill: "datahub-skills:datahub-connector-pr-review"
```

**User's request:** $ARGUMENTS

This skill reviews connector code against the 22 DataHub standards. On Claude Code with `pr-review-toolkit` installed, it runs 5 review agents in parallel. Otherwise it performs the same checks sequentially.

If no arguments provided, ask which connector to review.
