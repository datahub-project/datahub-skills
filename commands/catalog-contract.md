---
name: catalog-contract
description: Generate a native DataHub data contract for a dataset from its live schema and profiling stats
argument-hint: "[dataset to give a contract]"
---

# DataHub Contract Author

Use the Skill tool to invoke the full `datahub-contract-author` skill:

```
Skill tool:
  skill: "datahub-skills:datahub-contract-author"
```

**User's request:** $ARGUMENTS

This skill generates a native `dataContract` for a dataset:

1. Read the dataset's live schema and profiling statistics
2. Derive evidence-based thresholds (volume band, null and uniqueness checks)
3. Draft a declarative contract YAML (schema + freshness + volume + column checks) for approval
4. Emit it through the native `datahub.api.entities.datacontract` path and verify the assertions bound

If no dataset is provided, ask which dataset to give a contract.
