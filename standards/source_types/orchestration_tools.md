# Orchestration Tools Sources

**Source Type:** API-Based

## Overview

Orchestration tools like Airflow, Prefect, and Dagster expose pipeline and task metadata through REST/GraphQL APIs.

## What to Extract

- **DataFlow** - DAGs and pipelines
- **DataJob** - Individual tasks within pipelines
- **Datasets** - Input/output datasets referenced by tasks
- **Tags** - DAG and task tags
- **Users** - Pipeline owners
- **Lineage** - Task → Dataset relationships, extract from SQL operators

## Required Aspects

| Aspect                 | Required              | Description                                                  |
| ---------------------- | --------------------- | ------------------------------------------------------------ |
| `dataPlatformInstance` | ✅ ALWAYS             | Links entity to data platform. **Always required.**          |
| `dataFlowInfo`         | ✅ ALWAYS             | Pipeline/DAG metadata (name, description, URL)               |
| `dataJobInfo`          | ✅ ALWAYS             | Task metadata (name, type, description)                      |
| `dataJobInputOutput`   | ✅ ALWAYS             | Task input/output relationships (datasets and upstream jobs) |
| `ownership`            | ✅ IF SOURCE PROVIDES | Pipeline/task owners (required if source exposes owners)     |
| `globalTags`           | ✅ IF SOURCE PROVIDES | Tags from source system (required if source has tags)        |
| `status`               | 🔄 AUTO               | Auto-generated for all entities                              |

## Implementation Guide

→ **See [API-Based Sources Guide](../api.md)** for implementation details

## Lineage Considerations

Many orchestration tasks execute SQL queries. See [Lineage Extraction Guide](../lineage.md) for SQL parsing patterns.

## Special Considerations

- **Task Dependencies**: Capture upstream/downstream task relationships via `dataJobInputOutput.inputDatajobs`
- **Dataset Lineage**: Capture input/output datasets via `dataJobInputOutput.inputDatasets` and `outputDatasets`
- **Execution History**: Optionally track run history and statistics
- **SQL Operators**: Parse SQL from operators for dataset lineage

## Example Sources in DataHub

- `src/datahub/ingestion/source/airflow/`
- `src/datahub/ingestion/source/dagster/`
