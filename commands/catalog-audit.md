---
name: catalog-audit
description: Audit DataHub metadata governance coverage and risk
argument-hint: "[scope or audit question]"
---

# DataHub Audit

Use the Skill tool to invoke the full `datahub-audit` skill:

```text
Skill tool:
  skill: "datahub-skills:datahub-audit"
```

**User's request:** $ARGUMENTS

The skill performs a bounded, read-only governance audit and reports coverage,
priority findings, evidence, methodology, and limitations. It never changes metadata.

If no arguments are provided, ask which platforms, domains, environments, or governance
dimensions the user wants to audit.
