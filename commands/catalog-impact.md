---
name: catalog-impact
description: Decide whether a proposed schema or dbt change is safe to merge (PASS / REVIEW / BLOCK)
argument-hint: "[dataset and the change, e.g. 'drop airport_fee from trip_features']"
---

# DataHub Impact Gate

Use the Skill tool to invoke the full `datahub-impact-gate` skill:

```
Skill tool:
  skill: "datahub-skills:datahub-impact-gate"
```

**User's request:** $ARGUMENTS

This skill decides whether a proposed data change is safe to merge:

1. Identify the changed dataset and classify each field change (drop, rename, retype, add)
2. Compute the downstream blast radius with a skip-cache lineage query
3. Walk the ML path (dataset → mlFeature → mlModel) and find impacted dashboards
4. Resolve owners and return a PASS / REVIEW / BLOCK recommendation, failing safe when lineage is ambiguous

If no arguments are provided, ask which dataset is changing and what the change is.
