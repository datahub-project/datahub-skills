---
name: catalog-lineage
description: Explore lineage, trace data dependencies, and perform impact analysis
argument-hint: "[entity to trace or lineage question]"
---

# DataHub Lineage

Use the Skill tool to invoke the full `datahub-lineage` skill:

```
Skill tool:
  skill: "datahub-skills:datahub-lineage"
```

**User's request:** $ARGUMENTS

This skill explores data lineage in DataHub:

1. Identify the target entity
2. Determine traversal direction and depth (upstream, downstream, or both)
3. Execute lineage queries
4. Visualize the lineage graph with flow diagrams and impact analysis

If no arguments provided, ask which entity to trace.
