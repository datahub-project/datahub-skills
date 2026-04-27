# Audit Patterns Reference

Query patterns for each coverage dimension. All queries use `datahub -C skill=datahub-audit` for attribution.

---

## Coverage Dimensions

### Description Coverage

Checks both ingestion-provided (`properties.description`) and user-edited (`editableProperties.description`) descriptions. An entity is undocumented only if both are absent — and only if its siblings are also undocumented.

```bash
# Missing descriptions — with sibling projection for deduplication
datahub -C skill=datahub-audit search "*" \
  --where "entity_type = dataset AND description IS NULL AND editableDescription IS NULL" \
  --projection "urn type
    ... on Dataset { properties { name description } editableProperties { description }
      platform { name }
      siblings { isPrimary siblings { urn
        ... on Dataset { properties { description } editableProperties { description } }
      }}
    }" \
  --format json --limit 50

# Total entity count for denominator
datahub -C skill=datahub-audit search "*" \
  --where "entity_type = dataset" \
  --facets-only --format json
```

**Sibling rule:** If `siblings.isPrimary = false`, the sibling is the canonical source. Check the sibling's description before counting the entity as undocumented.

---

### Ownership Coverage

```bash
# Entities with no owners
datahub -C skill=datahub-audit search "*" \
  --where "entity_type = dataset AND owners IS NULL" \
  --projection "urn type
    ... on Dataset { properties { name } platform { name }
      globalTags { tags { tag { urn properties { name } } } }
    }" \
  --format json --limit 50
```

---

### Tag Coverage

```bash
# Entities with no tags
datahub -C skill=datahub-audit search "*" \
  --where "entity_type = dataset AND tags IS NULL" \
  --projection "urn type ... on Dataset { properties { name } platform { name } }" \
  --format json --limit 50

# Entities with a specific tag — resolve URN first
# Step 1: resolve tag URN
datahub -C skill=datahub-audit search "pii" \
  --where "entity_type = tag" --urns-only --limit 1

# Step 2: count entities with that tag
datahub -C skill=datahub-audit search "*" \
  --where "entity_type = dataset AND tags = 'urn:li:tag:<TAG_URN>'" \
  --facets-only --format json
```

---

### Glossary Term Coverage

```bash
# Entities with no glossary terms
datahub -C skill=datahub-audit search "*" \
  --where "entity_type = dataset AND glossary_term IS NULL" \
  --projection "urn type ... on Dataset { properties { name } platform { name } }" \
  --format json --limit 50
```

---

### Domain Assignment Coverage

```bash
# Entities not assigned to any domain
datahub -C skill=datahub-audit search "*" \
  --where "entity_type = dataset AND domain IS NULL" \
  --projection "urn type ... on Dataset { properties { name } platform { name } }" \
  --format json --limit 50

# Entities in a specific domain
datahub -C skill=datahub-audit search "*" \
  --where "entity_type = dataset AND domain = 'urn:li:domain:<DOMAIN_ID>'" \
  --facets-only --format json
```

---

### Field-Level (Column) Description Coverage

Column descriptions require fetching schema metadata per entity. Sample rather than fetch all for large scopes.

```bash
datahub -C skill=datahub-audit search "*" \
  --where "entity_type = dataset AND platform = snowflake" \
  --projection "urn type
    ... on Dataset { properties { name }
      schemaMetadata { fields { fieldPath description } }
      editableSchemaMetadata { editableSchemaFieldInfo { fieldPath description } }
    }" \
  --format json --limit 20
```

**Counting undocumented columns:** For each entity, count fields where both `schemaMetadata.fields[i].description` and the matching `editableSchemaMetadata.editableSchemaFieldInfo[i].description` are null or empty.

---

## Governance Patterns

### Data Product Coverage

```bash
# Datasets not in any data product
datahub -C skill=datahub-audit search "*" \
  --where "entity_type = dataset AND data_product IS NULL" \
  --projection "urn type
    ... on Dataset { properties { name } platform { name }
      domain { properties { name } }
    }" \
  --format json --limit 50
```

---

### Deprecation Hygiene

```bash
# Step 1: find deprecated datasets
datahub -C skill=datahub-audit search "*" \
  --where "entity_type = dataset AND deprecated = true" \
  --projection "urn type
    ... on Dataset { properties { name } platform { name }
      deprecation { deprecated note decommissionTime }
    }" \
  --format json --limit 50

# Step 2: for each deprecated entity, check downstream consumers
datahub lineage --urn "<URN>" --direction downstream --hops 1 --format json
```

Flag any deprecated entity with downstream consumers as a governance risk.

---

### PII Classification Audit

Finds datasets that contain PII columns (tagged at field level) but lack a PII tag at the entity level.

```bash
# Step 1: resolve PII tag URN
datahub -C skill=datahub-audit search "pii" \
  --where "entity_type = tag" --urns-only --limit 1

# Step 2: find datasets with entity-level PII tag
datahub -C skill=datahub-audit search "*" \
  --where "entity_type = dataset AND tags = 'urn:li:tag:<PII_URN>'" \
  --urns-only --format json --limit 200

# Step 3: find datasets with field-level PII tags (via editableSchemaMetadata)
# Fetch schema for a sample of datasets and check field-level tags
datahub -C skill=datahub-audit search "*" \
  --where "entity_type = dataset" \
  --projection "urn type
    ... on Dataset { properties { name }
      globalTags { tags { tag { urn } } }
      editableSchemaMetadata { editableSchemaFieldInfo {
        fieldPath globalTags { tags { tag { urn } } }
      }}
    }" \
  --format json --limit 20
```

An entity has a PII gap if any of its columns carry a PII tag but the entity itself does not.

---

## Pagination Pattern

For scopes larger than 50 entities, paginate and accumulate:

```bash
# Page 1
datahub -C skill=datahub-audit search "*" \
  --where "<filter>" --format json --limit 50 --offset 0

# Page 2
datahub -C skill=datahub-audit search "*" \
  --where "<filter>" --format json --limit 50 --offset 50

# Page 3
datahub -C skill=datahub-audit search "*" \
  --where "<filter>" --format json --limit 50 --offset 100
```

Stop paginating when the returned result count is less than the limit, or when the accumulated count reaches the user-confirmed maximum.

---

## Metric Calculation

```
coverage_pct  = (entities_with_field / total_entities) * 100
gap_count     = total_entities - entities_with_field
```

**Score thresholds:**

| Coverage % | Status |
| --- | --- |
| ≥ 80% | 🟢 Good |
| 50–79% | 🟡 Needs attention |
| < 50% | 🔴 Critical gap |
