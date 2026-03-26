---
name: catalog-search
description: Search the DataHub catalog and answer questions about your data
argument-hint: "[search query or question]"
---

# DataHub Search

Use the Skill tool to invoke the full `datahub-search` skill:

```
Skill tool:
  skill: "datahub-skills:datahub-search"
```

**User's request:** $ARGUMENTS

This skill searches the DataHub catalog in two modes:

1. **Discovery:** Find entities by keyword, browse by platform/domain, filter by metadata
2. **Questions:** Answer analytical questions by querying and reasoning over catalog metadata

If no arguments provided, ask what the user wants to find or know about their data catalog.
