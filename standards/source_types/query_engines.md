# Query Engines Sources

**Source Type:** SQL-Based (with API options)

## Overview

Query engines like Dremio, Trino, Presto, Hive, and Spark SQL provide SQL interfaces over distributed data. They typically expose metadata through INFORMATION_SCHEMA or system tables.

## What to Extract

- **Datasets** - Tables, views, and virtual datasets
- **Containers** - Spaces, catalogs, schemas
- **Column Metadata** - Column names, types, comments
- **Users** - Dataset owners
- **Groups** - Access control groups
- **Domains** - Logical data domains
- **Lineage** - Extract from view definitions and query logs

## Required Aspects

| Aspect                 | Required              | Description                                              |
| ---------------------- | --------------------- | -------------------------------------------------------- |
| `dataPlatformInstance` | ✅ ALWAYS             | Links entity to data platform. **Always required.**      |
| `containerProperties`  | ✅ ALWAYS             | For catalogs/spaces/schemas as containers                |
| `subTypes`             | ✅ ALWAYS             | Identifies entity subtype (Table, View, Virtual Dataset) |
| `container`            | ✅ ALWAYS             | Links datasets to parent containers                      |
| `datasetProperties`    | ✅ ALWAYS             | Dataset name, qualified name, custom properties          |
| `schemaMetadata`       | ✅ ALWAYS             | Column definitions with types                            |
| `viewProperties`       | ✅ IF VIEW            | View/virtual dataset definition SQL                      |
| `upstreamLineage`      | ✅ IF LINEAGE ENABLED | Upstream dependencies from view SQL                      |
| `ownership`            | ✅ IF SOURCE PROVIDES | Dataset owners                                           |
| `globalTags`           | ✅ IF SOURCE PROVIDES | Tags from source system                                  |
| `browsePathsV2`        | 🔄 AUTO               | Auto-generated from `container` aspect                   |
| `status`               | 🔄 AUTO               | Auto-generated for all entities                          |

## Implementation Guide

→ **See [SQL Sources Guide](../sql.md)** for implementation details

**Alternative**: Some query engines have rich REST APIs (e.g., Dremio). Consider [API-Based Sources Guide](../api.md) if the API provides better metadata access.

## Lineage Considerations

Query engines often provide excellent lineage through view definitions. See [Lineage Extraction Guide](../lineage.md) for SQL parsing patterns.

## Special Considerations

- **Federated Queries**: Handle references to external data sources
- **Virtual Datasets**: Distinguish between physical tables and virtual views
- **Catalog Structure**: May have multi-level hierarchies (catalog → schema → table)

## Example Sources in DataHub

- `src/datahub/ingestion/source/dremio/`
- `src/datahub/ingestion/source/trino/`
- `src/datahub/ingestion/source/presto/`
- `src/datahub/ingestion/source/hive/`
