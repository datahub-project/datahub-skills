# Example: Drop a Column

## Input

- Root: a resolved DataHub dataset URN.
- Column: `legacy_customer_code`.
- Change: drop.
- New value: not applicable.

## Expected Workflow

1. Verify the root and field with DataHub entity/schema evidence.
2. Inspect real governance and quality context without inferring missing values.
3. Traverse column lineage first and record dataset-level fallback if needed.
4. Deduplicate and classify datasets, pipelines, dashboards/charts, and ML
   assets.
5. Apply the drop base weight plus only evidence-backed deterministic factors.
6. Generate destructive-operation SQL for review, consumer deprecation steps,
   tests, and a restore-oriented rollback plan.

## Example Output Shape

```text
Decision: <deterministic result>
Risk factors:
  +25 Drop operation
  +<points> <only evidence-backed factors>
Agent narrative: Context summary only; it cannot change the score.
Mutation: Not started.
Safety: No migration SQL was executed.
```

Never execute the generated drop statement. Never modify downstream assets. A
write-back may record the completed review only after an exact preview and
explicit human confirmation; write only to the reviewed root asset and verify
the result.
