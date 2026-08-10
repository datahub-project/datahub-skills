# GraphQL reference

Queries backing `/datahub-ml-impact`. All run against `/api/graphql`.

## Downstream ML consumers of a dataset

`searchAcrossLineage` returns a `degree` per result, which is the hop count. Models sit two hops from
the source dataset because an `MLFeature` sits between them, so do not cap at one hop.

```graphql
query MLConsumers($urn: String!, $count: Int!) {
  searchAcrossLineage(
    input: {
      urn: $urn
      direction: DOWNSTREAM
      query: "*"
      start: 0
      count: $count
    }
  ) {
    total
    searchResults {
      degree
      entity {
        urn
        type
        ... on MLFeature {
          name
          properties {
            description
            sources {
              urn
            }
          }
        }
        ... on MLFeatureTable {
          name
          properties {
            description
            mlFeatures {
              urn
              name
            }
          }
        }
        ... on MLModel {
          name
          properties {
            description
            mlFeatures {
              urn
              name
            }
          }
          tags {
            tags {
              tag {
                name
              }
            }
          }
        }
      }
    }
  }
}
```

Filter results to `type` in `MLFEATURE`, `MLFEATURETABLE`, `MLMODEL`, `MLMODELGROUP`.

## Source schema, for column mapping

```graphql
query DatasetSchema($urn: String!) {
  dataset(urn: $urn) {
    urn
    name
    schemaMetadata {
      fields {
        fieldPath
        nativeDataType
        nullable
        description
      }
    }
  }
}
```

Match `fields[].fieldPath` against the `name` of each `MLFeature` from the first query.

## Features a specific model consumes

Use when the user names a model rather than a dataset.

```graphql
query ModelFeatures($urn: String!) {
  mlModel(urn: $urn) {
    urn
    name
    properties {
      description
      mlFeatures {
        urn
        name
        properties {
          sources {
            urn
          }
        }
      }
    }
  }
}
```

`properties.mlFeatures[].properties.sources[]` walks back to the source datasets, which is the
inverse of the main query.

## URN shapes

| Entity         | Form                                                              |
| -------------- | ----------------------------------------------------------------- |
| Dataset        | `urn:li:dataset:(urn:li:dataPlatform:<platform>,<name>,<fabric>)` |
| MLFeature      | `urn:li:mlFeature:(<featureNamespace>,<name>)`                    |
| MLFeatureTable | `urn:li:mlFeatureTable:(urn:li:dataPlatform:<platform>,<name>)`   |
| MLModel        | `urn:li:mlModel:(urn:li:dataPlatform:<platform>,<name>,<fabric>)` |
| Schema field   | `urn:li:schemaField:(<datasetUrn>,<fieldPath>)`                   |

Use the schema-field form when citing a specific column, so the citation resolves in the UI.

## Notes

- `degree` may be absent on older GMS releases; treat a missing value as one hop and say the depth is
  approximate.
- Sibling entities (the same asset ingested from two platforms) can appear twice. De-duplicate on the
  entity name before counting models, or the blast radius will be overstated.
