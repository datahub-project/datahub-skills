# DataHub Context Drift

Find documentation that has stopped being true — not documentation that is missing.

## What it does

1. Asks DataHub what changed — `datahub timeline --category technical_schema`
   is a semantic diff of successive schema versions, so nothing has to be
   inferred from how a token is spelled
2. Reads the description a human actually sees (editable first, then ingested)
3. Reports two kinds of drift: prose naming a departed field, and documentation
   still attached to a field that is gone
4. Abstains whenever it cannot point at a schema entry or a change-log event
5. Drafts a correction, waits for your approval, writes back, then reads back to
   confirm the value landed

```
> /datahub-context-drift check the descriptions in the finance domain
> /datahub-context-drift is this table's description still accurate?
> /datahub-context-drift the trip_records column was renamed, what else is stale?
```

All writes require your explicit approval for that specific text.

## Why this is not a coverage check

In February 2023 the NYC TLC renamed `airport_fee` to `Airport_fee` in its public
trip records. One letter, no error, no announcement. The description stayed as it
was and quietly stopped being true.

Coverage tooling scores that table perfectly: the description exists, the columns
are documented, nothing is missing. For "what has not been written yet", use
`/datahub-audit`. This skill reads what _has_ been written.

There is a quieter version. When a pipeline stops producing a column, DataHub
rewrites `schemaMetadata` and leaves `editableSchemaMetadata` alone — so a
description someone wrote in the UI stays behind, attached to a field that no
longer exists. The UI cannot show it, because there is no column left to render
it on. It is still in the graph, and still served to anything reading the catalog
through the API.
