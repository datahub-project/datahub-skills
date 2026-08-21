# DataHub Import Docs

Import documentation from a **git repository** (GitHub, GitLab, Bitbucket, or self-hosted) into DataHub's knowledge base — turning a repo's markdown/text files into a hierarchy of DataHub **Document** entities. Works on the **local repo you're currently in** (preferred — reads the working tree directly, no clone, any forge) or a **named remote repo** (GitHub implemented; other forges via shallow clone).

## What it does

1. Resolves the source — the local working directory you're in, or a named remote repo — plus ref and path scope
2. Fetches the file tree and previews the folder → document hierarchy
3. Builds an import plan (create vs. update) with deterministic, idempotent document IDs
4. Gets your approval
5. Generates and runs a small Python script using the DataHub SDK to upsert the documents
6. Verifies the imported tree

## How it works (no server dependency)

The skill writes documents through the **stable `datahub.sdk.Document` SDK** shipped in `acryl-datahub` v1.6.0+ — it does **not** depend on any server-side document-import GraphQL resolver. The import logic (walking the repo, mapping folders to a parent-child hierarchy, deriving idempotent IDs) runs in the agent; documents are persisted with `client.entities.upsert(...)`.

## Usage

```
# From inside a checked-out repo (preferred — reads the working tree):
/import-docs import docs from this repo into DataHub
/import-docs import the docs/ folder into DataHub

# Or a named remote repo:
/import-docs import docs from github.com/acme/handbook
/import-docs import acme/runbooks as AI-only context linked to the orders dataset
```

## Requirements

- DataHub CLI **v1.6.0+** (the `Document` SDK ships here)
- A working DataHub connection (`~/.datahubenv` or `DATAHUB_GMS_*`)
- `MANAGE_DOCUMENTS` privilege on the connected token
- `git` (for local imports, any forge); `gh` for GitHub remote imports, or `git` shallow-clone for other remotes

All writes require your explicit approval. Re-importing is idempotent — it updates documents in place rather than creating duplicates.

For one-off document creation or linking a single external doc to an asset, use `/datahub-enrich`.
