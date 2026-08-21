---
name: catalog-investigate
description: Investigate a data question across discovery, lineage, and documentation, and conclude with cited findings
argument-hint: "[question to investigate]"
---

# DataHub Investigate

Use the Skill tool to invoke the full `datahub-investigate` skill:

```
Skill tool:
  skill: "datahub-skills:datahub-investigate"
```

**User's request:** $ARGUMENTS

This skill answers questions that span more than one tool category:

1. Checks which tool categories (discovery, documents, mutations) are actually available this session
2. Discovers candidate entities and traces lineage
3. Reads existing context and institutional memory where exposed
4. Concludes with separate, URN-cited findings labeled observed or inferred
5. Writes back where mutation tools are enabled, with mandatory before/after approval

If no arguments provided, ask what the user wants investigated.
