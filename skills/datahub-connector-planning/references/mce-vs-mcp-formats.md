# MCE vs MCP Output Formats

DataHub connectors emit metadata in two formats. Understanding the difference
is critical for validating extraction output.

## Overview

| Format  | Full Name                | Use Case                                |
| ------- | ------------------------ | --------------------------------------- |
| **MCE** | Metadata Change Event    | Bundled snapshots with multiple aspects |
| **MCP** | Metadata Change Proposal | Individual aspect updates               |

## MCE Format (proposedSnapshot)

Used by most SQL connectors for bundled snapshots containing multiple aspects.

### Structure

```json
{
  "proposedSnapshot": {
    "com.linkedin.pegasus2avro.metadata.snapshot.DatasetSnapshot": {
      "urn": "urn:li:dataset:(urn:li:dataPlatform:duckdb,db.schema.table,PROD)",
      "aspects": [
        {"com.linkedin.pegasus2avro.schema.SchemaMetadata": {...}},
        {"com.linkedin.pegasus2avro.dataset.DatasetProperties": {...}}
      ]
    }
  }
}
```

### Characteristics

- Entity URN and all aspects bundled together
- Aspect types use full Java package names
- Aspects are in an array, not keyed by name
- Common for SQL connectors using `SQLAlchemySource` base classes

### Querying MCE Format

```bash
# Count datasets
jq '[.[] | select(.proposedSnapshot."com.linkedin.pegasus2avro.metadata.snapshot.DatasetSnapshot")] | length' output.json

# Extract schema metadata
jq '[.[] | .proposedSnapshot."com.linkedin.pegasus2avro.metadata.snapshot.DatasetSnapshot".aspects[]? | select(."com.linkedin.pegasus2avro.schema.SchemaMetadata")]' output.json
```

## MCP Format (aspectName)

Used for individual aspect updates, common for lineage and profiles.

### Structure

```json
{
  "entityType": "dataset",
  "entityUrn": "urn:li:dataset:(urn:li:dataPlatform:duckdb,db.schema.table,PROD)",
  "aspectName": "schemaMetadata",
  "aspect": {
    "fields": [...],
    "platform": "urn:li:dataPlatform:duckdb"
  }
}
```

### Characteristics

- Single aspect per record
- Aspect name in camelCase
- Entity URN separate from aspect
- Common for lineage, profiles, and API-based connectors

### Querying MCP Format

```bash
# Count schema metadata
jq '[.[] | select(.aspectName=="schemaMetadata")] | length' output.json

# Count lineage
jq '[.[] | select(.aspectName=="upstreamLineage")] | length' output.json
```

## Common Mistake

**Searching only for MCP format and concluding data is missing!**

```bash
# This may return 0 even when data exists in MCE format!
jq '[.[] | select(.aspectName=="schemaMetadata")] | length' output.json
# Result: 0

# But the data is actually here in MCE format:
jq '[.[] | .proposedSnapshot."com.linkedin.pegasus2avro.metadata.snapshot.DatasetSnapshot".aspects[]? | select(."com.linkedin.pegasus2avro.schema.SchemaMetadata")] | length' output.json
# Result: 3
```

## Validation Strategy

**Always check both formats:**

```bash
# Check MCP format
MCP_COUNT=$(jq '[.[] | select(.aspectName=="schemaMetadata")] | length' output.json)

# Check MCE format
MCE_COUNT=$(jq '[.[] | .proposedSnapshot // {} | .. | objects | select(."com.linkedin.pegasus2avro.schema.SchemaMetadata")] | length' output.json 2>/dev/null || echo 0)

TOTAL=$((MCP_COUNT + MCE_COUNT))
echo "Schema metadata count: $TOTAL (MCP: $MCP_COUNT, MCE: $MCE_COUNT)"
```

Or use the `analyze-output.py` script which handles both formats automatically.

## Which Format to Expect

| Connector Type         | Typical Format | Reason                         |
| ---------------------- | -------------- | ------------------------------ |
| SQL (SQLAlchemy-based) | MCE            | Base class emits snapshots     |
| API connectors         | MCP            | Individual aspect writes       |
| Lineage                | MCP            | Separate from entity creation  |
| Profiles               | MCP            | Added after initial extraction |
| Containers             | Either         | Depends on implementation      |

## See Also

- [Testing Patterns](./testing-patterns.md) - Golden file validation
- [Capability Mapping](./capability-mapping.md) - What outputs to expect
