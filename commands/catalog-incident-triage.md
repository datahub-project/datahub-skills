---
name: catalog-incident-triage
description: Triage a data incident — blast radius, root cause, and write-back
argument-hint: "[incident report or affected asset]"
---

# DataHub Incident Triage

Use the Skill tool to invoke the full `datahub-incident-triage` skill:

```
Skill tool:
  skill: "datahub-skills:datahub-incident-triage"
```

**User's request:** $ARGUMENTS

This skill diagnoses a data incident end to end:

1. Parse the report into a structured incident
2. Resolve the mentioned names to concrete URNs
3. Search past postmortems in the catalog before investigating
4. Compute the downstream blast radius and the owners to notify
5. Rank root-cause hypotheses with cited evidence URNs
6. Propose the write-back as a dry run and wait for approval
7. Save the postmortem so the next investigation starts from it

If no arguments provided, ask what broke and what the symptom is.
