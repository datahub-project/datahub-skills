---
name: catalog-ml-rca
description: Root-cause silent ML failures through lineage — probe upstream data health and write findings back
argument-hint: "[model name/urn or reliability question]"
---

# DataHub ML Root-Cause Analysis

Use the Skill tool to invoke the full `datahub-ml-rca` skill:

```
Skill tool:
  skill: "datahub-skills:datahub-ml-rca"
```

**User's request:** $ARGUMENTS

This skill investigates ML model reliability end to end:

1. Walk the model's upstream lineage (features, training runs, marts, staging, raw)
2. Compile governance metadata (SLAs, cadence tags, column constraints) into read-only SQL probes
3. Diagnose the first broken ancestor — one root cause, not symptom spam
4. Write back an incident on the root cause plus an RCA case document

If no arguments provided, ask which model (or all models) to audit.
