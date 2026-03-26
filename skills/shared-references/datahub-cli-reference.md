# DataHub CLI Reference

Commands verified against DataHub CLI v1.4.0. Install via `pip install acryl-datahub`.

---

## Tool Detection

Before running any DataHub commands, determine which tools are available:

1. **MCP tools available** — If tools like `datahub_search`, `datahub_get_entity`, `datahub_get_lineage` are in your tool list, use them directly. They are the preferred path — no CLI installation needed.
2. **CLI available** — If you have a `Bash` tool, check: `which datahub`. If found, use the CLI commands documented below.
3. **Neither** — Suggest the user set up a DataHub connection using `/datahub-setup`.

**MCP takes priority over CLI** when both are available — MCP tools are purpose-built for agent use with structured inputs/outputs and no shell overhead.

### CLI ↔ MCP Equivalents

| Operation | CLI Command | MCP Tool |
| --- | --- | --- |
| Search | `datahub search "query" --where "..."` | `search(query="...", filter="...")` |
| Get entity | `datahub get --urn "..." --aspect ownership` | `get_entities(urns=["..."])` |
| Upstream lineage | `datahub lineage --urn "..." --direction upstream` | `get_lineage(urn="...", upstream=true)` |
| Downstream lineage | `datahub lineage --urn "..." --direction downstream` | `get_lineage(urn="...", upstream=false)` |
| GraphQL | `datahub graphql --query '...'` | `execute_graphql(query="...")` |
| Server config | `datahub check server-config` | Not needed (MCP server handles config) |

MCP tool names may be prefixed (e.g. `mcp__datahub-cloud__search`). Match by the function name suffix, not the full prefixed name. MCP tools are self-documenting — check their schemas for parameter details rather than relying on static documentation.

The rest of this document covers the CLI path.

---

## Authentication

The CLI reads connection settings from `~/.datahubenv`:

```yaml
gms:
  server: "http://localhost:8080"
  token: "<personal-access-token>"
```

Or via environment variables:

```bash
export DATAHUB_GMS_URL="http://localhost:8080"
export DATAHUB_GMS_TOKEN="<token>"
```

---

## Version Check

Before running commands, check the installed CLI version:

```bash
datahub version
```

If a skill requires a minimum version and the installed version is older, upgrade:

```bash
pip install --upgrade acryl-datahub --pre
```

The `--pre` flag ensures pre-release versions (e.g. `1.5.0rc1`) are included, which may be required for newer features.

## Server Detection

Detect whether you're connected to DataHub Cloud or OSS:

```bash
datahub check server-config
```

- `serverEnv: 'cloud'` → DataHub Cloud (supports popularity sorting, dataset features)
- `serverEnv: 'core'` or other → OSS / self-hosted (feature fields not available)

Cache this result for the session — don't re-check on every command. Some features marked **(Cloud only)** below require `serverEnv: cloud`.

## Context

Pass context on CLI commands using `-C key=value` so commands can be correlated:

```bash
datahub -C skill=datahub-audit search "revenue"
datahub -C skill=datahub-audit -C caller=claude-code get --urn "..."
```

The `-C` flag goes on the root `datahub` command (before the subcommand). Use the skill's own name from its YAML frontmatter as the `skill` value. If the flag is not recognized, omit it — the command works the same without it.

---

## Search & Discovery

The search CLI uses a positional query argument — not `--query`.

