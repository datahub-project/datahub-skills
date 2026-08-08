# DataHub Code Guardian

Check repository code against the catalog that governs the data it touches, repair only what the catalog proves, and record the verdict back so the next agent inherits it.

## What it does

1. Maps the code to the catalog — which governed assets does this repository actually name?
2. Reads the check history on those assets **before** proposing anything
3. Checks the code against catalog facts — schema, types, ownership, tags, lineage
4. Repairs only what the catalog proves, and verifies by re-running the check
5. Records every verdict back as a custom assertion, passes included

## Capabilities

- **Retired columns** — source still reads a column the catalog no longer declares
- **Type disagreements** — a cast or comparison that contradicts the declared type
- **Unreviewable dependencies** — code depending on assets with no owner and no description
- **Blast radius** — how far a change to a named asset reaches downstream
- **Proven repairs** — a rename applied only when column-level lineage proves it
- **Durable memory** — verdicts written back as custom assertions with a stable identity

## Usage

```
/datahub-code-guardian check this repo against DataHub before I merge
/datahub-code-guardian what has already been tried on ecommerce.analytics.orders?
/datahub-code-guardian the orders table dropped legacy_total, fix the pipeline
/datahub-code-guardian record what this run concluded back to the catalog
```

All file edits and all catalog writes require your explicit approval.

## Works on DataHub Core

The whole loop runs on open source DataHub. `upsertCustomAssertion` and `reportAssertionResult` are available on Core, so nothing here requires Cloud.
