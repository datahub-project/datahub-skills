---
name: catalog-incident-triage
description: Triage a data incident end to end (root cause, blast radius, post-mortem)
argument-hint: "[failing entity or incident]"
---

# DataHub Incident Triage

Use the Skill tool to invoke the full `datahub-incident-triage` skill:

```
Skill tool:
  skill: "datahub-skills:datahub-incident-triage"
```

**User's request:** $ARGUMENTS

This skill runs a closed-loop incident investigation:

1. Resolve the failing entity and validate the signal from dataset health
2. Recall prior post-mortems before walking lineage
3. Trace upstream one hop at a time until a node fails intrinsically
4. Rank downstream blast radius by usage and resolve owners
5. Execute approved metadata actions, then store a structured post-mortem

If no arguments provided, ask which entity or signal to triage.