```bash
# Basic keyword search
datahub search "revenue"

# Search with limit
datahub search "customers" --limit 20

# Filter by platform (simple filter)
datahub search "*" --filter platform=snowflake

# Filter by entity type
datahub search "*" --where "entity_type = dataset"

# SQL-like WHERE expressions (recommended for agents)
datahub search "*" --where "platform = snowflake AND env = PROD"
datahub search "*" --where "platform IN (snowflake, bigquery)"
datahub search "*" --where "entity_type = dataset AND platform = snowflake"

# Multiple simple filters (AND between fields, comma = OR within field)
datahub search "*" --filter platform=snowflake --filter env=PROD
datahub search "*" --filter platform=snowflake,bigquery

# Output formats
datahub search "revenue" --table          # Human-readable table
datahub search "revenue" --urns-only      # URNs only, one per line
datahub search "revenue" --format json    # JSON (default)

# Pagination (max 50 per page)
datahub search "customers" --limit 50 --offset 0     # page 1
datahub search "customers" --limit 50 --offset 50    # page 2

# Facets only (counts by type/platform/etc.)
datahub search "*" --facets-only --format json

# Dry run (preview query without executing)
datahub search "revenue" --where "platform = snowflake" --dry-run

# Projection (limit returned fields — reduces token cost)
datahub search "customers" --projection "urn type"

# Column-level search (find datasets containing a specific field)
datahub search "*" --where "entity_type = dataset AND fieldPaths = customer_id"

# Sorting
datahub search "*" --sort-by lastModifiedAt --sort-order desc --limit 10
datahub search "*" --sort-by _entityName --sort-order asc --limit 10

# Popularity / usage sorting (Cloud only — check serverEnv first)
# Most queried datasets
datahub search "*" --where "entity_type = dataset" \
  --sort-by queryCountLast30DaysFeature --sort-order desc --limit 10 \
  --projection "urn type ... on Dataset { properties { name } platform { name } statsSummary { queryCountLast30Days uniqueUserCountLast30Days } }"

# Most updated datasets
datahub search "*" --where "entity_type = dataset" --sort-by writeCountLast30DaysFeature --sort-order desc --limit 10

# Largest tables (by row count or bytes)
datahub search "*" --where "entity_type = dataset" --sort-by rowCountFeature --sort-order desc --limit 10
datahub search "*" --where "entity_type = dataset" --sort-by sizeInBytesFeature --sort-order desc --limit 10

# Existence filters (IS NULL / IS NOT NULL)
datahub search "*" --where "entity_type = dataset AND description IS NULL AND editableDescription IS NULL"
datahub search "*" --where "entity_type = dataset AND glossary_term IS NOT NULL"

# Sibling-aware description audit (single query, no N+1 fetches)
# Step 1: Find datasets missing both ingestion and user-edited descriptions
# Step 2: Project siblings with their descriptions to compute effective coverage
datahub search "*" \
  --where "entity_type = dataset AND platform = snowflake AND description IS NULL AND editableDescription IS NULL" \
  --projection "urn type ... on Dataset { siblings { isPrimary siblings { urn ... on Dataset { properties { name description } editableProperties { description } } } } }" \
  --format json --limit 50

# URN resolution for filters
# Tag, domain, and glossary_term filters require full URNs — not display names.
# Always resolve the name to a URN first, then use the URN in the filter.

# Step 1: Find tag URN by name
datahub search "large table" --where "entity_type = tag" --urns-only --limit 1
# → urn:li:tag:sample_data___default_large_table

# Step 2: Use the URN in a filter
datahub search "*" --where "entity_type = dataset AND tags = 'urn:li:tag:sample_data___default_large_table'"

# Same pattern for domains:
datahub search "ecommerce" --where "entity_type = domain" --urns-only --limit 1
# → urn:li:domain:91994180-...
datahub search "*" --where "entity_type = dataset AND domain = 'urn:li:domain:91994180-...'"

# And glossary terms:
datahub search "PII" --where "entity_type = glossaryTerm" --urns-only --limit 1
datahub search "*" --where "entity_type = dataset AND glossary_term = 'urn:li:glossaryTerm:...'"

# Discover available filters
datahub search list-filters
datahub search describe-filter platform

# Agent best practices
datahub search --agent-context
```

## Entity Retrieval

```bash
# Get full entity metadata
datahub get --urn "urn:li:dataset:(urn:li:dataPlatform:hive,table_name,PROD)"

# Get specific aspect
datahub get --urn "<URN>" --aspect schemaMetadata
datahub get --urn "<URN>" --aspect ownership
datahub get --urn "<URN>" --aspect globalTags
```

## Lineage

```bash
# Upstream sources (full graph by default)
datahub lineage --urn "<URN>" --direction upstream

# Downstream dependents
datahub lineage --urn "<URN>" --direction downstream

# Limit to immediate neighbors
datahub lineage --urn "<URN>" --direction upstream --hops 1

# Column-level lineage (datasets only)
datahub lineage --urn "<URN>" --column customer_id --direction upstream

# JSON output (includes metadata with capped/hint info)
datahub lineage --urn "<URN>" --direction downstream --format json

# Find path between two entities
datahub lineage path --from "<URN_A>" --to "<URN_B>"

# Agent best practices
datahub lineage --agent-context
```

## Timeline (Change History)

