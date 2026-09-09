# Coverage Metrics Reference

Use this reference when selecting audit dimensions, building a projection, normalizing sibling metadata, or calculating coverage.

## Contents

- [Metric definitions](#metric-definitions)
- [Effective metadata precedence](#effective-metadata-precedence)
- [Field discovery and projection](#field-discovery-and-projection)
- [Sibling normalization](#sibling-normalization)
- [Scoring](#scoring)
- [Prioritization](#prioritization)

## Metric definitions

| Dimension                    | Eligible population                                                           | Covered when                                                           | Common exclusions                                    |
| ---------------------------- | ----------------------------------------------------------------------------- | ---------------------------------------------------------------------- | ---------------------------------------------------- |
| Asset description            | Logical assets whose type supports descriptions                               | Non-blank ingestion, editable, or effective sibling description exists | Generated placeholders only when policy defines them |
| Ownership                    | Logical assets in scope                                                       | At least one accepted owner type is present                            | Service accounts only when policy excludes them      |
| Domain                       | Logical assets in scope that may belong to a domain                           | A domain is assigned                                                   | Assets intentionally global only when documented     |
| Classification               | Logical assets in scope                                                       | Required tag or glossary-term rule is satisfied                        | Assets outside the policy's classified population    |
| Column documentation (asset) | Dataset logical assets with a readable schema and at least one eligible field | Every eligible field has an effective description                      | Policy-defined technical fields                      |
| Column documentation (field) | Eligible fields on readable dataset schemas                                   | Non-blank ingestion or editable field description exists               | Policy-defined technical fields                      |
| Lineage readiness            | Asset types for which lineage is expected by policy                           | Required upstream/downstream relationship exists                       | Sources or terminal assets explicitly exempted       |

Do not assume every asset requires every dimension. Apply the user's policy first and show exclusions.

## Effective metadata precedence

Treat a value as covered when any accepted source supplies a non-blank value:

1. user-edited value on the primary logical entity;
2. ingestion-provided value on the primary logical entity;
3. accepted effective value on a linked primary sibling;
4. accepted value on another sibling when no primary is declared.

Precedence selects what to display; it does not mean lower-precedence values are invalid. Trim whitespace before testing descriptions. Do not treat placeholder strings such as `TODO` as missing unless the user's policy defines a placeholder rule.

For fields, join editable schema metadata by exact `fieldPath`. A field is documented if either `schemaMetadata.fields[].description` or its matching `editableSchemaMetadata.editableSchemaFieldInfo[].description` is non-blank.

## Field discovery and projection

GraphQL schemas vary by DataHub version and deployment. Validate fields before running a large audit:

```bash
datahub graphql --describe searchAcrossEntities --recurse --format json
datahub search "*" --where "entity_type = dataset" --projection "<projection>" --dry-run
```

Start with this dataset projection and remove dimensions not being measured. If a field is unavailable, inspect the schema and mark that dimension unavailable rather than guessing a replacement.

```graphql
urn
type
... on Dataset {
  properties { name description }
  editableProperties { description }
  platform { name }
  ownership { owners { owner type } }
  domain { domain { urn } }
  globalTags { tags { tag { urn } } }
  glossaryTerms { terms { term { urn } } }
  schemaMetadata {
    fields {
      fieldPath
      description
      globalTags { tags { tag { urn } } }
      glossaryTerms { terms { term { urn } } }
    }
  }
  editableSchemaMetadata {
    editableSchemaFieldInfo {
      fieldPath
      description
      globalTags { tags { tag { urn } } }
      glossaryTerms { terms { term { urn } } }
    }
  }
  siblings {
    isPrimary
    siblings {
      urn
      ... on Dataset {
        properties { name description }
        editableProperties { description }
        ownership { owners { owner type } }
        domain { domain { urn } }
      }
    }
  }
}
```

Use the corresponding GraphQL type and supported fields for dashboards, charts, data flows, data jobs, and containers. Discover them with `--dry-run` or `graphql --describe`; do not reuse a Dataset fragment for every type.

### Count integrity

Record:

- facet or search total at audit start;
- number of pages requested and succeeded;
- physical entity rows parsed;
- logical assets after deduplication;
- unmeasured rows and reason;
- total at audit end for long-running audits when practical.

## Sibling normalization

Build an undirected graph whose vertices are dataset URNs and edges are sibling relationships. Each connected component is one logical dataset.

Canonical selection:

1. declared primary entity;
2. otherwise lexicographically smallest URN for deterministic output.

Do not merge physical properties such as row count, platform, or usage into a single ambiguous value. Keep those as per-entity evidence. Merge only metadata dimensions whose effective behavior is part of the audit policy.

If sibling links point outside the fetched scope, fetch those siblings when needed to evaluate effective metadata, but do not add them to the denominator unless they independently match the scope.

## Scoring

Per-dimension coverage:

```text
dimension percentage = covered / eligible * 100
```

Round only for display; retain integer counts and unrounded values for aggregate calculations.

If the user explicitly requests a single score:

```text
coverage score = sum(dimension percentage * normalized dimension weight)
```

Normalize weights across measured dimensions only. Example: if three equally weighted dimensions are measured, each has weight `1/3`. Show the per-dimension values even when an aggregate score is present.

Never convert an unavailable dimension to zero. Use `N/A` and explain the capability or permission gap.

## Prioritization

Use only catalog evidence. A defensible default ranking tuple is:

1. explicit tier/criticality descending;
2. production before non-production;
3. downstream reach or popularity descending when measured;
4. number of failed required dimensions descending;
5. canonical name ascending.

Label each signal's source. If criticality, lineage, or usage was not collected, omit it from the ranking and state that limitation.
