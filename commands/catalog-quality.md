---
name: catalog-quality
description: Manage data quality — assertions, incidents, and subscriptions
argument-hint: "[entity or quality question]"
---

# DataHub Quality

Use the Skill tool to invoke the full `datahub-quality` skill:

```
Skill tool:
  skill: "datahub-skills:datahub-quality"
```

**User's request:** $ARGUMENTS

This skill manages data quality across two tiers:

1. **Open Source:** Find assets with health problems, inspect assertion results and active incidents
2. **Cloud (Acryl SaaS):** Create assertions, run quality checks, raise/resolve incidents, set up notification subscriptions

If no arguments provided, ask what the user wants to check or set up for data quality.
