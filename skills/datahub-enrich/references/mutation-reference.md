# Mutation Reference

All write operations use `datahub graphql --query '...' --format json` or MCP tools.

---

## URN Quoting

Dataset and schemaField URNs contain parentheses that break inline `--query` strings. **Use `--variables` with a temp JSON file for any mutation involving these URNs:**

```bash
cat > /tmp/enrich-vars.json << 'EOF'
{
  "input": {
    "description": "New description",
    "resourceUrn": "urn:li:dataset:(urn:li:dataPlatform:snowflake,db.schema.table,PROD)"
  }
}
EOF

datahub graphql \
  -q 'mutation updateDesc($input: DescriptionUpdateInput!) { updateDescription(input: $input) }' \
  -v /tmp/enrich-vars.json \
  --format json

rm /tmp/enrich-vars.json
```

Short mutations with simple URNs (tags, users, domains) can use inline `--query`.

---

## Tags

```bash
# Batch add tags (preferred — works for single or multiple entities)
datahub graphql --query 'mutation {
  batchAddTags(input: {
    tagUrns: ["urn:li:tag:<TAG1>", "urn:li:tag:<TAG2>"],
    resources: [{ resourceUrn: "<URN1>" }, { resourceUrn: "<URN2>" }]
  })
}' --format json

# Batch remove tags
datahub graphql --query 'mutation {
  batchRemoveTags(input: {
    tagUrns: ["urn:li:tag:<TAG>"],
    resources: [{ resourceUrn: "<URN1>" }, { resourceUrn: "<URN2>" }]
  })
}' --format json

# Field-level tag (add subResourceType and subResource to the resource entry)
# Works with batchAddTags, batchRemoveTags, batchAddTerms, batchRemoveTerms
datahub graphql --query 'mutation {
  batchAddTags(input: {
    tagUrns: ["urn:li:tag:<TAG>"],
    resources: [{
      resourceUrn: "<ENTITY_URN>",
      subResourceType: DATASET_FIELD,
      subResource: "<FIELD_PATH>"
    }]
  })
}' --format json

# Mix entity-level and field-level in a single batch call
datahub graphql --query 'mutation {
  batchAddTags(input: {
    tagUrns: ["urn:li:tag:<TAG>"],
    resources: [
      { resourceUrn: "<ENTITY_URN>" },
      { resourceUrn: "<ENTITY_URN>", subResourceType: DATASET_FIELD, subResource: "customer_id" },
      { resourceUrn: "<ENTITY_URN>", subResourceType: DATASET_FIELD, subResource: "email" }
    ]
  })
}' --format json

# Create a tag (must exist before adding to entities)
datahub graphql --query 'mutation {
  createTag(input: { id: "pii", name: "PII", description: "Contains PII" })
}' --format json
```

---

## Glossary Terms

```bash
# Batch add terms (preferred)
datahub graphql --query 'mutation {
  batchAddTerms(input: {
    termUrns: ["urn:li:glossaryTerm:<TERM>"],
    resources: [{ resourceUrn: "<URN1>" }, { resourceUrn: "<URN2>" }]
  })
}' --format json

# Batch remove terms
datahub graphql --query 'mutation {
  batchRemoveTerms(input: {
    termUrns: ["urn:li:glossaryTerm:<TERM>"],
    resources: [{ resourceUrn: "<URN1>" }, { resourceUrn: "<URN2>" }]
  })
}' --format json

# Field-level term (same subResourceType pattern as tags)
datahub graphql --query 'mutation {
  batchAddTerms(input: {
    termUrns: ["urn:li:glossaryTerm:<TERM>"],
    resources: [{
      resourceUrn: "<ENTITY_URN>",
      subResourceType: DATASET_FIELD,
      subResource: "<FIELD_PATH>"
    }]
  })
}' --format json

# Create glossary term
datahub graphql --query 'mutation {
  createGlossaryTerm(input: { id: "Revenue", name: "Revenue", description: "Total revenue metric" })
}' --format json

# Create glossary group (node)
datahub graphql --query 'mutation {
  createGlossaryNode(input: { id: "Finance", name: "Finance", description: "Finance domain terms" })
}' --format json

# Move glossary term/group under a parent (null removes parent → root)
datahub graphql --query 'mutation {
  updateParentNode(input: {
    resourceUrn: "urn:li:glossaryTerm:<TERM>",
    parentNode: "urn:li:glossaryNode:<GROUP>"
  })
}' --format json
```

---

## Ownership

Owner types: `TECHNICAL_OWNER`, `BUSINESS_OWNER`, `DATA_STEWARD`, `NONE`

```bash
# Batch add owners (preferred — additive, does not replace)
datahub graphql --query 'mutation {
  batchAddOwners(input: {
    owners: [{ ownerUrn: "urn:li:corpuser:<USER>", ownerEntityType: CORP_USER }],
    resources: [{ resourceUrn: "<URN1>" }, { resourceUrn: "<URN2>" }]
  })
}' --format json

# Batch remove owners
datahub graphql --query 'mutation {
  batchRemoveOwners(input: {
    ownerUrns: ["urn:li:corpuser:<USER>"],
    resources: [{ resourceUrn: "<URN1>" }, { resourceUrn: "<URN2>" }]
  })
}' --format json
```

---

## Domains

