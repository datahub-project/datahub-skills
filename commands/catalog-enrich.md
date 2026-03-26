---
name: catalog-enrich
description: Add or update metadata in DataHub - descriptions, tags, glossary terms, ownership
argument-hint: "[entity and what to update]"
---

# DataHub Enrich

Use the Skill tool to invoke the full `datahub-enrich` skill:

```
Skill tool:
  skill: "datahub-skills:datahub-enrich"
```

**User's request:** $ARGUMENTS

This skill manages metadata in DataHub:

1. Understand the enrichment intent (add tag, update description, set owner, etc.)
2. Resolve target entities and show current state
3. Build an enrichment plan with before/after comparison
4. Get your approval before making any changes
5. Execute updates and verify

If no arguments provided, ask what metadata to update.
