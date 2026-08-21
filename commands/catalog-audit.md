---
name: catalog-audit
description: Scan the DataHub catalog for systemic problems and generate a report
argument-hint: "[what to audit, e.g. a glossary term or group]"
---

# DataHub Audit

Use the Skill tool to invoke the full `datahub-audit` skill:

```
Skill tool:
  skill: "datahub-skills:datahub-audit"
```

**User's request:** $ARGUMENTS

This skill scans the catalog for systemic problems rather than looking up or changing one entity:

1. Determine the audit type (currently: Glossary Schema Consistency)
2. Resolve scope — a named term, a named group, or a confirmed full-glossary sweep
3. Discover matching fields and compare their schema across the group
4. Report inconsistencies with severity, and suggest a fix path

If no arguments provided, ask what to audit — a specific glossary term, a group, or the whole glossary.