```bash
# Batch set domain (preferred)
datahub graphql --query 'mutation {
  batchSetDomain(input: {
    domainUrn: "urn:li:domain:<ID>",
    resources: [{ resourceUrn: "<URN1>" }, { resourceUrn: "<URN2>" }]
  })
}' --format json

# Unset domain (single entity)
datahub graphql --query 'mutation {
  unsetDomain(entityUrn: "<URN>")
}' --format json

# Create domain (parentDomain is optional — omit for top-level)
datahub graphql --query 'mutation {
  createDomain(input: {
    name: "Campaigns",
    description: "Campaign analytics",
    parentDomain: "urn:li:domain:<PARENT_ID>"
  })
}' --format json

# Move domain under a parent (null removes parent → top-level)
datahub graphql --query 'mutation {
  moveDomain(input: {
    resourceUrn: "urn:li:domain:<CHILD_ID>",
    parentDomain: "urn:li:domain:<PARENT_ID>"
  })
}' --format json
```

---

## Descriptions

No batch mutation exists. Execute per entity sequentially.

```bash
# Entity description
datahub graphql --query 'mutation {
  updateDescription(input: {
    description: "<NEW_DESCRIPTION>",
    resourceUrn: "<ENTITY_URN>"
  })
}' --format json

# Field-level description
datahub graphql --query 'mutation {
  updateDescription(input: {
    description: "<FIELD_DESCRIPTION>",
    resourceUrn: "<ENTITY_URN>",
    subResourceType: DATASET_FIELD,
    subResource: "<FIELD_PATH>"
  })
}' --format json
```

Use `--variables` with a temp JSON file for dataset URNs (see URN Quoting above).

---

## Deprecation

```bash
# Batch deprecation (preferred)
datahub graphql --query 'mutation {
  batchUpdateDeprecation(input: {
    deprecated: true,
    note: "<REASON>",
    resources: [{ resourceUrn: "<URN1>" }, { resourceUrn: "<URN2>" }]
  })
}' --format json

# Un-deprecate
datahub graphql --query 'mutation {
  batchUpdateDeprecation(input: {
    deprecated: false,
    resources: [{ resourceUrn: "<URN>" }]
  })
}' --format json
```

---

## Data Products

```bash
# Create data product (domainUrn is REQUIRED)
datahub graphql --query 'mutation {
  createDataProduct(input: {
    domainUrn: "urn:li:domain:<ID>",
    properties: { name: "Revenue Analytics", description: "Revenue pipeline" }
  }) { urn }
}' --format json

# Batch assign entities to a data product
datahub graphql --query 'mutation {
  batchSetDataProduct(input: {
    dataProductUrn: "urn:li:dataProduct:<ID>",
    resourceUrns: ["<URN1>", "<URN2>"]
  })
}' --format json
```

---

## Structured Properties

```bash
# Upsert structured property values on an entity
datahub graphql --query 'mutation {
  upsertStructuredProperties(input: {
    assetUrn: "<ENTITY_URN>",
    structuredPropertyInputs: [{
      structuredPropertyUrn: "urn:li:structuredProperty:<PROP>",
      values: ["<VALUE>"]
    }]
  })
}' --format json

# Remove structured property values
datahub graphql --query 'mutation {
  removeStructuredProperties(input: {
    assetUrn: "<ENTITY_URN>",
    structuredPropertyUrns: ["urn:li:structuredProperty:<PROP>"]
  })
}' --format json
```

---

## Documents

```bash
# Create a document (parentDocument is optional — omit for root-level)
datahub graphql --query 'mutation {
  createDocument(input: {
    title: "Data Dictionary",
    contents: { text: "Document body in markdown" },
    relatedAssets: ["<ENTITY_URN_1>", "<ENTITY_URN_2>"],
    parentDocument: "<PARENT_DOC_URN>"
  })
}' --format json

# Update document contents
datahub graphql --query 'mutation {
  updateDocumentContents(input: {
    urn: "<DOC_URN>",
    title: "Updated Title",
    contents: { text: "Updated body" }
  })
}' --format json

# Link document to assets (replaces existing related asset list)
datahub graphql --query 'mutation {
  updateDocumentRelatedEntities(input: {
    urn: "<DOC_URN>",
    relatedAssets: ["<ENTITY_URN_1>", "<ENTITY_URN_2>"]
  })
}' --format json

# Move document (null/absent parentDocument → root)
datahub graphql --query 'mutation {
  moveDocument(input: {
    urn: "<DOC_URN>",
    parentDocument: "<NEW_PARENT_DOC_URN>"
  })
}' --format json
```

---

## Links (External Docs)

```bash
# Add link
datahub graphql --query 'mutation {
  addLink(input: {
    linkUrl: "https://docs.example.com/table-spec",
    label: "Table Specification",
    resourceUrn: "<ENTITY_URN>"
  })
}' --format json

# Remove link
datahub graphql --query 'mutation {
  removeLink(input: {
    linkUrl: "https://docs.example.com/table-spec",
    resourceUrn: "<ENTITY_URN>"
  })
}' --format json
```

---

## ID Strategy: Name-Based vs GUID-Based

When creating tags, glossary terms, or domains, you choose between two ID strategies:

**Name-based (pass `id`):** `createTag(input: { id: "pii", name: "PII" })` → `urn:li:tag:pii`. Human-readable, predictable, but the ID is immutable — can't rename later.

**GUID-based (omit `id`):** `createTag(input: { name: "PII" })` → `urn:li:tag:a1b2c3d4-...`. Display name can change freely, but URNs are opaque.

| Situation | Recommended |
| --- | --- |
| Industry-standard label (PII, deprecated) | Name-based |
| Name may evolve as org matures | GUID-based |
| User explicitly requests a specific ID | Name-based |
| Unsure | Ask the user |

---

## Discovering Available Mutations

Use `datahub graphql` introspection to discover mutations and their input shapes:

```bash
datahub graphql --list-mutations --format json
datahub graphql --describe batchAddTags --recurse --format json
datahub graphql --describe createDocument --recurse --format json
```
