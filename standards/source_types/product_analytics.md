# Product Analytics Sources

**Source Type:** API-Based

## Overview

Product analytics tools like Snowplow, Amplitude, Mixpanel, and Segment track user events and expose event schemas through REST APIs.

## What to Extract

- **Datasets** - Event streams and collections
- **Containers** - Projects and workspaces (optional)
- **Schemas** - Event schemas and properties

## Required Aspects

| Aspect                 | Required               | Description                                         |
| ---------------------- | ---------------------- | --------------------------------------------------- |
| `dataPlatformInstance` | ✅ ALWAYS              | Links entity to data platform. **Always required.** |
| `datasetProperties`    | ✅ ALWAYS              | Event name, qualified name, custom properties       |
| `schemaMetadata`       | ✅ IF SCHEMA AVAILABLE | Event schema with property definitions              |
| `subTypes`             | ✅ ALWAYS              | Identifies entity subtype (Event, Stream)           |
| `container`            | ✅ IF HIERARCHICAL     | Links to parent container (project, workspace)      |
| `containerProperties`  | ✅ FOR CONTAINERS      | Project/workspace metadata                          |
| `browsePathsV2`        | 🔄 AUTO                | Auto-generated from `container` aspect              |
| `status`               | 🔄 AUTO                | Auto-generated for all entities                     |

## Implementation Guide

→ **See [API-Based Sources Guide](../api.md)** for implementation details

## Special Considerations

- **Event Schemas**: Capture event names and property definitions
- **Sampling**: APIs may only return sampled data
- **Rate Limits**: Analytics APIs often have strict rate limits

## Example Sources in DataHub

- `src/datahub/ingestion/source/looker/` (includes LookML event tracking)
