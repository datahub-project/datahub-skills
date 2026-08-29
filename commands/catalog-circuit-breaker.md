---
name: catalog-circuit-breaker
description: Trip, lift, or inspect advisory circuit-breaker quarantine state in DataHub
argument-hint: "[entity or gate question]"
---

# DataHub Circuit Breaker

Use the Skill tool to invoke the full `datahub-circuit-breaker` skill:

```
Skill tool:
  skill: "datahub-skills:datahub-circuit-breaker"
```

**User's request:** $ARGUMENTS

This skill manages **advisory** quarantine (tags + structured properties) so consumers can honor unsafe context — without claiming platform-wide MCP auto-denial.

If no arguments are provided, ask which entity to trip, lift, or inspect.
