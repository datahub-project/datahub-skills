# Impact Scoring Reference

How to rank the downstream consumers of a broken asset deterministically.

## The formula

```
impact(consumer) = type_weight × hop_decay × owner × critical × domain

  hop_decay = 1 / (1 + hops)

total_impact = Σ impact(consumer)
```

### Type weights

| Consumer type                                         | Weight | Why                                                      |
| ----------------------------------------------------- | ------ | -------------------------------------------------------- |
| `dashboard`, `mlmodel`, `mlfeature`, `mlfeatureTable` | 3.0    | A human or a model consumes this directly and acts on it |
| `chart`, `dataJob`                                    | 2.0    | One step from a decision, or a pipeline that will fail   |
| `dataset`                                             | 1.0    | Intermediate — its own consumers carry the real weight   |
| anything else                                         | 1.0    | Default                                                  |

If the entity type is not reported, derive it from the URN: `urn:li:dashboard:(...)` is a dashboard.

### Multipliers

| Condition                            | Multiplier | Signal                                         |
| ------------------------------------ | ---------- | ---------------------------------------------- |
| Has at least one owner               | ×1.5       | Someone is accountable — someone will be paged |
| Carries a Tier1 or PII glossary term | ×2.0       | Business-critical or regulated                 |
| Belongs to a domain                  | ×1.3       | Governed asset, not a scratch table            |

Multipliers compose. A PII dashboard with an owner, 1 hop away, scores `3.0 × 0.5 × 1.5 × 2.0 = 4.5`.

### Rounding

Carry the exact values through every multiplication and through the sum. Round to **two decimals only when displaying** — never round a row and then add the rounded column, or the total will not match the scores above it.

### Hop decay

`1 / (1 + hops)`, where 1 hop is a direct consumer.

| Hops | Decay |
| ---- | ----- |
| 1    | 0.50  |
| 2    | 0.33  |
| 3    | 0.25  |

Decay is deliberately gentle. A dashboard three hops away still outranks a scratch dataset one hop away — which is correct, because the dashboard is what someone is looking at right now.

## Worked example

A Snowflake table breaks. Four consumers found:

| Consumer            | Type      | Hops | Owner | Tier1/PII | Domain | Score                               |
| ------------------- | --------- | ---- | ----- | --------- | ------ | ----------------------------------- |
| `exec_revenue`      | dashboard | 2    | yes   | yes       | yes    | 3.0 × 0.33 × 1.5 × 2.0 × 1.3 = 3.86 |
| `order_details`     | dataset   | 1    | yes   | no        | yes    | 1.0 × 0.50 × 1.5 × 1.3 = 0.98       |
| `daily_export`      | dataJob   | 1    | no    | no        | no     | 2.0 × 0.50 = 1.00                   |
| `stg_orders_backup` | dataset   | 3    | no    | no        | no     | 1.0 × 0.25 = 0.25                   |

Total: **6.09** (sum of the exact values, rounded once). Ranking: `exec_revenue` first, then `daily_export`, then `order_details`, then the backup.

Note what the formula did: `exec_revenue` sits further away than `order_details` and still outranks it four to one, because a governed PII dashboard is what someone is looking at right now. Distance matters less than who consumes the output.

## Why this is arithmetic and not judgement

The consumer facts — type, hops, owners, glossary terms, domain — come from DataHub. The ranking is then pure arithmetic, so the same graph produces the same ranking on every run. Report facts, then apply the formula. Do not eyeball the order.

## Owners to notify

Collect owner URNs from every impacted consumer, deduplicate, and sort. Report them as a flat list alongside the ranked table.

This is the operational output of the whole step. "20 consumers affected" is information. "These four groups need to know now" is an action.
