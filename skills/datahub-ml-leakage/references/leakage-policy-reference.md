# Leakage Policy Reference

Default predicates, reason codes, and fail-closed rules for `datahub-ml-leakage`.

---

## Policy shape

A leakage policy is three things: what is forbidden, how far to look, and what to do when you cannot see.

| Setting            | Default                                         | Notes                                                              |
| ------------------ | ----------------------------------------------- | ------------------------------------------------------------------ |
| `forbidden_tags`   | `post_outcome`, `is_target`, `label`, `outcome` | Matched on tag URNs, not display strings                           |
| `forbidden_terms`  | _(empty)_                                       | Glossary terms — most orgs already model outcome data here         |
| `max_hops`         | `6`                                             | Deep enough for staging → mart → feature store; bounded on purpose |
| `on_unresolvable`  | `block`                                         | Dangling URN, permission error, timeout                            |
| `on_truncated`     | `block`                                         | Walk hit `max_hops` with frontier remaining                        |
| `on_no_provenance` | `block`                                         | Model records no features or training datasets                     |

Confirm the tag set with the user before traversing. Establishing the policy
after seeing the graph makes every verdict unfalsifiable.

## Resolving tag URNs

Tag filters and comparisons require full URNs:

```bash
datahub -C skill=datahub-ml-leakage search "post outcome" --where "entity_type = tag" --urns-only --limit 5
```

Name-based tag URNs look like `urn:li:tag:post_outcome`. GUID-based ones are
opaque — resolve by searching, never by constructing a guess.

## Reason codes

| Code                 | Verdict    | Meaning                                                                 |
| -------------------- | ---------- | ----------------------------------------------------------------------- |
| `TARGET_LEAKAGE`     | `blocked`  | A traversed path reached a node carrying a forbidden tag or term        |
| `INCOMPLETE_LINEAGE` | `blocked`  | Provenance missing, empty, or a hop could not be resolved               |
| `TRUNCATED_LINEAGE`  | `blocked`  | The walk hit `max_hops` with unexplored frontier                        |
| `POLICY_EMPTY`       | _(none)_   | No forbidden tags exist in the estate — the check is vacuous, not clean |
| `NO_VIOLATION`       | `approved` | Walk completed, every hop resolved, nothing forbidden reached           |

`POLICY_EMPTY` is deliberately not a verdict. A check with nothing to check for
should be reported as unusable so someone tags the outcome columns first.

## Why fail-closed

An approval means "I traversed the provenance and it is clean." A model whose
lineage could not be read produces the same absence of findings as a model that
is genuinely clean. Collapsing those two states into `approved` makes the check
worse than no check, because it manufactures confidence.

So: `approved` requires positive evidence of completeness — every hop resolved,
the walk terminated on its own rather than on its bound, and column-level edges
were available for a column-level question.

## What is not a leakage signal

Do not block on these alone:

- **A scary column name.** `is_fraud_score` may be a model input, not the label.
- **A `PII` or `sensitive` tag.** That is an access-control concern, not leakage.
- **A dataset-level tag on a wide table**, when the traversed column is a
  different field in that table. Report it as a weaker signal and say why.
- **Downstream position.** Being late in the pipeline is not the same as being
  derived from an outcome.

Conversely, a forbidden tag on a node you actually traversed is sufficient. You
do not need to explain the business mechanism to issue the block — though naming
it (see below) makes the block far more likely to be acted on.

## Common leakage mechanisms worth naming in a report

| Mechanism          | What it looks like in lineage                                            |
| ------------------ | ------------------------------------------------------------------------ |
| Rename             | Forbidden column feeds a differently-named staging column                |
| Aggregate          | Outcome column absorbed into a `SUM`/`AVG` that becomes a feature        |
| Post-outcome event | Field only populated after the outcome (refunds, cancellations, cures)   |
| Label copy         | The target column itself, reshaped and re-served through a feature store |
| Join contamination | A safe fact table joined to an outcome table, exported as one dataset    |

Naming the mechanism converts a policy violation into an actionable fix. Name it
only when the traversed path supports it; otherwise report the path alone.

## Depth guidance

`max_hops = 6` covers most real estates (source → staging → cleaned → mart →
aggregate → feature). Raising it increases both runtime and per-field label
lookups. Lowering it increases truncated blocks. If truncation is frequent, the
right response is usually to raise the bound once, deliberately, rather than to
relax the fail-closed rule.
