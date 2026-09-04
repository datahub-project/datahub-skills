# Scoring model

## Components and weights

| Component     | Weight | Range | Meaning |
| ------------- | ------ | ----- | ------- |
| Quality       | 35     | 0-100 | Share of data tests or assertions passing |
| Documentation | 25     | 0-100 | Description, field-level docs and glossary coverage |
| Ownership     | 20     | 0-100 | Datasets with at least one assigned owner |
| Freshness     | 20     | 0-100 | Recency of lineage and last update |

Weights are a starting point, not a standard. Adjust them to the organization and state
the chosen weights wherever the score is shown. Persist a `score_version` alongside the
value so a change in methodology is distinguishable from a change in the data.

## Signal sources

| Component     | Primary aspect | Fallback |
| ------------- | -------------- | -------- |
| Quality       | `assertionRunEvent` results | `testResults` (`passing` / `failing`) |
| Documentation | `editableDatasetProperties.description` | `datasetProperties.description`, `editableSchemaMetadata`, `glossaryTerms` |
| Ownership     | `ownership.owners` | none |
| Freshness     | Most recent operation or update timestamp | `datasetProperties.lastModified`, presence of `upstreamLineage` |

Some deployments have no assertion entities at all. In that case `testResults` at dataset
level carries the pass and fail counts and is the correct source for the quality
component.

## Component formulas

```
quality       = passing / (passing + failing) * 100        # absent when no tests exist
documentation = 50 * has_description
              + 25 * has_field_docs
              + 25 * has_glossary_terms
ownership     = 100 if the dataset has an owner else 0
freshness     = max(0, 100 - days_since_update / WINDOW * 100)   # absent without a timestamp
```

`WINDOW` defaults to 30 days. Documentation and ownership are always available: their
absence is a real signal, not a gap. Quality and freshness can be genuinely absent.

## Renormalization

Never score an absent signal as zero. Drop it and rescale:

```
score = sum(weight_i * value_i for available i) / sum(weight_i for available i)
```

Report `coverage = sum(weight_i for available i) / 100` next to the score. A domain at 90
with 45% coverage is a different claim from a domain at 90 with full coverage, and the
reader deserves to see the difference.

## Aggregation

The domain score is the unweighted mean of its dataset scores. Weighting by business
criticality is a reasonable refinement when the organization has a criticality signal,
since treating every dataset as equally important is the most common reason these
initiatives lose credibility.

## Tiers

| Tier    | Range     |
| ------- | --------- |
| gold    | 80 to 100 |
| silver  | 60 to 79  |
| bronze  | 40 to 59  |
| at risk | below 40  |

Publish these thresholds in any interface that shows a tier. A reader who sees "bronze"
cannot tell whether that means 41 or 59 unless the scale is visible.

## Determinism

Given the same graph state, the score must be identical. Avoid sampling, avoid ordering
dependencies, and round only at presentation time.
