# Data Lakes Sources

**Source Type:** API-Based

## Overview

Data Lakes like AWS S3, Google Cloud Storage (GCS), and Azure Data Lake Storage (ADLS) expose object metadata through cloud provider APIs.

## What to Extract

- **Datasets** - Files, objects, and directories
- **Tags** - Object metadata tags (S3 tags, GCS labels, ADLS metadata)
- **Containers** - Buckets, containers, storage accounts (optional organizational structure)

## Required Aspects

| Aspect                 | Required              | Description                                                     |
| ---------------------- | --------------------- | --------------------------------------------------------------- |
| `dataPlatformInstance` | ✅ ALWAYS             | Links entity to data platform. **Always required.**             |
| `datasetProperties`    | ✅ ALWAYS             | File/object name, path, custom properties (size, modified time) |
| `schemaMetadata`       | ✅ IF SCHEMA INFERRED | Schema from file format (Parquet, Avro, CSV)                    |
| `subTypes`             | ✅ ALWAYS             | Identifies entity subtype (File, Directory, Table)              |
| `container`            | ✅ IF HIERARCHICAL    | Links to parent container (bucket, folder)                      |
| `containerProperties`  | ✅ FOR CONTAINERS     | Bucket/folder metadata                                          |
| `globalTags`           | ✅ IF SOURCE PROVIDES | S3 tags, GCS labels, ADLS metadata                              |
| `browsePathsV2`        | 🔄 AUTO               | Auto-generated from `container` aspect                          |
| `status`               | 🔄 AUTO               | Auto-generated for all entities                                 |

## Implementation Guide

→ **See [API-Based Sources Guide](../api.md)** for implementation details

## Special Considerations

- **Schema Inference**: May need to infer schemas from file formats (Parquet, Avro, CSV)
- **Partitioning**: Handle partitioned datasets appropriately - emit as single dataset with partition info in properties
- **Large-scale**: Implement efficient listing and pagination for large buckets

## Example Sources in DataHub

- `src/datahub/ingestion/source/s3/`
- `src/datahub/ingestion/source/gcs/`
- `src/datahub/ingestion/source/azure/adls_gen2.py`
