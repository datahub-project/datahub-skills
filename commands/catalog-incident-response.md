---
name: catalog-incident-response
description: Diagnose and contain a live data incident from a consumer-visible symptom
argument-hint: "[symptom or affected asset]"
---

# DataHub Incident Response

Use the Skill tool to invoke the full `datahub-incident-response` skill:

```
Skill tool:
  skill: "datahub-skills:datahub-incident-response"
```

**User's request:** $ARGUMENTS

This skill performs a read-only, evidence-backed investigation first. Any catalog warning tags
require an exact plan and explicit user approval, followed by read-after-write verification.

If no arguments are provided, ask what consumer-visible symptom occurred and which asset is
affected.
