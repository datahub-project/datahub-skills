---
name: catalog-setup
description: Set up DataHub connection, install CLI, configure authentication and default scopes
argument-hint: "[setup or configuration task]"
---

# DataHub Setup

Use the Skill tool to invoke the full `datahub-setup` skill:

```
Skill tool:
  skill: "datahub-skills:datahub-setup"
```

**User's request:** $ARGUMENTS

This skill sets up your DataHub connection and configures defaults:

1. Check the current environment (Python, CLI, config)
2. Install the DataHub CLI and configure authentication
3. Verify connectivity
4. Configure default scopes and profiles (optional)

If no arguments provided, check the environment and guide from there.
