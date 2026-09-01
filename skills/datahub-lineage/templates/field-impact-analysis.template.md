# Field Impact Analysis

## Target Change

**Entity:** <!-- entity name -->
**URN:** <!-- exact DataHub URN -->
**Changed fields:** <!-- field names -->
**Before/after contract:** <!-- schema, type, unit, or semantic change -->
**Observed at:** <!-- timestamp -->

## Query Provenance

| Scope         | Tool | Direction | Depth | Result cap | Complete? | Queried at |
| ------------- | ---- | --------- | ----- | ---------- | --------- | ---------- |
| Dataset graph |      |           |       |            |           |            |
| Changed field |      |           |       |            |           |            |

**Fallbacks used:** <!-- none, MCP to CLI, CLI to SDK, etc. -->
**Known freshness or ingestion limits:** <!-- limits or none observed -->

## Classification Summary

| State       | Count | Meaning                                                       |
| ----------- | ----- | ------------------------------------------------------------- |
| `AFFECTED`  |       | A changed field reaches the asset through a directed path     |
| `PRESERVED` |       | Complete field evidence proves only unchanged fields reach it |
| `UNKNOWN`   |       | Available lineage cannot prove affected or preserved          |

## Affected Paths

| Asset | URN | Changed field path | Hop | Owner | Evidence |
| ----- | --- | ------------------ | --- | ----- | -------- |
|       |     |                    |     |       |          |

## Preserved Paths

Do not list an asset here from absence of a changed-field edge. State the positive field
evidence and why the relevant path is complete.

| Asset | URN | Unchanged field path | Completeness proof | Owner | Evidence |
| ----- | --- | -------------------- | ------------------ | ----- | -------- |
|       |     |                      |                    |       |          |

## Unknown Paths

| Asset | URN | Missing or ambiguous evidence | Required next check |
| ----- | --- | ----------------------------- | ------------------- |
|       |     |                               |                     |

## Consequential Consumers

| Consumer | Type | First affected path | Consequence | Evidence |
| -------- | ---- | ------------------- | ----------- | -------- |
|          |      |                     |             |          |

## Completeness Checks

- [ ] Every dataset-level downstream asset appears in exactly one classification.
- [ ] Affected and preserved URN sets are disjoint.
- [ ] Every preserved claim has positive, complete field-level evidence.
- [ ] Capped or truncated queries were retried or disclosed.
- [ ] The report records query provenance and uncertainty.
- [ ] No halt, allow, or resume decision is presented as a lineage fact.
