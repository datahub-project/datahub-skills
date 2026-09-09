---
name: catalog-quality-circuit
description: Selective quality circuit-breaking — findings, blast radius, quarantine set, MBOM
argument-hint: "[pipeline, entity, or quality circuit question]"
---

# DataHub Quality Circuit

Use the Skill tool to invoke the full `datahub-quality-circuit` skill:

```
Skill tool:
  skill: "datahub-skills:datahub-quality-circuit"
```

**User's request:** $ARGUMENTS

This skill diagnoses quality/governance issues, maps selective blast radius on lineage, recommends a minimum quarantine set, and drafts MBOM-style attestations.

If no arguments are provided, ask which pipeline or entity to analyze.
