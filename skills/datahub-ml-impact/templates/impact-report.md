# ML impact report template

Fill and present. Omit sections that have no content rather than printing empty headings.

---

**ML impact of `{entity_name}`**

{n_models} model(s) consume this data, through {n_features} feature(s).

## Models

| Model          | Hops   | Features consumed | Production       |
| -------------- | ------ | ----------------- | ---------------- |
| `{model_name}` | {hops} | {feature_list}    | {yes/no/unknown} |

## Column mapping

| Column     | Consumed as      | Models   |
| ---------- | ---------------- | -------- |
| `{column}` | `{feature_name}` | {models} |

Columns not known to be consumed: {unmatched_columns}
_Not known to be consumed is not the same as unused - see evidence below._

## Evidence

- Mapping basis: {column-level lineage | feature-name matching}
- Traversal depth: {depth}{, capped if applicable}
- {any sibling de-duplication applied}

## If `{column}` changes

| Model          | Consequence                                         |
| -------------- | --------------------------------------------------- |
| `{model_name}` | {feature goes null / parse fails / feature missing} |

---

## Guidance

- Lead with the count, then the table. The reader wants "two models" before they want URNs.
- Name models by their display name; keep URNs for citations at the end.
- If nothing downstream is ML, say exactly that and stop - do not pad the report with dataset
  consumers, which is `/datahub-lineage`'s job.
- Never state that a column is safe to drop. State what is known to consume it and what evidence
  that rests on.
- Do not recommend retraining, schedule changes, or rollbacks. Report impact; the decision is the
  user's.
