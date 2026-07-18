---
name: catalog-ml-lineage
description: Audit ML model lineage for target leakage, blast radius, and retrain triggers
argument-hint: "[model to audit or ML lineage question]"
---

# DataHub ML Lineage

Use the Skill tool to invoke the full `datahub-ml-lineage` skill:

```
Skill tool:
  skill: "datahub-skills:datahub-ml-lineage"
```

**User's request:** $ARGUMENTS

This skill audits ML model lineage in DataHub:

1. Resolve the target model and pull its full upstream lineage graph
2. Check for target-leakage signals via governance glossary terms
3. Check for blast-radius risk from stale/orphaned upstream tables
4. Write findings back (tags, Analysis document, description update)
5. Optionally generate a remediation diff against the source pipeline

If no arguments provided, ask which model to audit.
