---
name: connector-planning
description: Plan a new DataHub connector - research the source system, map entities, design architecture, and create a planning document
argument-hint: "[source system name]"
---

# DataHub Connector Planning

Use the Skill tool to invoke the full `datahub-connector-planning` skill:

```
Skill tool:
  skill: "datahub-skills:datahub-connector-planning"
```

**User's request:** $ARGUMENTS

This skill guides you through planning a new DataHub connector:

1. Classify the source system type (SQL DB, API, etc.)
2. Research the source using the `datahub-skills:connector-researcher` agent
3. Gather user requirements (test environment, features, permissions)
4. Create a comprehensive `_PLANNING.md` document with entity mapping, architecture decisions, and implementation order

If no arguments provided, ask which source system to plan a connector for.