```bash
# Schema changes
datahub timeline --urn "<URN>" --category technical_schema

# Ownership changes
datahub timeline --urn "<URN>" --category owner

# Tag changes
datahub timeline --urn "<URN>" --category tag

# With time range
datahub timeline --urn "<URN>" --category technical_schema --start 7daysago
```

Categories: `tag`, `glossary_term`, `technical_schema`, `documentation`, `owner`

---

## Write Operations (via GraphQL Mutations)

Write operations use `datahub graphql --query 'mutation { ... }'`. The CLI does not have dedicated `tag`, `glossary`, or inline `put` commands for these operations.

**Important rules for GraphQL mutations:**

- **Return field subselections required.** Mutations returning objects (not scalars like `Boolean`) need `{ urn }` or similar after the mutation. Without it: `SubselectionRequired` error.
- **Long queries must use temp files.** Long inline `--query` strings get misinterpreted as file paths on macOS (`File name too long`). Write to a `.graphql` file and pass the path: `datahub graphql --query /tmp/my-mutation.graphql --format json`.
- **Short mutations can be inline.** Simple mutations like `addTag`, `removeTag`, `addOwner` are short enough to pass inline.

### Tags

```bash
# Create a tag
# With id: name-based URN (human-readable, but ID is immutable — can't rename later)
# Without id: GUID-based URN (opaque, but display name can change freely)
# When unsure, ask the user which they prefer.
datahub graphql --query 'mutation {
  createTag(input: { id: "pii", name: "PII", description: "Contains PII data" })
}' --format json
# → returns urn:li:tag:pii

# Add tag to entity (tag must exist first)
datahub graphql --query 'mutation {
  addTag(input: { tagUrn: "urn:li:tag:<TAG_URN>", resourceUrn: "<ENTITY_URN>" })
}' --format json

# Add tag to a specific field
datahub graphql --query 'mutation {
  addTag(input: {
    tagUrn: "urn:li:tag:<TAG_URN>",
    resourceUrn: "<ENTITY_URN>",
    subResourceType: DATASET_FIELD,
    subResource: "<FIELD_PATH>"
  })
}' --format json

# Remove tag
datahub graphql --query 'mutation {
  removeTag(input: { tagUrn: "urn:li:tag:<TAG_URN>", resourceUrn: "<ENTITY_URN>" })
}' --format json

# Batch add tags
datahub graphql --query 'mutation {
  batchAddTags(input: {
    tagUrns: ["urn:li:tag:<TAG1>", "urn:li:tag:<TAG2>"],
    resources: [{ resourceUrn: "<URN1>" }, { resourceUrn: "<URN2>" }]
  })
}' --format json
```

### Glossary Terms

```bash
# Add term to entity
datahub graphql --query 'mutation {
  addTerm(input: { termUrn: "urn:li:glossaryTerm:<TERM>", resourceUrn: "<ENTITY_URN>" })
}' --format json

# Remove term
datahub graphql --query 'mutation {
  removeTerm(input: { termUrn: "urn:li:glossaryTerm:<TERM>", resourceUrn: "<ENTITY_URN>" })
}' --format json
```

### Ownership

```bash
# Add owner (appends — does not replace existing owners)
datahub graphql --query 'mutation {
  addOwner(input: {
    ownerUrn: "urn:li:corpuser:<USER>",
    resourceUrn: "<ENTITY_URN>",
    ownerEntityType: CORP_USER,
    type: TECHNICAL_OWNER
  })
}' --format json

# Remove owner
datahub graphql --query 'mutation {
  removeOwner(input: { ownerUrn: "urn:li:corpuser:<USER>", resourceUrn: "<ENTITY_URN>" })
}' --format json

# Batch add owners
datahub graphql --query 'mutation {
  batchAddOwners(input: {
    owners: [{ ownerUrn: "urn:li:corpuser:<USER>", ownerEntityType: CORP_USER }],
    resources: [{ resourceUrn: "<URN1>" }, { resourceUrn: "<URN2>" }]
  })
}' --format json
```

Owner types: `TECHNICAL_OWNER`, `BUSINESS_OWNER`, `DATA_STEWARD`, `NONE`

### Deprecation

```bash
# Deprecate
datahub graphql --query 'mutation {
  updateDeprecation(input: { urn: "<URN>", deprecated: true, note: "Replaced by new_table" })
}' --format json

# Un-deprecate
datahub graphql --query 'mutation {
  updateDeprecation(input: { urn: "<URN>", deprecated: false })
}' --format json
```

