# ML Lineage Traversal Reference

How DataHub connects a dataset to the ML models and dashboards that depend on it, and the traps that make a naive traversal report the wrong answer.

## The chain

DataHub represents the dataset-to-model dependency as three hops:

```
dataset ──(mlFeatureProperties.sources)──▶ mlFeature ──(mlModelProperties.mlFeatures)──▶ mlModel
```

| Hop               | Aspect / field                 | Direction of the reference                                 |
| ----------------- | ------------------------------ | ---------------------------------------------------------- |
| dataset → feature | `mlFeatureProperties.sources`  | The **feature** points at the datasets it is computed from |
| feature → model   | `mlModelProperties.mlFeatures` | The **model** points at the features it consumes           |

Because the references point "backwards" (a feature names its sources; a model names its features), DataHub materializes them as **downstream** lineage edges from the dataset. A `DOWNSTREAM` traversal from the dataset therefore reaches the feature at hop 1 and the model at hop 2.

Dashboards attach through ordinary dataset-to-dashboard lineage (a chart/dashboard consuming the dataset or one of its downstream tables) and show up in the same downstream traversal.

## The canonical query

`searchAcrossLineage` is the only traversal surface that lets you **skip the cache** and **filter by type**. Traverse downstream from the changed dataset:

```graphql
query ($urn: String!) {
  searchAcrossLineage(
    input: {
      urn: $urn
      direction: DOWNSTREAM
      query: "*"
      start: 0
      count: 200
      searchFlags: { skipCache: true }
    }
  ) {
    total
    searchResults {
      degree
      entity {
        urn
        type
        ... on MLModel {
          name
          properties {
            mlFeatures
          }
          ownership {
            owners {
              owner {
                ... on CorpUser {
                  urn
                }
                ... on CorpGroup {
                  urn
                }
              }
              type
            }
          }
        }
        ... on MLFeature {
          urn
          properties {
            sources
          }
        }
        ... on Dashboard {
          urn
          ownership {
            owners {
              owner {
                ... on CorpUser {
                  urn
                }
                ... on CorpGroup {
                  urn
                }
              }
              type
            }
          }
        }
      }
    }
  }
}
```

Run it via `datahub graphql --query /tmp/blast.graphql --variables /tmp/vars.json --format json`. Pass the dataset URN through `--variables` — dataset URNs contain `(`, `)`, and `,`, which break inline shell quoting.

`degree` is the hop count. A model at `degree: 2` reached via a feature at `degree: 1` is a model consuming a feature sourced from the changed dataset.

## Gotcha 1: GMS caches lineage, including empty answers

GMS caches `searchAcrossLineage` results — **empty results included** — for several minutes. A freshly ingested edge can read back as `total: 0` while the underlying relationship already exists. For a merge gate, an empty answer is interpreted as "nothing downstream, safe to merge," which is the exact failure mode a gate must avoid.

**Always send `searchFlags: { skipCache: true }`.** The `datahub lineage` CLI command has no equivalent flag, which is why the gate uses `searchAcrossLineage` via `datahub graphql`.

## Gotcha 2: `mlFeatureTable` is not on the lineage path

A `mlFeatureTable` groups features for organizational purposes. It does **not** carry `upstreamLineage`, and it does **not** appear as a downstream hop from a dataset. Do not try to reach a model through a feature table. The path runs through the individual `mlFeature` entities.

To go from a feature to its feature table (a sideways lookup, not a lineage hop), use the `Contains` relationship:

```python
from datahub.ingestion.graph.client import DatahubClientConfig, DataHubGraph
from datahub.ingestion.graph.openapi import RelationshipDirection
from datahub.metadata.urns import MlFeatureUrn

graph = DataHubGraph(DatahubClientConfig(server="http://localhost:8080"))
rels = graph.get_related_entities(
    entity_urn=str(MlFeatureUrn("user_features", "age")),
    relationship_types=["Contains"],
    direction=RelationshipDirection.INCOMING,
)
```

## Gotcha 3: the dataset → feature hop is dataset-grained

In open source, `mlFeatureProperties.sources` lists **datasets**, not columns. There is no column-level edge from a specific dataset column to a feature. Consequently, you cannot prove that a dropped column misses a feature that sources the same dataset. When a breaking change touches a dataset that a feature sources, treat the feature — and therefore the model consuming it — as **in scope**. Column-level lineage (`datahub lineage --column`) narrows only the dataset → dataset portion of the path.

## Reading the link aspects directly

When lineage is sparse or you want to confirm a single edge:

```bash
# Datasets a feature is computed from
datahub get --urn "urn:li:mlFeature:(trip_features,airport_fee)" --aspect mlFeatureProperties
# Features a model consumes
datahub get --urn "urn:li:mlModel:(urn:li:dataPlatform:mlflow,fare_predictor,PROD)" --aspect mlModelProperties
```

`mlFeatureProperties.sources` is the dataset list; `mlModelProperties.mlFeatures` is the feature list. Cross-reference them to reconstruct the chain by hand.

## URN shapes

| Entity         | URN shape                                                       |
| -------------- | --------------------------------------------------------------- |
| dataset        | `urn:li:dataset:(urn:li:dataPlatform:<platform>,<name>,<env>)`  |
| mlFeature      | `urn:li:mlFeature:(<featureNamespace>,<name>)`                  |
| mlFeatureTable | `urn:li:mlFeatureTable:(urn:li:dataPlatform:<platform>,<name>)` |
| mlModel        | `urn:li:mlModel:(urn:li:dataPlatform:<platform>,<name>,<env>)`  |
