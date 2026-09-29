# DataHub Trust Score

Computes a composite trust score per domain from DataHub signals, writes it back into the
graph as structured properties, tier tags and descriptions, and raises incidents on the
assets that drag a domain down.

## What it does

| Step | Result |
| ---- | ------ |
| Read | Quality, documentation, ownership and freshness signals per dataset |
| Score | Weighted 0-100 score per domain, renormalized when a signal is missing |
| Write | `trustScore` and `trustTier` structured properties on the domain |
| Label | Tier tag on each dataset, filterable from search |
| Explain | Scorecard block in the domain description |
| Act | Operational incident on datasets below threshold, resolved when they recover |

## Why it is separate from `datahub-quality`

`datahub-quality` diagnoses and manages assertions and incidents on individual assets:
what is broken right now. This skill composes several signals into one number per team,
persists that number as metadata, and keeps it current across runs. The output is not a
report, it is enriched metadata that other people and agents can query.

## Requirements

- DataHub CLI 1.4.0 or newer, authenticated (`datahub init`)
- Permissions to edit structured properties, tags, descriptions and incidents
- Structured property definitions for `trustScore` (number) and `trustTier` (string),
  declaring `domain` in their `entityTypes`

## Files

- `SKILL.md` — the workflow the agent follows
- `references/scoring-model.md` — signal sources, weights, renormalization and tiers
