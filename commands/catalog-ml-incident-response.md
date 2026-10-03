---
name: catalog-ml-incident-response
description: Investigate an ML data incident through verified DataHub context and prepare a safe remediation
argument-hint: "[incident evidence or affected asset]"
---

# DataHub ML Incident Response

Use the Skill tool to invoke the full `datahub-ml-incident-response` skill:

```text
Skill tool:
  skill: "datahub-skills:datahub-ml-incident-response"
```

**User's request:** $ARGUMENTS

This skill:

1. classifies freshness, feature skew, replay, backfill, late-event, or stale-lineage incidents;
2. verifies assets and traces bounded lineage through MCP tools or the DataHub CLI;
3. routes owners and produces remediation, validation, rollback, and a dry-run writeback payload;
4. requires explicit human approval before any live mutation.

If no arguments are provided, ask for the affected asset and the observed incident evidence.
