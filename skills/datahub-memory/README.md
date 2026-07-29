# DataHub Memory

Check whether something was already figured out before investigating again, and remember new conclusions for next time — using DataHub's own documents as the memory store, no external database.

## What it does

1. Checks whether `search_documents`/`grep_documents`/`save_document` are available this session
2. Recalls first — searches existing documents (tagged `investigation-report` for this skill's own prior output, plus the organization's own runbooks/notes) before doing anything else
3. Decides what's still missing: full hit (cite and stop), partial/stale hit (investigate just the gap), or no hit (investigate fresh)
4. Investigates any remaining gap, scoped to only what recall didn't already answer — using a dedicated deep-dive investigation skill if one is installed, or chaining Search/Lineage/schema tools directly
5. Persists new conclusions — one `save_document` call per distinct finding, with the same before-you-save approval `save_document` itself requires
6. Supersedes stale documents by saving a new one that links back to the old, rather than deleting or silently overwriting it

## Usage

```
/datahub-memory did we already look into why orders_daily's row count dropped?
/datahub-memory what do we already know about the revenue dashboard discrepancy?
/datahub-memory remember that customer_ltv's definition comes from the finance glossary term
```

Or ask naturally: "check if this was already investigated before you dig in", "save this conclusion for next time".

## When to use something else

- You explicitly want a fresh investigation with no recall check → investigate directly (Search/Lineage, or a dedicated investigation skill if installed)
- One-off question answerable from a single search or lineage call → `/datahub-search` or `/datahub-lineage`
- You already know the new value and just want to write it → `/datahub-enrich`
