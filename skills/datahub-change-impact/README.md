# DataHub Change Impact

Analyze the downstream blast radius and risk of a proposed schema or asset
change — rename, drop, or deprecate — before you make it, using DataHub's
own lineage and metadata context.

## What it does

1. Classifies the change (rename / drop / deprecate) from a plain-English
   description
2. Resolves the target asset via `datahub-search`, stopping to disambiguate
   rather than guessing when multiple candidates match
3. Traces the downstream blast radius via `datahub-lineage`, scoped to the
   specific column when the change is column-level, and states explicitly
   when the trace had to fall back from column-level to table-level
   confidence
4. Scores risk with a transparent, named-signal heuristic — downstream
   count, business-facing exposure, pipeline involvement, missing
   ownership — never an opaque tier with no stated reason
5. Proposes a mitigation plan tailored to the change type and risk tier
6. On explicit confirmation only, hands off to `datahub-enrich` to persist
   the analysis as durable catalog context

## Usage

```
/datahub-change-impact what breaks if I rename customer_id in orders?
/datahub-change-impact impact of dropping loyalty_status from customer_profile
/datahub-change-impact is it safe to deprecate the customer_features table?
```

Or ask naturally: "what's the blast radius of changing the orders table?",
"who's affected if I remove this column?".

## Notes

- Read-and-recommend by default. Write-back only happens if you confirm it,
  following `datahub-enrich`'s own propose-then-confirm pattern.
- Composes `datahub-search`, `datahub-lineage`, optionally `datahub-quality`,
  and `datahub-enrich` — it does not duplicate their underlying tool calls,
  and degrades gracefully (with an explicit note on what was skipped) if any
  of them are unavailable in a given DataHub deployment.
- The risk heuristic is intentionally simple and explainable rather than
  statistical, so a reviewer can audit exactly why a change was scored the
  way it was.
