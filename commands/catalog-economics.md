---
name: catalog-economics
description: Price the catalog — asset cost, value at risk, and deprecation candidates
argument-hint: "[entity or economics question]"
---

# DataHub Economics

Use the Skill tool to invoke the full `datahub-economics` skill:

```
Skill tool:
  skill: "datahub-skills:datahub-economics"
```

**User's request:** $ARGUMENTS

This skill operates in two modes:

1. **Pricing:** What an asset costs (storage, read compute, rebuild compute) and what it costs when it breaks
2. **Decision:** Whether to deprecate it, right-size its schedule, protect it, or refuse to judge for lack of evidence

Ask for a rate card before quoting any dollar figure — never invent a price. If no arguments are provided, ask whether the user wants to price a specific asset or scan an estate for recoverable spend.