### Domains

```bash
# Create domain
datahub graphql --query 'mutation {
  createDomain(input: { name: "Marketing", description: "Marketing data" })
}' --format json

# Assign entity to domain (domain must exist)
datahub graphql --query 'mutation {
  setDomain(entityUrn: "<ENTITY_URN>", domainUrn: "urn:li:domain:<DOMAIN_ID>")
}' --format json

# Remove from domain
datahub graphql --query 'mutation {
  unsetDomain(entityUrn: "<ENTITY_URN>")
}' --format json

# Batch assign
datahub graphql --query 'mutation {
  batchSetDomain(input: {
    domainUrn: "urn:li:domain:<ID>",
    resources: [{ resourceUrn: "<URN1>" }, { resourceUrn: "<URN2>" }]
  })
}' --format json
```

### Description

```bash
datahub graphql --query 'mutation {
  updateDescription(input: {
    description: "New description text",
    resourceUrn: "<ENTITY_URN>"
  })
}' --format json
```

### Data Products

**Note:** `domainUrn` is required — every data product must belong to a domain. Use `datahub graphql --describe createDataProduct --recurse` to verify the schema.

```bash
# Create (domainUrn is REQUIRED)
datahub graphql --query 'mutation {
  createDataProduct(input: {
    domainUrn: "urn:li:domain:<DOMAIN_ID>",
    properties: { name: "Revenue Analytics", description: "Revenue pipeline" }
  }) { urn }
}' --format json

# Add assets to data product
datahub graphql --query 'mutation {
  batchSetDataProduct(input: {
    dataProductUrn: "urn:li:dataProduct:<ID>",
    resourceUrns: ["<URN1>", "<URN2>"]
  })
}' --format json
```

---

## Verification & Health

```bash
# Check CLI version
datahub version

# Verify connectivity (this entity always exists)
datahub get --urn "urn:li:corpuser:datahub"

# Test search (confirms search index works)
datahub search "*" --limit 1

# Server configuration
datahub check server-config
```

**Note:** `datahub check server-health` does not exist. Use `datahub get --urn "urn:li:corpuser:datahub"` to verify connectivity.

---

## GraphQL Discovery

```bash
# List all available operations
datahub graphql --list-operations --format json

# List mutations only
datahub graphql --list-mutations --format json

# Describe a specific operation
datahub graphql --describe addTag --format json

# Describe with full type expansion
datahub graphql --describe addTag --recurse --format json

# Dry run (preview without executing)
datahub graphql --query '{ me { corpUser { urn } } }' --dry-run

# Agent best practices
datahub graphql --agent-context
```

---

## Batch Mutation Pattern (Python)

Shell loops with dataset URNs are fragile due to quoting issues with parentheses. For multi-entity mutations, use a Python script with temp files:

```python
import subprocess, json, tempfile, os

def run_graphql_mutation(query, variables):
    """Run a GraphQL mutation with variables via temp file. Returns parsed JSON or None."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(variables, f)
        vf = f.name
    try:
        result = subprocess.run(
            ["datahub", "graphql", "-q", query, "-v", vf, "--format", "json", "--no-pretty"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            print(f"ERROR: {result.stderr.strip()[:120]}")
            return None
    finally:
        os.unlink(vf)

# Example: batch update descriptions
query = "mutation updateDataset($urn: String!, $input: DatasetUpdateInput!) { updateDataset(urn: $urn, input: $input) { urn } }"

datasets = {
    "urn:li:dataset:(urn:li:dataPlatform:snowflake,db.schema.table1,PROD)": "Description for table1",
    "urn:li:dataset:(urn:li:dataPlatform:snowflake,db.schema.table2,PROD)": "Description for table2",
}

for urn, desc in datasets.items():
    variables = {"urn": urn, "input": {"editableProperties": {"description": desc}}}
    result = run_graphql_mutation(query, variables)
    status = "OK" if result else "FAIL"
    print(f"  {urn.split(',')[1]}: {status}")
```

---

## Output Processing

```bash
# Pipe search URNs to get for batch retrieval
datahub search "customers" --urns-only | xargs -I{} datahub get --urn {}

# Extract field names from schema
datahub get --urn "<URN>" --aspect schemaMetadata | python3 -c "
import sys, json
data = json.load(sys.stdin)
for f in data.get('schemaMetadata', {}).get('fields', []):
    print(f['fieldPath'])
"
```
