---
name: catalog-change-safety
description: Assess a proposed data change with DataHub context and executable evidence
argument-hint: "[change, pull request, or artifact to assess]"
---

# DataHub Change Safety

Use the Skill tool to invoke the full `datahub-change-safety` skill:

```
Skill tool:
  skill: "datahub-skills:datahub-change-safety"
```

**User's request:** $ARGUMENTS

This skill assesses a concrete proposed change:

1. Bind the exact base and candidate revisions
2. Resolve the changed asset and downstream critical consumers in DataHub
3. Execute baseline/candidate and approved protection checks
4. Return `UNSAFE`, `SAFE_WITHIN_SCOPE`, or `UNVERIFIED`
5. Produce a machine-readable Change Passport and compact reviewer Check

If no arguments are provided, ask for the repository change, pull request, or artifact revision to assess.
