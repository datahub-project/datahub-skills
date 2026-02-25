# Streaming Platforms Sources

**Source Type:** API-Based

## Overview

Streaming platforms like Kafka, Kinesis, and Pulsar expose topic and schema metadata through REST APIs or admin clients.

## What to Extract

- **Datasets** - Topics and streams (with schema metadata when available)
- **Schemas** - Avro/Protobuf/JSON schemas from Schema Registry
- **Domains** - Logical groupings of topics
- **DataFlow/DataJob** - Stream processing pipelines (Kafka Connect, KSQL)
- **Lineage** - Topic → Topic transformations in stream processors

## Required Aspects for Topics (Datasets)

| Aspect                 | Required               | Description                                                             |
| ---------------------- | ---------------------- | ----------------------------------------------------------------------- |
| `dataPlatformInstance` | ✅ ALWAYS              | Links entity to data platform. **Always required.**                     |
| `datasetProperties`    | ✅ ALWAYS              | Topic name, qualified name, custom properties (partitions, replication) |
| `schemaMetadata`       | ✅ IF SCHEMA AVAILABLE | Schema from Schema Registry (Avro, Protobuf, JSON Schema)               |
| `subTypes`             | ✅ ALWAYS              | Identifies entity subtype (Topic, Stream)                               |
| `container`            | ✅ IF HIERARCHICAL     | Links to parent container (cluster, namespace)                          |
| `globalTags`           | ✅ IF SOURCE PROVIDES  | Tags from source system                                                 |
| `browsePathsV2`        | 🔄 AUTO                | Auto-generated from `container` aspect                                  |
| `status`               | 🔄 AUTO                | Auto-generated for all entities                                         |

## Required Aspects for Stream Processing (DataFlow/DataJob)

| Aspect                 | Required  | Description                                           |
| ---------------------- | --------- | ----------------------------------------------------- |
| `dataPlatformInstance` | ✅ ALWAYS | Links entity to data platform. **Always required.**   |
| `dataFlowInfo`         | ✅ ALWAYS | Pipeline metadata (Kafka Connect connector, KSQL app) |
| `dataJobInfo`          | ✅ ALWAYS | Job/task metadata                                     |
| `dataJobInputOutput`   | ✅ ALWAYS | Input/output topic relationships                      |
| `status`               | 🔄 AUTO   | Auto-generated for all entities                       |

## Implementation Guide

→ **See [API-Based Sources Guide](../api.md)** for implementation details

## Special Considerations

- **Schema Registry**: Integrate with Confluent Schema Registry or AWS Glue
- **Partitioning**: Capture topic partition information in `datasetProperties.customProperties`
- **Stream Processing**: Extract lineage from Kafka Connect, KSQL, Flink

## Example Sources in DataHub

- `src/datahub/ingestion/source/kafka/`
- `src/datahub/ingestion/source/kafka_connect/`
- `src/datahub/ingestion/source/pulsar/`
