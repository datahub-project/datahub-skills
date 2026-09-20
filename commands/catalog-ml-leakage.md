---
name: catalog-ml-leakage
description: Check an ML model's feature provenance for target leakage before deployment
argument-hint: "[model name or URN, or leakage question]"
---

# DataHub ML Leakage

Use the Skill tool to invoke the full `datahub-ml-leakage` skill:

```
Skill tool:
  skill: "datahub-skills:datahub-ml-leakage"
```

**User's request:** $ARGUMENTS

This skill checks ML feature provenance safety in DataHub:

1. Resolve the model and confirm the forbidden-tag policy up front
2. Acquire the provenance subgraph, including column-level `fineGrainedLineages`
3. Traverse deterministically — cycle-safe, hop-bounded, path-preserving
4. Issue a fail-closed verdict with the evidence path
5. Optionally record the decision back to DataHub, after approval

If no arguments provided, ask which model to check.
