# BI Tools Sources

**Source Type:** API-Based

## Overview

BI Tools like Tableau, Looker, Power BI, Qlik, Metabase, and Superset expose metadata through REST or GraphQL APIs.

## What to Extract

- **Dashboards** - Main BI dashboard entities
- **Charts** - Individual visualizations within dashboards
- **Datasets** - Data sources referenced by dashboards/charts (for lineage)
- **Containers** - Workspaces, projects, folders (organizational hierarchy)
- **Users** - Dashboard/chart owners and creators
- **Tags** - Custom tags and labels
- **Lineage** - Extract from Custom SQL queries, LookML SQL, M Query (converted to SQL)

## Required Aspects

| Aspect                 | Required              | Description                                                |
| ---------------------- | --------------------- | ---------------------------------------------------------- |
| `dataPlatformInstance` | ✅ ALWAYS             | Links entity to data platform. **Always required.**        |
| `containerProperties`  | ✅ ALWAYS             | For workspaces/projects/folders                            |
| `subTypes`             | ✅ ALWAYS             | Identifies entity subtype (Dashboard, Chart, Report)       |
| `container`            | ✅ ALWAYS             | Links entities to parent containers                        |
| `dashboardInfo`        | ✅ IF DASHBOARD       | Dashboard metadata (required for all dashboards)           |
| `chartInfo`            | ✅ IF CHART           | Chart metadata (required for all charts)                   |
| `ownership`            | ✅ IF SOURCE PROVIDES | Dashboard/chart owners (required if source exposes owners) |
| `globalTags`           | ✅ IF SOURCE PROVIDES | Tags from source system (required if source has tags)      |
| `browsePathsV2`        | 🔄 AUTO               | Auto-generated from `container` aspect                     |
| `status`               | 🔄 AUTO               | Auto-generated for all entities                            |

## Implementation Guide

→ **See [API-Based Sources Guide](../api.md)** for implementation details

## Lineage Considerations

Many BI tools allow custom SQL queries. See [Lineage Extraction Guide](../lineage.md) for SQL parsing patterns.

## Example Sources in DataHub

- `src/datahub/ingestion/source/tableau/`
- `src/datahub/ingestion/source/looker/`
- `src/datahub/ingestion/source/powerbi/`
