# NoSQL Databases Sources

**Source Type:** API-Based (when using REST APIs)

## Overview

NoSQL databases like MongoDB, Cassandra, DynamoDB, Redis, and Elasticsearch can be accessed through REST APIs or native drivers.

## What to Extract

- **Datasets** - Collections (MongoDB), tables (Cassandra, DynamoDB), indexes (Elasticsearch)
- **Containers** - Databases, keyspaces (optional)
- **Schemas** - Inferred schemas when available (MongoDB, DynamoDB)
- **Indexes** - Secondary indexes and their configurations

## Required Aspects

| Aspect                 | Required              | Description                                              |
| ---------------------- | --------------------- | -------------------------------------------------------- |
| `dataPlatformInstance` | ✅ ALWAYS             | Links entity to data platform. **Always required.**      |
| `datasetProperties`    | ✅ ALWAYS             | Collection/table name, qualified name, custom properties |
| `schemaMetadata`       | ✅ IF SCHEMA INFERRED | Schema inferred from sampling or schema registry         |
| `subTypes`             | ✅ ALWAYS             | Identifies entity subtype (Collection, Table, Index)     |
| `container`            | ✅ IF HIERARCHICAL    | Links to parent container (database, keyspace)           |
| `containerProperties`  | ✅ FOR CONTAINERS     | Database/keyspace metadata                               |
| `globalTags`           | ✅ IF SOURCE PROVIDES | Tags from source system                                  |
| `browsePathsV2`        | 🔄 AUTO               | Auto-generated from `container` aspect                   |
| `status`               | 🔄 AUTO               | Auto-generated for all entities                          |

## Implementation Guide

→ **See [API-Based Sources Guide](../api.md)** for implementation details when using REST APIs

**Alternative**: Some NoSQL databases support SQL-like interfaces (e.g., MongoDB SQL connector, Cassandra CQL). In those cases, consider using the [SQL Sources Guide](../sql.md).

## Special Considerations

- **Schema Inference**: Most NoSQL databases are schema-less; may need to sample documents
- **Index Metadata**: Capture index definitions and performance characteristics
- **Sharding**: Handle sharded collections appropriately

## Example Sources in DataHub

- `src/datahub/ingestion/source/mongodb/`
- `src/datahub/ingestion/source/dynamodb/`
- `src/datahub/ingestion/source/elasticsearch.py`
