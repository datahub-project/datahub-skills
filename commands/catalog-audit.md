---
name: catalog-audit
description: Audit metadata coverage and governance health across your DataHub catalog
argument-hint: "[scope or audit question]"
---

# DataHub Audit

Use the Skill tool to invoke the full `datahub-audit` skill:

```
Skill tool:
  skill: "datahub-skills:datahub-audit"
```

**User's request:** $ARGUMENTS

This skill generates systematic metadata coverage reports and governance health checks:

1. Classify the audit intent (coverage audit vs. governance audit)
2. Confirm scope (entity type, platform, environment, domain)
3. Execute coverage queries across the catalog
4. Calculate metrics and percentages per dimension
5. Generate a structured report with actionable recommendations

If no arguments provided, ask what the user wants to audit.
