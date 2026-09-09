# Catalog read reference

One bounded read that returns everything Step 3 compares repository code against. Sending it once per batch of assets keeps a repository pass to a handful of round trips.

## Resolving a source reference to a URN

Every name in the source has to become a URN before anything else happens. Search per name, and stop rather than guess when more than one asset matches.

```bash
datahub -C skill=datahub-code-guardian search "orders" \
  --where "entity_type = dataset AND platform = snowflake" \
  --projection "urn type ... on Dataset { properties { name } platform { name } }" \
  --format json --limit 5
```

Report the map before reading further, so the user can correct it while that is still cheap.

```markdown
| Source reference            | Resolved asset               | Confidence |
| --------------------------- | ---------------------------- | ---------- |
| `pipeline.py:12` "orders"   | `ecommerce.analytics.orders` | exact      |
| `pipeline.py:31` "invoices" | `ecommerce.marts.invoices`   | exact      |
| `report.sql:4` "daily"      | unresolved (3 candidates)    | ask user   |
```

## The catalog page

`count` and `start` page the response, and `skipHighlighting` keeps it small when the query is a wildcard.

```graphql
query DatasetPage($query: String!, $count: Int!, $start: Int!) {
  searchAcrossEntities(
    input: {
      query: $query
      count: $count
      start: $start
      types: [DATASET]
      searchFlags: { skipHighlighting: true }
    }
  ) {
    total
    searchResults {
      entity {
        urn
        ... on Dataset {
          properties {
            description
            lastModified {
              time
            }
          }
          deprecation {
            deprecated
          }
          ownership {
            owners {
              owner {
                ... on CorpUser {
                  urn
                  username
                }
                ... on CorpGroup {
                  urn
                  name
                }
              }
            }
          }
          domain {
            domain {
              urn
              properties {
                name
              }
            }
          }
          schemaMetadata {
            fields {
              fieldPath
              type
              nativeDataType
              description
              globalTags {
                tags {
                  tag {
                    urn
                    properties {
                      name
                    }
                  }
                }
              }
              glossaryTerms {
                terms {
                  term {
                    urn
                    properties {
                      name
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

Three things are easy to miss.

`ownership.owners[].owner` is a union. A query that selects only `urn` silently loses the human name a report wants to print. Spreading both `CorpUser` and `CorpGroup` is what gets you a usable identity.

`globalTags` and `glossaryTerms` sit under each entry of `schemaMetadata.fields`, not on the dataset. A tag applied through the UI lives instead under `editableSchemaMetadata.editableSchemaFieldInfo`, so a pass that must see every label reads both and merges them. The same split applies to descriptions, where `editableProperties.description` holds the UI-authored one.

`properties.lastModified.time` is epoch milliseconds. Comparing it against a cutoff is how an agent scopes a run to assets that changed since its last pass, without a second API.

## Column-level lineage

Column-level lineage is the only thing that proves a rename.

```graphql
query FieldLineage($urn: String!) {
  dataset(urn: $urn) {
    urn
    fineGrainedLineages {
      upstreams {
        urn
        path
      }
      downstreams {
        urn
        path
      }
    }
  }
}
```

`path` is the field path, which joins back to `schemaMetadata.fields[].fieldPath`. The `urn` on each side is a `schemaField` URN that embeds its dataset URN, so an intra-dataset rename is distinguishable from a cross-dataset derivation without a second lookup.

Exactly one surviving downstream field for a retired column licenses a rewrite. Two or more is an ambiguity to ask about. Zero is a breakage to report.

## Table-level lineage

`searchAcrossLineage` answers reachability, and `degree` is what turns it into a graph.

```graphql
query DatasetLineage($urn: String!, $count: Int!, $start: Int!) {
  searchAcrossLineage(
    input: {
      urn: $urn
      direction: DOWNSTREAM
      query: "*"
      count: $count
      start: $start
      searchFlags: { skipHighlighting: true }
    }
  ) {
    total
    searchResults {
      degree
      entity {
        urn
      }
    }
  }
}
```

Keep `degree` equal to one when building edges. Every result is reachable from the URN you asked about, so treating the whole response as adjacency produces a graph where the source appears to feed the entire warehouse directly, and any impact measure computed over it is wrong in a way that looks plausible.

## Running these from the CLI

Write long queries to a file and pass the path. The CLI auto-detects file paths, and long inline strings hit OS filename length limits.

```bash
cat > /tmp/catalog-read.graphql << 'EOF'
query { ... }
EOF
datahub -C skill=datahub-code-guardian graphql \
  --query /tmp/catalog-read.graphql \
  --variables /tmp/catalog-read-vars.json \
  --format json
rm /tmp/catalog-read.graphql /tmp/catalog-read-vars.json
```

Use `--variables` with a temp JSON file for anything containing a dataset URN. Dataset URNs contain `(`, `)`, and `,`, which break shell escaping.

Never invent a field spelling. `datahub graphql --describe <type> --recurse --format json` prints what actually exists on the live schema, and `--strip-unknown-fields` is a safety net on reads only, never on mutations. Do not run `datahub telemetry disable`, and ignore telemetry prompts.

## Editable versus ingested metadata

A description, tag, or glossary term applied through the UI does not land where the ingested one does. Read both and merge, or a well-governed asset reports as ungoverned.

| Field               | Ingested                                            | UI-edited                                                  |
| ------------------- | --------------------------------------------------- | ---------------------------------------------------------- |
| Asset description   | `properties { description }`                        | `editableProperties { description }`                       |
| Column descriptions | `schemaMetadata { fields { description } }`         | `editableSchemaMetadata { editableSchemaFieldInfo { … } }` |
| Column tags         | `schemaMetadata { fields { globalTags { … } } }`    | `editableSchemaMetadata { editableSchemaFieldInfo { … } }` |
| Column terms        | `schemaMetadata { fields { glossaryTerms { … } } }` | `editableSchemaMetadata { editableSchemaFieldInfo { … } }` |

## Type spellings

Compare declared types through one engine-neutral vocabulary rather than by string equality. `type` is DataHub's canonical enum and `nativeDataType` is the platform spelling, so a `NUMBER` column read through a `DECIMAL` cast is agreement, while `NUMBER` read through `STRING` is a real finding. Naive comparison reports a disagreement on every correct cast, which is the fastest way to make a check untrusted.
