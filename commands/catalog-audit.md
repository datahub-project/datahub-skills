---
name: catalog-audit
description: Audit DataHub metadata coverage and governance readiness
argument-hint: "[scope or audit question]"
---

# DataHub Audit

Use the Skill tool to invoke the full `datahub-audit` skill:

```text
Skill tool:
  skill: "datahub-skills:datahub-audit"
```

**User's request:** $ARGUMENTS

This skill runs a read-only, evidence-backed metadata audit:

1. Define the catalog scope and complete or sampled population
2. Measure effective descriptions, ownership, domains, and requested governance fields
3. Deduplicate sibling datasets into logical assets
4. Report visible denominators, limitations, and prioritized gaps

If no arguments are provided, ask which entity types, environment, platform, or domain to audit.
