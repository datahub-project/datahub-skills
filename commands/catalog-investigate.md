---
name: catalog-investigate
description: Investigate a data incident — lineage-driven root cause analysis, remediation, and resolution
argument-hint: "[symptom, incident, or asset to investigate]"
---

# DataHub Incident Investigation

Use the Skill tool to invoke the full `datahub-incident-investigation` skill:

```
Skill tool:
  skill: "datahub-skills:datahub-incident-investigation"
```

**User's request:** $ARGUMENTS

This skill drives a data incident from symptom to resolution:

1. Frame the symptom — affected field, magnitude, and onset
2. Localize the fault by traversing upstream and column-level lineage
3. Generate competing hypotheses and eliminate them against cited evidence
4. Confirm a root cause that is both necessary and sufficient, or declare no incident
5. Assess blast radius, propose a scoped remediation, verify it, and write the resolution back to DataHub

If no arguments provided, ask what looks wrong, by how much, and since when.
