# DataHub Search

Search the DataHub catalog and answer questions about your data — find entities, browse by platform or domain, and get answers backed by metadata evidence.

## What it does

**Discovery mode:** Find, browse, and list entities.

**Question mode:** Answer analytical questions by querying and reasoning over metadata.

1. Classifies your intent (discovery vs. question)
2. Translates to DataHub search, get, and browse operations
3. Executes via MCP tools or DataHub CLI
4. Presents results or synthesizes an answer with evidence

## Usage

```
/datahub-search revenue tables in Snowflake
/datahub-search who owns the revenue pipeline?
/datahub-search datasets tagged PII in the Finance domain
/datahub-search how many tables lack descriptions?
```

Or ask naturally: "find all BigQuery datasets", "what dashboards use the customer_orders table?".
