# SQL Databases Sources

**Source Type:** SQL-Based

## Overview

Traditional SQL databases like PostgreSQL, MySQL, Oracle, SQL Server, and DB2 expose metadata through INFORMATION_SCHEMA or system catalogs.

## What to Extract

- **Datasets** - Tables, views
- **Containers** - Databases, schemas
- **Column Metadata** - Column names, types, comments, nullability
- **Constraints** - Primary keys, foreign keys, unique constraints
- **Indexes** - Index definitions
- **Users** - Table owners (when available)
- **Lineage** - Extract from view definitions

## Required Aspects

| Aspect                 | Required                | Description                                         |
| ---------------------- | ----------------------- | --------------------------------------------------- |
| `dataPlatformInstance` | ✅ ALWAYS               | Links entity to data platform. **Always required.** |
| `containerProperties`  | ✅ ALWAYS               | For databases/schemas as containers                 |
| `subTypes`             | ✅ ALWAYS               | Identifies entity subtype (Table, View)             |
| `container`            | ✅ ALWAYS               | Links datasets to parent containers                 |
| `datasetProperties`    | ✅ ALWAYS               | Dataset name, qualified name, custom properties     |
| `schemaMetadata`       | ✅ ALWAYS               | Column definitions with types, constraints          |
| `viewProperties`       | ✅ IF VIEW              | View definition SQL (required for all views)        |
| `upstreamLineage`      | ✅ IF LINEAGE ENABLED   | Upstream table dependencies from view SQL           |
| `ownership`            | ✅ IF SOURCE PROVIDES   | Table owners (if available in system catalog)       |
| `datasetProfile`       | ✅ IF PROFILING ENABLED | Row counts, column stats                            |
| `browsePathsV2`        | 🔄 AUTO                 | Auto-generated from `container` aspect              |
| `status`               | 🔄 AUTO                 | Auto-generated for all entities                     |

## Implementation Guide

→ **See [SQL Sources Guide](../sql.md)** for implementation details

## Special Considerations

- **Dialect Differences**: Each database has unique system catalogs
- **Foreign Keys**: Can be used to infer basic lineage relationships
- **Performance**: Large databases may require filtering by schema/database

## Example Sources in DataHub

- `src/datahub/ingestion/source/postgres/`
- `src/datahub/ingestion/source/mysql/`
- `src/datahub/ingestion/source/mssql/`
- `src/datahub/ingestion/source/oracle/`
