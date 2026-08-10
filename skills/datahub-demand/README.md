# DataHub Demand

Establish whether an asset is genuinely absent from the catalog, and record the unmet need
so the signal is not discarded.

## What it does

Every other skill in this repository assumes the asset exists. This one covers the moment
the search comes back empty — which is where an agent is most likely to be confidently
wrong.

1. **Disproves the absence** through eight checks before allowing the words "does not
   exist": literal and tokenised search, glossary terms, column-level search, other
   platforms, deprecated assets, data products, and lineage neighbours.
2. **Reports the absence with its receipt** — what was ruled out, and the nearest existing
   asset — so a human can audit the claim.
3. **Records the unmet need** in the sink the organisation already uses, without creating
   placeholder entities in the catalog.

## Why the disproof step is the point

An empty result is not evidence of absence. It is far more often evidence that the search
was wrong. An agent that declares a table missing after one query sends someone to rebuild
an asset that already exists, which is worse than returning nothing at all.

The output of this skill is therefore an argument, not a status:

```
ABSENT: "monthly recurring revenue by segment"
  glossary terms   "MRR" exists, points at revenue_events (raw, not by segment)
  column search    no column named mrr on any catalogued asset
  ... 6 more checks ...
Nearest existing asset: ecommerce.revenue_events (raw events, no segment grain)
```

## Usage

```
/datahub-demand is there a table for trial-to-paid conversion by cohort?
/datahub-demand I could not find monthly recurring revenue by segment
/datahub-demand record that finance needs churn by cohort
```

Or ask naturally: "does a customer health score table exist?", "nothing matched, is it
really missing?".

## Related skills

| Situation                              | Skill              |
| -------------------------------------- | ------------------ |
| The asset exists — find it             | `/datahub-search`  |
| It exists but is undocumented          | `/datahub-enrich`  |
| It was deprecated — who depended on it | `/datahub-lineage` |
| It exists but is untrustworthy         | `/datahub-quality` |
