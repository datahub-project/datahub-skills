# `get_lineage` / `get_entities` response shapes for ML entities

Observed against `mcp-server-datahub` 0.6.0 / DataHub 1.5.x (OSS quickstart).
Field paths worth knowing when writing detector code against these tools.

## `get_lineage(urn=<mlModel urn>, upstream=true, ...)`

Top-level key is the direction you asked for (`upstreams` or
`downstreams`), not a generic `results`:

```json
{
  "upstreams": {
    "total": 16,
    "facets": [...],
    "searchResults": [
      {
        "entity": {
          "urn": "urn:li:dataset:(urn:li:dataPlatform:duckdb,raw.raw_refunds,PROD)",
          "type": "DATASET",
          "name": "raw_refunds",
          "platform": {"urn": "...", "name": "duckdb"},
          "properties": {
            "name": "raw_refunds",
            "description": "...",
            "customProperties": [
              {"key": "dbt_layer", "value": "raw"}
            ]
          },
          "ownership": {"owners": [...]},
          "glossaryTerms": {
            "terms": [
              {"term": {"urn": "urn:li:glossaryTerm:PostOutcomeEvent", "hierarchicalName": "PostOutcomeEvent", "properties": {...}}}
            ]
          },
          "subTypes": {"typeNames": ["Raw Table"]},
          "health": [{"type": "INCIDENTS", "status": "PASS"}]
        },
        "degree": 4
      },
      {
        "entity": {
          "urn": "urn:li:mlFeature:(customer_features_table,days_since_last_refund)",
          "type": "MLFEATURE",
          "name": "days_since_last_refund",
          ...
        },
        "degree": 1
      }
    ]
  }
}
```

Key points:

- `customProperties` is a **list** of `{key, value}` objects, not a dict --
  build a dict yourself: `{p["key"]: p["value"] for p in customProperties}`.
- `glossaryTerms.terms[].term.urn` is where to check for governance-tag-style
  signals (leakage markers, PII, etc).
- `paths` is stripped from entity-level results (present only for
  column-level lineage queries) -- you get the full upstream _set_, not
  edge-level attribution back to a specific feature.
- Both `Dataset` and `MLFeature` (and `MLFeatureTable`, `MLModelGroup` if
  present) entities come back in the same flat list, distinguished by
  `type`.

## `get_entities(urn=<mlModel urn>)`

Deliberately lighter than lineage results -- does **not** include
`MLModelProperties.mlFeatures`, `deployments`, `trainingMetrics`, or
`customProperties`:

```json
{
  "urn": "urn:li:mlModel:(urn:li:dataPlatform:duckdb,churn_predictor,PROD)",
  "name": "churn_predictor",
  "description": "...",
  "origin": "PROD",
  "ownership": {"owners": [...]},
  "platform": {"urn": "...", "name": "duckdb"},
  "relatedDocuments": {"start": 0, "count": 10, "total": 0}
}
```

Same goes for `get_entities` on an `MLFeature` urn -- no `sources` field.
If you need those, use `get_lineage` from the model (see above), or issue a
raw `datahub.ingestion.graph.client.DataHubGraph.get_aspect(...)` call for
`MLFeatureProperties` / `MLModelProperties` directly against GMS.

## `Dataset` entities generally

`Dataset` entities returned from either tool _do_ include
`properties.customProperties` and `glossaryTerms` -- this is what makes the
staleness/leakage detection patterns in this skill possible without a raw
REST fallback.
