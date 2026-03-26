# Lineage Patterns Reference

Common lineage traversal strategies and patterns.

## Traversal Strategies

### Impact Analysis (Downstream)

**Goal:** Determine what breaks if an entity changes.

**Strategy:**

1. Get all downstream entities (start with depth 1, expand as needed)
2. Classify by type (datasets, dashboards, jobs)
3. Identify critical paths (entities with single upstream dependency)
4. List affected owners for notification

**Key question:** "Which downstream entities have no alternative data source?"

### Root Cause (Upstream)

**Goal:** Trace where data originates and how it's transformed.

**Strategy:**

1. Get all upstream entities (depth 1-3)
2. Follow until reaching source-of-record systems (databases, APIs, files)
3. Note transformation types at each hop (TRANSFORMED, VIEW, COPY)
4. Identify the original data source

**Key question:** "Where does this data ultimately come from?"

### Full Pipeline (Both Directions)

**Goal:** Map the complete data flow from source to consumption.

**Strategy:**

1. Get upstream to source (root cause)
2. Get downstream to consumers (impact)
3. Merge into a single directed graph
4. Present as end-to-end flow

### Cross-Platform Tracing

**Goal:** Understand how data moves between systems.

**Strategy:**

1. Trace lineage in both directions
2. Group entities by platform
3. Identify cross-platform edges (e.g., PostgreSQL → Snowflake via dbt)
4. Highlight the integration points

### Path Finding

**Goal:** Determine if and how entity A connects to entity B.

**Strategy:**

1. Start BFS from entity A downstream
2. At each hop, check if entity B appears
3. If found, return the path
4. Max depth: 5 hops (ask user before going deeper)

## Lineage Edge Types

| Type | Meaning |
| --- | --- |
| `TRANSFORMED` | Data was transformed (e.g., SQL query, dbt model) |
| `VIEW` | Entity is a view over the source |
| `COPY` | Data was copied without transformation |

## Platform-Specific Lineage Notes

| Platform | Lineage Source | Notes |
| --- | --- | --- |
| dbt | dbt manifest | Model-level lineage, often the richest |
| Airflow | Task dependencies | Job-level lineage |
| Snowflake | Query logs | Column-level lineage possible |
| BigQuery | Audit logs | Table-level lineage |
| Looker | LookML explores | Dashboard → dataset lineage |
| Tableau | Workbook metadata | Dashboard → dataset lineage |

## Choosing the Right Command

| Need | Command | Why |
| --- | --- | --- |
| Unfiltered upstream/downstream | `datahub lineage` | Simple, returns names and platforms |
| Column-level lineage | `datahub lineage --column <field>` | Only command that supports column tracing |
| Filter by type, platform, tags | `searchAcrossLineage` via `datahub graphql` | Server-side filtering avoids fetching full graph |
| Time-windowed lineage | `searchAcrossLineage` with `lineageFlags` | Only way to scope by edge update time |
| Large result sets (300+) | `scrollAcrossLineage` via `datahub graphql` | Cursor-based pagination for large graphs |

## Lineage Limitations

- **Use `datahub lineage`** for both upstream and downstream traversal. Supports `--hops`, `--column`, and `--format json` with metadata hints.
- **Use `searchAcrossLineage`** when filtering is needed. `datahub lineage` has no filter support — use the GraphQL query via `datahub graphql` to filter by entity type, platform, tags, domain, or time window.
- **Depth:** Deep lineage graphs (5+ hops) can be very large. Always cap and ask.
- **Staleness:** Lineage reflects the last ingestion. It may not reflect recent pipeline changes.
- **Column-level:** Not all sources provide column-level lineage. Note when unavailable.
