---
name: catalog-schema-change-certification
description: Certify a risky DataHub dataset field change before implementation
argument-hint: "[dataset field rename, drop, or type change]"
---

# DataHub Schema-Change Certification

Use the Skill tool to invoke the full `datahub-schema-change-certification` skill:

```
Skill tool:
  skill: "datahub-skills:datahub-schema-change-certification"
```

**User's request:** $ARGUMENTS

This skill uses the official DataHub MCP server to:

1. Prove the exact target, field, and bounded downstream impact
2. Calculate deterministic, policy-versioned risk
3. Validate a non-destructive expand-migrate-contract package
4. Bind a human decision to the exact immutable scope
5. Write and durably verify only the approved decision metadata

If no arguments are provided, ask for the exact dataset URN, source field, and proposed rename, drop, or type change.
