---
name: catalog-pr-blast-radius
description: Review a SQL or dbt PR for downstream blast radius before merge
argument-hint: "[PR number or branch to review]"
---

# DataHub PR Blast Radius

Use the Skill tool to invoke the full `datahub-pr-blast-radius` skill:

```
Skill tool:
  skill: "datahub-skills:datahub-pr-blast-radius"
```

**User's request:** $ARGUMENTS

This command reviews a SQL/dbt pull request for downstream impact:

1. Fetch the PR diff and identify changed data models and columns
2. Resolve every entity in the catalog (exact match only, never a guess)
3. Trace downstream lineage and collect owners
4. Score with deterministic rules (missing lineage never produces SAFE)
5. Post the verdict with an impact table and a fix suggestion

If no PR number is provided, ask which PR to review.
