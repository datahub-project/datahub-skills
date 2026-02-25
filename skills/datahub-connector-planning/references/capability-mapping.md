# Capability to Feature Mapping

This guide maps user-requested features to DataHub `@capability` decorators
and expected outputs.

## Feature to Capability Mapping

| User Feature       | Capability Decorator | Expected Output                               |
| ------------------ | -------------------- | --------------------------------------------- |
| Basic metadata     | (implicit)           | `schemaMetadata`, `datasetProperties` aspects |
| Tables & Views     | `SCHEMA_METADATA`    | `schemaMetadata` with fields                  |
| Containers         | `CONTAINERS`         | Container entities with hierarchy             |
| Table lineage      | `LINEAGE_COARSE`     | `upstreamLineage` aspects                     |
| Column lineage     | `LINEAGE_FINE`       | `fineGrainedLineages` in lineage aspects      |
| Usage statistics   | `USAGE_STATS`        | `datasetUsageStatistics` aspects              |
| Data profiling     | `DATA_PROFILING`     | `datasetProfile` aspects                      |
| Platform instance  | `PLATFORM_INSTANCE`  | URNs include platform instance                |
| Domains            | `DOMAINS`            | Domain associations in metadata               |
| Deletion detection | `DELETION_DETECTION` | Soft deletes for removed entities             |

## Capability Details

### SCHEMA_METADATA

**What it provides:** Table and view schemas with column information.

**Expected output:**

- `schemaMetadata` aspect for each table/view
- Contains: fields array, platform, schema name
- Format: Usually MCE (in proposedSnapshot)

**Validation:**

```bash
# MCE format
jq '[.[] | .proposedSnapshot // {} | .. | objects | select(."com.linkedin.pegasus2avro.schema.SchemaMetadata")] | length' output.json
```

### CONTAINERS

**What it provides:** Database and schema containers with hierarchy.

**Expected output:**

- Container entities (entityType: "container")
- `containerProperties` aspect
- `container` aspect linking children to parents

**Validation:**

```bash
jq '[.[] | select(.entityType=="container")] | length' output.json
```

### LINEAGE_COARSE

**What it provides:** Table-level lineage (view → upstream tables).

**Expected output:**

- `upstreamLineage` aspect
- Contains: upstream dataset URNs

**Validation:**

```bash
jq '[.[] | select(.aspectName=="upstreamLineage")] | length' output.json
```

### LINEAGE_FINE

**What it provides:** Column-level lineage with transformations.

**Expected output:**

- `fineGrainedLineages` array in upstreamLineage
- Contains: downstream fields, upstream fields, transform type

**Validation:**

```bash
jq '[.[] | select(.aspectName=="upstreamLineage") | .aspect.fineGrainedLineages // []] | flatten | length' output.json
```

### DATA_PROFILING

**What it provides:** Table statistics and column profiles.

**Expected output:**

- `datasetProfile` aspect
- Contains: rowCount, columnCount, column statistics

**Validation:**

```bash
jq '[.[] | select(.aspectName=="datasetProfile")] | length' output.json
```

### USAGE_STATS

**What it provides:** Query frequency and user access patterns.

**Expected output:**

- `datasetUsageStatistics` aspect
- Contains: query counts, user counts, timestamps

**Note:** Often requires query log access, not available for all sources.

## Configuration-Only Capabilities

These capabilities are framework features that don't produce specific aspects:

| Capability           | Purpose                                      | Validation                           |
| -------------------- | -------------------------------------------- | ------------------------------------ |
| `PLATFORM_INSTANCE`  | Supports multiple instances of same platform | Check URNs contain platform instance |
| `DOMAINS`            | Supports domain assignment                   | Config has domain field              |
| `DELETION_DETECTION` | Detects removed entities                     | Config has stateful ingestion        |

## Common Validation Mistakes

### Mistake 1: Expecting MCP when data is MCE

```bash
# Returns 0 even when data exists
jq '[.[] | select(.aspectName=="schemaMetadata")] | length' output.json

# Check MCE format instead
jq '[.[] | .proposedSnapshot // {} | .. | objects | select(."com.linkedin.pegasus2avro.schema.SchemaMetadata")] | length' output.json
```

### Mistake 2: Declaring capability without implementation

```python
# ❌ BAD - Declares lineage but doesn't implement it
@capability(SourceCapability.LINEAGE_COARSE, "Supports lineage")
class MySource(SQLAlchemySource):
    pass  # Base class doesn't do lineage for this source!

# ✅ GOOD - Only declare what you implement
@capability(SourceCapability.SCHEMA_METADATA, "Extracts schemas")
@capability(SourceCapability.CONTAINERS, "Creates containers")
class MySource(SQLAlchemySource):
    pass  # These are actually provided by base class
```

### Mistake 3: Missing dialect support

Lineage requires `get_view_definition()` to work. If the dialect returns None,
you must implement custom view definition retrieval.

## Capability Checklist

Before declaring a capability, verify:

- [ ] The feature actually produces output for your source
- [ ] You have test data that exercises the feature
- [ ] Golden files contain expected aspects
- [ ] Capability validation passes (`check-capabilities.sh`)

## See Also

- [MCE vs MCP Formats](./mce-vs-mcp-formats.md) - Understanding output formats
- [Testing Patterns](./testing-patterns.md) - Validating capabilities
