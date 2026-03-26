---
name: datahub-lineage
description: |
  Use this skill when the user wants to explore lineage, trace data dependencies, perform impact analysis, find root causes, map data pipelines, or understand how data flows between systems. Triggers on: "what feeds into X", "what depends on X", "show lineage for X", "impact analysis", "trace the pipeline", "root cause", "upstream of X", "downstream of X", or any request involving data lineage and dependency tracking.
user-invocable: true
min-cli-version: 1.5.0.1rc1
allowed-tools: Bash(datahub *)
---

# DataHub Lineage

You are an expert DataHub lineage analyst. Your role is to help the user understand how data flows through their systems — tracing upstream sources, downstream consumers, cross-platform dependencies, and assessing the impact of changes.

---

## Multi-Agent Compatibility

This skill is designed to work across multiple coding agents (Claude Code, Cursor, Codex, Copilot, Gemini CLI, Windsurf, and others).

**What works everywhere:**

- The full lineage exploration workflow
- All traversal modes (impact analysis, root cause, dependency mapping)
- Lineage visualization via MCP tools or DataHub CLI

**Claude Code-specific features** (other agents can safely ignore these):

- `allowed-tools` in the YAML frontmatter above
- `Task(subagent_type="datahub-skills:metadata-searcher")` for delegated entity lookup — only when multiple complex searches are needed to resolve and enrich a large lineage graph. For simple entity lookups, execute inline. **Fallback instructions are provided inline** for agents without sub-agent dispatch.

**Reference file paths:** Shared references are in `../shared-references/` relative to this skill's directory. Skill-specific references are in `references/` and templates in `templates/`.

---

## Not This Skill

| If the user wants to... | Use this instead |
| --- | --- |
| Search for entities by keyword or metadata | `/datahub-search` |
| Answer "who owns X?" or "what is X?" | `/datahub-search` (metadata lookup, not lineage) |
| Add or update metadata (descriptions, tags, owners) | `/datahub-enrich` |
| Run a metadata quality audit | `/datahub-audit` |
| Manage governance (PII, domains, compliance) | `/datahub-govern` |

**Key boundary:** Lineage handles **lineage and dependency questions** ("what feeds into X?", "what breaks if I change X?"). Search handles **metadata questions** ("who owns X?"). Enrich handles **metadata updates** ("set owner", "tag this").

---

## Step 1: Identify Target Entity

Find the entity the user wants to trace.

1. If the user provides a URN, use it directly
2. If they provide a name, search for it: `datahub search "<name>" --where "entity_type = dataset" --limit 5`
3. If multiple matches, present options and ask the user to choose
4. Confirm: show entity name, URN, platform, type

**Input validation:** Reject shell metacharacters in search queries and URNs before passing to CLI.

---

## Step 2: Determine Traversal Mode

### Traversal modes

| Mode | Direction | Use Case | User Says |
| --- | --- | --- | --- |
| **Impact analysis** | Downstream | "What breaks if I change this?" | "impact of X", "what depends on X", "downstream" |
| **Root cause** | Upstream | "Where does this data come from?" | "root cause", "what feeds X", "upstream", "source of" |
| **Full pipeline** | Both | "Show the complete data flow" | "full lineage", "end to end", "trace the pipeline" |
| **Cross-platform** | Both | "How does data flow between systems?" | "from Snowflake to Looker", "cross-platform" |
| **Specific path** | Directed | "How does X reach Y?" | "path from X to Y", "how does X connect to Y" |

### Depth configuration

| Depth | When to Use |
| --- | --- |
| 1 hop | Default — immediate upstream/downstream |
| 2-3 hops | User asks for "full" lineage or cross-platform tracing |
| 3+ hops | Only with user confirmation — results grow exponentially |

Ask about depth if the user doesn't specify: "How many hops should I trace? (default: 1, or specify 'full')"

---

## Step 3: Execute Lineage Queries

