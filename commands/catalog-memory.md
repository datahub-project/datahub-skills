---
name: catalog-memory
description: Check whether this was already investigated before digging in, and remember new conclusions for next time
argument-hint: "[question to recall or remember]"
---

# DataHub Memory

Use the Skill tool to invoke the full `datahub-memory` skill:

```
Skill tool:
  skill: "datahub-skills:datahub-memory"
```

**User's request:** $ARGUMENTS

This skill is the recall-first front door onto DataHub's own documents:

1. Checks whether document tools (`search_documents`, `grep_documents`, `save_document`) are available this session
2. Recalls first — searches existing documents before investigating anything
3. Investigates only the remaining gap — using a dedicated deep-dive investigation skill if one is installed, or chaining Search/Lineage directly
4. Persists new conclusions as documents, one per distinct finding, with approval
5. Supersedes stale documents rather than deleting or overwriting them

If no arguments provided, ask what the user wants recalled or remembered.
