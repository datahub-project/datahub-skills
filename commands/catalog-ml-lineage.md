---
name: catalog-ml-lineage
description: Trace lineage into ML entities — features, models and the endpoints serving them
argument-hint: "[model, feature, or ML lineage question]"
---

# DataHub ML Lineage

Use the Skill tool to invoke the full `datahub-ml-lineage` skill:

```
Skill tool:
  skill: "datahub-skills:datahub-ml-lineage"
```

**User's request:** $ARGUMENTS

This skill traces lineage past the warehouse boundary:

1. Identify the model, feature or endpoint in question
2. Walk dataset → feature → feature table → model → deployment
3. Resolve features to columns, and state the confidence tier that resolution rests on
4. Report the path, and whether the model is actually deployed

If no arguments provided, ask which model or feature to trace.
