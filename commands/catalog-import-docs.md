---
name: catalog-import-docs
description: Import documents into DataHub from the current local repo or a remote GitHub repo, preserving folder hierarchy
argument-hint: "[this repo | owner/repo | github url, optional path scope]"
---

# DataHub Import Docs

Use the Skill tool to invoke the full `datahub-import-docs` skill:

```
Skill tool:
  skill: "datahub-skills:datahub-import-docs"
```

**User's request:** $ARGUMENTS

This skill imports documents into DataHub from a git repository — the local repo you're currently in (preferred, reads the working tree) or a named remote GitHub repo:

1. Resolve the source (local working dir or named remote repo), ref, and path scope
2. Fetch the file tree and preview the folder → document hierarchy
3. Build an import plan with deterministic, idempotent document IDs
4. Get your approval before writing
5. Generate and run a DataHub SDK script to upsert the documents
6. Verify the imported tree

It uses only the stable `datahub.sdk.Document` SDK (CLI v1.6.0+) — no server-side import resolvers. If no repo is provided, ask which GitHub repository to import.
