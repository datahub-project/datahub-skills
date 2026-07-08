# datahub-ml-drift-rca

Root-cause silent ML model degradation in DataHub: walk lineage to the upstream change, identify the owner, and write the cause back.

## What it does

- Confirms a drift signal is real degradation, not benign drift the model is invariant to
- Walks model lineage (via `searchAcrossLineage`) to the upstream table that changed
- Reads the owning team from catalog ownership
- Writes the finding back: a `drift_causation` structured property and a document on the model, plus an incident on the upstream dataset (because the incident metamodel does not allow incidents on `mlModel`)

## Usage

```
> My purchase_intent model's AUC dropped. Root-cause it.
> Which upstream change degraded this model?
> Trace this drift to its source and record it in DataHub
```

## Files

- `SKILL.md` — the procedure and judgment
- `standards/drift-root-cause.md` — drift vs degradation, the write-back split, honesty
- `references/datahub-apis.md` — the exact reads and writes
- `templates/drift-causation.md` — the structured-property, RCA-document, and incident templates
