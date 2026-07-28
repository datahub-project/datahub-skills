# ML Entity Model Reference

The entities and aspects a traversal touches, and the URN shapes needed to build a
query by hand. The authoritative field-by-field definitions are in the metamodel
docs — [mlModel](https://docs.datahub.com/docs/generated/metamodel/entities/mlmodel),
[mlFeature](https://docs.datahub.com/docs/generated/metamodel/entities/mlfeature),
[mlFeatureTable](https://docs.datahub.com/docs/generated/metamodel/entities/mlfeaturetable),
[mlModelGroup](https://docs.datahub.com/docs/generated/metamodel/entities/mlmodelgroup),
[mlModelDeployment](https://docs.datahub.com/docs/generated/metamodel/entities/mlmodeldeployment),
[dataProcessInstance](https://docs.datahub.com/docs/generated/metamodel/entities/dataprocessinstance).
This page covers what a traversal needs that a field list does not say.

## Entities and how you reach them

| Entity                | Reached by                                | Searchable by `entity_type` |
| --------------------- | ----------------------------------------- | --------------------------- |
| `mlModel`             | search, or a group's members              | yes                         |
| `mlModelGroup`        | search, or `mlModelProperties.groups`     | yes                         |
| `mlFeature`           | search, or `mlModelProperties.mlFeatures` | yes                         |
| `mlFeatureTable`      | search, or a feature's containing table   | yes                         |
| `dataProcessInstance` | `mlModelProperties.trainingJobs`          | yes                         |
| `mlModelDeployment`   | `mlModelProperties.deployments` **only**  | **no** — see below          |

`entity_type = mlModelDeployment` fails: the filter maps to `ML_MODEL_DEPLOYMENT`,
which is not a member of the GraphQL `EntityType` enum. Deployments are reachable
only by following a model.

## URN shapes

```
urn:li:mlModel:(urn:li:dataPlatform:<platform>,<name>,<env>)
urn:li:mlModelGroup:(urn:li:dataPlatform:<platform>,<name>,<env>)
urn:li:mlModelDeployment:(urn:li:dataPlatform:<platform>,<name>,<env>)
urn:li:mlFeatureTable:(urn:li:dataPlatform:<platform>,<table_name>)
urn:li:mlFeature:(<feature_table_name>,<feature_name>)
urn:li:dataProcessInstance:<id>
urn:li:schemaField:(<dataset_urn>,<column_name>)
```

Two of these break the pattern and cost time if you assume otherwise:

- **`mlFeature` has no platform segment.** It is keyed by feature-table _name_,
  not by the feature table's URN. You cannot build a feature URN from a feature
  table URN by substitution; read `mlFeatureTableProperties.mlFeatures` instead.
- **`dataProcessInstance` is a bare id**, with no platform and no env.

`schemaField` URNs nest a full dataset URN, so they contain commas and parentheses.
Split on the _last_ comma to separate dataset from column; splitting on the first
gives you a fragment of the platform URN.

## Aspects, by the question they answer

| Question                        | Entity                | Aspect                                     |
| ------------------------------- | --------------------- | ------------------------------------------ |
| features, groups, jobs, deploys | `mlModel`             | `mlModelProperties`                        |
| which datasets trained it       | `mlModel`             | `mlModelTrainingData`                      |
| where a feature comes from      | `mlFeature`           | `mlFeatureProperties`                      |
| what a feature table contains   | `mlFeatureTable`      | `mlFeatureTableProperties`                 |
| what a run consumed             | `dataProcessInstance` | `dataProcessInstanceInput`                 |
| metrics and params of a run     | `dataProcessInstance` | `mlTrainingRunProperties`                  |
| run name and creation stamp     | `dataProcessInstance` | `dataProcessInstanceProperties`            |
| run status and timing           | `dataProcessInstance` | `dataProcessInstanceRunEvent` (timeseries) |
| how the run is labelled         | `dataProcessInstance` | `subTypes`                                 |
| is it serving                   | `mlModelDeployment`   | `mlModelDeploymentProperties`              |
| column derivations of a dataset | `dataset`             | `upstreamLineage`                          |

### The one that reads differently

`dataProcessInstanceRunEvent` is a **timeseries** aspect. A normal aspect read
raises rather than returning empty:

```
TypeError: Cannot get a timeseries aspect using "get_aspect".
           Use "get_latest_timeseries_value" instead.
```

Every other aspect on the same entity is versioned. The run's status and
completion timestamp are the only facts behind that call, so if an approximate
time is enough, `dataProcessInstanceProperties.created` avoids it.

## Granularity: what the model can and cannot express

`mlFeatureProperties.sources` holds **dataset** URNs. A `schemaField` URN is
rejected by the server:

```
Entity type for urn urn:li:schemaField:(...) is not a valid destination for field
  ERROR :: /sources/0
```

So the metamodel records which _table_ a feature draws on, not which column.
Producers that know the column generally park it in the feature's
`customProperties` or `description`; there is no standard field for it. Whether
that should change is under discussion in
[datahub#18625](https://github.com/datahub-project/datahub/issues/18625).

Practical consequence: to get from a feature to a column you go feature → source
dataset → dataset column lineage, and the mapping from feature to _which_ column
in that dataset is only as good as what the producer wrote down.

## Metrics appear twice

`trainingMetrics` is present on both `mlModelProperties` and
`mlTrainingRunProperties`, with the same name/value pairs when one producer wrote
both. Values are strings — `"0.97"`, not `0.97` — on both. Report one source.

## Versions

`mlModelProperties.groups` links a model to its `mlModelGroup`, and
`mlModelProperties.version.versionTag` carries a version label. Sorting version
tags is not a reliable way to find the newest model: the tags are free-form
strings, and lexicographic order disagrees with numeric order as soon as a
project reaches `v10`.

DataHub has a dedicated mechanism for this — the `versionProperties` aspect
(`versionSet`, `sortId`, `isLatest`) and the `versionSet` entity, populated
through the `linkAssetVersion` mutation. If `versionProperties` is present, use
`isLatest`. If it is absent, say the ordering is unknown rather than guessing from
the tag.

## Where column lineage is stored

For a column edge `A.col → B.col`, the `fineGrainedLineages` entry describing it
lives in **B**'s `upstreamLineage` aspect. Reading A shows what A consumes, not
what A feeds.

dbt ingestion emits two dataset entities per model — the `dbt` entity and the
target-platform entity — linked as siblings, and it emits column lineage both
between dbt nodes and between the dbt node and its platform twin. The result is
that the twins' column edges are split, and one side's edges can be **mirrors**
whose endpoints differ only by platform:

```
dbt:fct_customer_orders.customer_id  ->  duckdb:fct_customer_orders.customer_id
```

A traversal that collapses siblings into one canonical node and visits it once can
spend that visit on a mirror and stop, reporting no upstreams and no error. Merge
both twins' edges under the canonical key and drop self-mirrors; do not pick a
twin, because which twin carries the real derivations varies by project.
