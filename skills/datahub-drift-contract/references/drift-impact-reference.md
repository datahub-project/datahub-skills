# Drift Impact — technical reference

Details behind the `datahub-drift-contract` skill. Verified against DataHub v1.5 /
`mcp-server-datahub` v0.6.0.

## Why column-level needs the fine-grained aspect

`get_lineage(urn, column=...)` and `datahub lineage --column` resolve lineage but return the
downstream **dataset(s)**, not the specific downstream columns. The exact column→column edges
live in the downstream dataset's `upstreamLineage.fineGrainedLineages`:

```
fineGrainedLineages: [
  { upstreams:  ["urn:li:schemaField:(<src_urn>,haircut_pct)", ...],
    downstreams:["urn:li:schemaField:(<report_urn>,collateral_after_haircut)"],
    transformOperation: "market_value * (1 - haircut_pct/100)" },
  ...
]
```

Build `upstream_column → [downstream_columns]` from these edges and traverse (BFS) to get the
transitive impacted set for a changed upstream column.

## schemaField URN parsing

`urn:li:schemaField:(<dataset_urn>,<column>)`. The dataset URN itself contains commas and
parens, so split on the **top-level** comma only (scan characters, tracking paren depth; split at
the first comma seen at depth 0).

## Severity model

| change  | severity       | rationale                                             |
| ------- | -------------- | ----------------------------------------------------- |
| dropped | `hard_break`   | transform input disappears → error/null               |
| renamed | `hard_break`   | referenced name gone → same as dropped for the report |
| retyped | `silent_break` | value flows but miscomputes → no error, wrong numbers |

## Write-back call shapes (MCP, mutations enabled)

- `add_tags`: `{tag_urns:[...], entity_urns:[<dataset_urn>], column_paths:[<col>]}` — tag entities
  must already exist.
- `add_structured_properties`: `{property_values:{<prop_urn>:[<vals>]}, entity_urns:[<schemaField_urn>]}`
  — no `column_paths`; property must be defined first.
- `update_description`: `{entity_urn:<dataset_urn>, column_path:<col>, operation:"replace", description:<text>}`.
- Read-back: `editableSchemaMetadata` aspect → `editableSchemaFieldInfo[].globalTags` + `.description`.

## Reference implementation

A deterministic Python implementation of exactly this workflow (impact engine + write-back +
Gemini narration + UI) lives in the **Compliance Drift Sentinel** project this skill was
extracted from: `engine/impact.py`, `engine/lineage_graph.py`, `engine/writer.py`.
