---
name: code-guardian
description: Check repository code against the catalog, repair what it proves, record the verdict back
argument-hint: "[repository path or change to review]"
---

# DataHub Code Guardian

Use the Skill tool to invoke the full `datahub-code-guardian` skill:

```
Skill tool:
  skill: "datahub-skills:datahub-code-guardian"
```

**User's request:** $ARGUMENTS

This skill runs one loop over code that touches governed data:

1. Map the code to the catalog and resolve every named asset to a URN
2. Read what earlier runs already concluded about those assets, before proposing anything
3. Check the code against schema, types, ownership, tags, and lineage
4. Repair only what the catalog proves, and verify by re-running the check
5. Record every verdict back as a custom assertion

If no arguments provided, ask which repository or change to review.
