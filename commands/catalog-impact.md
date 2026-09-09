---
name: catalog-impact
description: Analyze schema change blast radius, calculate severity tiers, and build remediation migration plans
argument-hint: "[schema change details, e.g. rename column customer_id in raw.customers]"
---

# DataHub Schema Change Impact Analysis

Use the Skill tool to invoke the full `datahub-impact` skill:

```
Skill tool:
  skill: "datahub-skills:datahub-impact"
```

**User's request:** $ARGUMENTS

This skill assesses the blast radius of proposed database schema changes:

1. Resolve target entity and column URNs
2. Trace combined column-level and dataset-level lineage
3. Label lineage confidence honestly (confirmed vs inferred)
4. Enrich downstream assets and query usage
5. Rank asset severity using a 5-factor heuristic
6. Generate a change-type specific remediation migration plan
7. Write impact metadata back into DataHub (incidents, properties, document, tags)

If no arguments provided, ask which dataset, column, and change type (`rename`, `drop`, `type_change`, `add`) to analyze.
