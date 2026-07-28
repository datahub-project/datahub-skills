# DataHub Investigate

Chain discovery, lineage, and documentation into a multi-step investigation, then conclude with claims that are each traceable to a specific URN — optionally saving the write-up back to DataHub.

## What it does

1. Checks which tool categories are actually available this session (discovery, documents, mutations) — never assumes
2. Scopes the user's question into a specific, falsifiable claim to investigate
3. Discovers candidate entities (search + get_entities), then traces relationships (get_lineage)
4. Reads existing context where exposed — schema, query history, and institutional memory (documents)
5. Concludes with separate, independently-cited findings, each labeled observed or inferred
6. Writes back where mutation tools are enabled — filling a description or saving the investigation as a document — with mandatory before/after approval
7. Presents a report that's explicit about what wasn't checked, not just what was found

## Usage

```
/datahub-investigate why did orders_daily's row count drop last week?
/datahub-investigate trace the root cause of the revenue dashboard discrepancy and write up what you find
/datahub-investigate figure out where the customer_ltv column's definition comes from
```

Or ask naturally: "investigate why this pipeline broke and document the cause", "find out what changed upstream of the orders table and record the answer".

## When to use something else

- One-off question answerable from a single search or lineage call → `/datahub-search` or `/datahub-lineage`
- You already know the new value and just want to write it → `/datahub-enrich`
- Assertions, incidents, or quality health checks → `/datahub-quality`