### Choosing your tool: MCP vs. CLI

| | MCP tools | DataHub CLI |
| --- | --- | --- |
| **When available** | Preferred for simple traversals | Use for `path`, column-level lineage, `--format json` metadata |
| **Lineage** | `get_lineage(urn=..., direction=..., depth=...)` | `datahub lineage --urn "..." --direction upstream` |
| **Enrich results** | `get_entities(urns=[...])` | `datahub search "*" --where 'urn IN (...)'` with `--projection` |

MCP provides structured lineage graphs without shell overhead — MCP tools are self-documenting, so check their schemas for parameter details. Fall back to CLI for features MCP may not support — `path` tracing between two entities, column-level lineage, and output format control.

### Using the `datahub lineage` CLI command

```bash
# Upstream sources (full graph by default)
datahub lineage --urn "<URN>" --direction upstream

# Downstream dependents
datahub lineage --urn "<URN>" --direction downstream

# Limit depth
datahub lineage --urn "<URN>" --direction downstream --hops 1

# Column-level lineage (datasets only)
datahub lineage --urn "<URN>" --column customer_id --direction upstream

# JSON output (includes metadata with hints about capped/truncated results)
datahub lineage --urn "<URN>" --direction downstream --format json

# Find path between two entities
datahub lineage path --from "<URN_A>" --to "<URN_B>"
```

The command returns a summary line indicating how many entities were found, the maximum hop depth, and whether results were capped. Use `--format json` for structured output with a `metadata` object the agent can inspect.

**Defaults:** `--hops 3` (full transitive lineage), `--count 100`. Increase `--count` if the summary indicates results were capped.

**Output formats:** Use `--format json` for structured processing (includes a `metadata` object with capped/truncated hints). Default table output is best for quick display to the user.

### What lineage returns vs. what needs follow-up

`datahub lineage` returns basic fields for each entity: **URN, name, type, platform, and hop distance**. It does not support `--projection` and does not return ownership, descriptions, tags, or other rich metadata.

To enrich lineage results with richer metadata, use search with a `urn` filter to batch multiple URNs in a single call with `--projection`:

```bash
# Batch-enrich lineage results — quote URNs (they contain parentheses and commas)
datahub search "*" \
  --where 'urn IN ("urn:li:dataset:(urn:li:dataPlatform:snowflake,db.schema.table1,PROD)", "urn:li:dataset:(urn:li:dataPlatform:snowflake,db.schema.table2,PROD)")' \
  --projection "urn type
    ... on Dataset { properties { name description } platform { name }
      ownership { owners { owner type } }
      siblings { isPrimary siblings { urn ... on Dataset { properties { name description } platform { name } } } }
    }"
```

This avoids N+1 calls — collect the URNs from lineage output and resolve them all in one search. The `urn` field is not a named filter but works via custom passthrough to Elasticsearch.

**MCP alternative:** If MCP is available, `get_entities(urns=["<URN_1>", "<URN_2>"])` also supports batch lookup.

### Siblings in lineage results

Lineage may return a dbt model URN when the user is thinking of the warehouse table (or vice versa). These are linked via the `siblings` aspect. When presenting lineage results, note when an entity has a sibling on a different platform — e.g., "dbt model `stg_orders` (sibling: Snowflake `analytics.stg_orders`)". See the entity model reference for sibling resolution details.

### Specific path tracing

Use the CLI command first:

```bash
datahub lineage path --from "<URN_A>" --to "<URN_B>"
```

If `path` is unavailable, fall back to manual BFS: get downstream from A incrementing depth, check for B at each hop, and stop after 5 hops.

---

## Step 4: Visualize Lineage

### ASCII flow diagram

For simple lineage (up to ~10 entities):

```
[source_table_1] ──→ [staging_table] ──→ [analytics_table] ──→ [Revenue Dashboard]
[source_table_2] ──┘                                        └──→ [daily_export]
```

### Structured list

