# DataHub Document

Capture answers as DataHub documents, and recall the ones already written before answering
again.

## What it does

1. Searches existing documents before answering, so prior work is reused rather than redone
2. Decides whether an answer is worth keeping
3. Writes it for the next reader — question first, every asset named by URN, dated
4. Saves it with `save_document`
5. Verifies the write actually happened before reporting success

## Usage

```
/datahub-document save this impact analysis
/datahub-document is there a runbook for the orders pipeline?
/datahub-document write up why revenue_daily was deprecated
/datahub-document what do our docs say about PII retention?
```

For metadata attached to an entity — descriptions, tags, glossary terms, ownership — use
`/datahub-enrich`. For finding the entities themselves, use `/datahub-search`.

## Requirements

`save_document` needs mutations enabled (`TOOLS_IS_MUTATION_ENABLED=true`) and DataHub
Cloud 0.3.16+ or Core 1.4.0+. `search_documents` and `grep_documents` are hidden when the
catalog has no documents yet, so their absence means an empty knowledge base rather than a
misconfiguration.
