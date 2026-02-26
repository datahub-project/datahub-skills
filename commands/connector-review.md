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

The skill launches 5 review agents in parallel with DataHub standards context:

- `pr-review-toolkit:silent-failure-hunter` - Find error handling gaps (with patterns.md)
- `pr-review-toolkit:pr-test-analyzer` - Analyze test coverage quality (with testing.md)
- `pr-review-toolkit:type-design-analyzer` - Review Pydantic models and type safety (with patterns.md)
- `pr-review-toolkit:code-simplifier` - Find complexity and refactoring opportunities (with patterns.md)
- `datahub-skills:comment-resolution-checker` - Verify previous review comments were substantively addressed

If no arguments provided, ask which connector to review.