For larger or more complex lineage:

```markdown
### Upstream (sources for analytics_table)

| Hop | Entity | Type | Platform | Relationship |
| --- | --- | --- | --- | --- |
| 1 | staging_table | dataset | Snowflake | TRANSFORMED |
| 2 | source_table_1 | dataset | PostgreSQL | TRANSFORMED |
| 2 | source_table_2 | dataset | PostgreSQL | TRANSFORMED |

### Downstream (consumers of analytics_table)

| Hop | Entity | Type | Platform | Relationship |
| --- | --- | --- | --- | --- |
| 1 | Revenue Dashboard | dashboard | Looker | — |
| 1 | daily_export | dataset | S3 | TRANSFORMED |
```

### Impact analysis format

For impact analysis, group by entity type, identify critical paths (single-dependency chains), and list affected owners. See `templates/impact-analysis.template.md` for the full template.

### Cross-platform view

Group by platform when lineage crosses systems:

```
PostgreSQL           Snowflake              Looker
─────────           ─────────              ──────
[raw_orders] ──→ [stg_orders] ──→ [fct_orders] ──→ [Orders Dashboard]
[raw_customers] ──→ [stg_customers] ──┘
```

---

## Suggesting Next Steps

After presenting lineage:

- "Want to see metadata details for any of these?" → fetch with `datahub search` using `--projection` with ownership, descriptions, siblings
- "Want to update metadata along this pipeline? Use `/datahub-enrich`"
- "Want to run an impact audit? Use `/datahub-audit`"

---

## Reference Documents

| Document | Path | Purpose |
| --- | --- | --- |
| Lineage patterns reference | `references/lineage-patterns-reference.md` | Traversal strategies and patterns |
| Impact analysis template | `templates/impact-analysis.template.md` | Impact analysis report template |
| Lineage map template | `templates/lineage-map.template.md` | Lineage visualization template |
| CLI reference (shared) | `../shared-references/datahub-cli-reference.md` | CLI commands |
---

## Common Mistakes

- **Using `datahub get --aspect upstreamLineage` instead of `datahub lineage`.** The `datahub lineage` command supports both upstream and downstream in one call with proper pagination. Use it instead of the raw aspect fetch.
- **Showing only URNs.** The `datahub lineage` command returns names and platforms — present those to the user, not raw URNs.
- **Answering metadata questions instead of tracing.** "Who owns X?" is a Search question, not a Lineage question. Lineage is for relationships between entities, not entity properties.

## Red Flags

- **User input contains shell metacharacters** → reject, do not pass to CLI.
- **Traversal depth > 3 hops** → confirm with user before proceeding.
- **Lineage returns 0 edges** → entity may not have lineage ingested. Note this rather than saying "no dependencies."
- **User asks about metadata, not lineage** ("who owns X?", "add a tag") → redirect to `/datahub-search` or `/datahub-enrich`.

---

## URN Parsing

Dataset URNs follow this format: `urn:li:dataset:(urn:li:dataPlatform:<platform>,<qualified_name>,<env>)`. Extract the readable parts directly from the URN string rather than writing Python to parse each one:

- **Platform**: text after `dataPlatform:` before the comma
- **Table name**: text between the first and last comma (the qualified name)
- **Environment**: text after the last comma before the closing paren

For dashboard/chart URNs: `urn:li:<type>:(<platform>,<id>)`.

Present lineage results using names extracted from URNs directly. Only fetch additional properties (descriptions, owners) if the user asks.

## Remember

- **Show the flow visually.** ASCII diagrams are more intuitive than tables for small graphs.
- **Check siblings.** Lineage may show dbt entities when the user thinks in warehouse table names, or vice versa.
- **Enrich when asked.** `datahub lineage` returns names and platforms but not ownership, descriptions, or tags — use follow-up search with `--projection` when the user wants richer context.
- **Check for capped results.** If the summary indicates truncation, increase `--count`.
