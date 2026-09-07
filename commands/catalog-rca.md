---
name: catalog-rca
description: Diagnose a data incident and find its root cause with a verifiable lineage path
argument-hint: "[incident description, failing assertion, or entity URN]"
---

# DataHub Root-Cause Analysis

Use the Skill tool to invoke the full `datahub-rca` skill:

```
Skill tool:
  skill: "datahub-skills:datahub-rca"
```

**User's request:** $ARGUMENTS

This skill performs path-grounded root-cause analysis in DataHub:

1. Detect — resolve the symptom (failing assertion / stale table / bad dashboard)
2. Scope — walk lineage upstream to a minimal suspect subgraph
3. Hypothesize — rank candidates from freshness, volume, schema, query signals
4. Prove — accept a cause only with a verifiable lineage path + transform SQL
5. Write back — persist the incident dossier and tag the culprit

If no arguments are provided, ask which incident or entity to investigate.
