# Impact Scoring Reference

The severity rules for the PR blast radius skill. These rules are
deterministic: the same change against the same catalog state always
produces the same verdict. No model opinion is involved.

## Severity Levels

| Level | Meaning |
| ----- | ------- |
| SAFE | The change has no downstream consumers, or every consumer is verified unaffected. |
| RISKY | Impact exists but cannot be fully proven, or an entity could not be resolved. |
| BREAKING | Downstream consumers are verifiably affected by the change. |

## Scoring Matrix

| Change | Catalog state | Verdict |
| ------ | ------------- | ------- |
| Any change | Entity unresolved (no exact match, or ambiguous collision) | RISKY |
| Any change | Parse produced no intents from a data diff | FAILED run, never SAFE |
| Destructive change | Entity resolved, zero downstream lineage found | RISKY (blast radius unverified) |
| Column drop or rename | Downstream assets exist, column-level impact unproven | RISKY |
| Column drop or rename | Downstream asset consumes the affected column | BREAKING |
| Entity dropped | Downstream assets exist | BREAKING |
| Logic change | Downstream assets exist | RISKY |
| Any non-destructive change | No downstream consumers | SAFE |
| Any change | Lineage data missing or catalog unreachable | never SAFE (escalate to RISKY or FAILED) |

## Resolution Policy

- Resolve by exact display-name match only, case-insensitive.
- A name collision (same table name on multiple platforms) is unresolved.
- A near-miss is unresolved. Never analyze a different asset's blast radius.
- Unresolved entities always escalate; they never lower severity.

## Why the Column Distinction Matters

Entity-level lineage answers "who consumes this table?" Column-level lineage
answers "who consumes this column?". A column drop with only entity-level
lineage proves impact exists but not which consumers are hit, so it stays
RISKY. When column-level edges are present and a downstream asset consumes the
dropped column, the impact is proven and the verdict is BREAKING.

## Worst Severity Wins

Multiple changed entities produce multiple intents. The overall verdict is the
worst severity across all scored impacts. A run that contains any BREAKING
impact is BREAKING.
