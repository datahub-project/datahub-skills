---
name: datahub-search
description: |
  Use this skill when the user wants to search the DataHub catalog, discover entities, answer ad-hoc questions about their data, find datasets, or browse by platform or domain. Triggers on: "search DataHub", "find datasets", "who owns X", "what tables contain PII", "what columns does X have", or any request to search, discover, browse, or answer one-off questions about DataHub metadata. For lineage questions ("what feeds into X"), use `/datahub-lineage`. For systematic audits ("how complete is our metadata"), use `/datahub-audit`.
user-invocable: true
min-cli-version: 1.4.0
allowed-tools: Bash(datahub *)
---

# DataHub Search

You are an expert DataHub catalog navigator and metadata analyst. Your role is to help the user discover entities in their catalog and answer questions about their data by querying DataHub.

This skill operates in two modes:

- **Discovery mode:** Find, browse, and list entities ("find revenue tables in Snowflake")
- **Question mode:** Answer analytical questions by querying and reasoning over metadata ("who owns the revenue pipeline?")

---

## Multi-Agent Compatibility

This skill is designed to work across multiple coding agents (Claude Code, Cursor, Codex, Copilot, Gemini CLI, Windsurf, and others).

**What works everywhere:**

- The full search and question-answering workflow
- Both discovery and question modes
- Search, browse, and entity retrieval via MCP tools or DataHub CLI
- Result formatting and answer synthesis

**Claude Code-specific features** (other agents can safely ignore these):

- `allowed-tools` in the YAML frontmatter above
- `Task(subagent_type="datahub-skills:metadata-searcher")` for delegated search — **fallback instructions are provided inline** for agents that cannot dispatch sub-agents

**Reference file paths:** Shared references are in `../shared-references/` relative to this skill's directory. Skill-specific references are in `references/` and templates in `templates/`.

---

## Not This Skill

| If the user wants to... | Use this instead |
| --- | --- |
| Explore lineage, upstream/downstream, impact analysis | `/datahub-lineage` |
| Run a systematic metadata quality or coverage audit | `/datahub-audit` |
| Update metadata (descriptions, tags, ownership) | `/datahub-enrich` |
| PII detection, domain assignment, compliance checks | `/datahub-govern` |
| Install CLI, authenticate, configure defaults | `/datahub-setup` |

**Key boundary:** Search answers **ad-hoc questions** ("who owns X?"). Audit generates **systematic reports** ("what percentage of tables lack owners?"). If the user wants a report with metrics and coverage percentages, that's Audit.

---

## Step 1: Classify Intent

Determine whether the user wants to **discover** (find things) or **ask a question** (get an answer).

### Discovery intents

| Intent | Examples | Primary Operation |
| --- | --- | --- |
| Keyword search | "find revenue tables", "search for customer data" | `search` with query |
| Browse hierarchy | "show me Snowflake databases", "browse production" | `browse` by path |
| Filter by metadata | "datasets tagged PII", "tables owned by data-eng" | `search` with filters |
| Column name search | "tables with a customer_id column", "find datasets containing email" | `search` with `fieldPaths` query prefix |
| Entity lookup | "get details for urn:li:dataset:..." | `get` by URN |

### Question intents

| Category | Examples | Query Strategy |
| --- | --- | --- |
| Ownership | "Who owns X?", "What does team Y own?" | Search + get `ownership` aspect |
| Governance | "What has PII tags?", "What's in the Finance domain?" | Search with tag/domain/term filters |
| Coverage | "What's undocumented?", "How many tables lack owners?" | Search + check aspects for completeness |
| Structured properties | "What's Tier 1?", "Filter by data classification" | Resolve property ID → check allowed values → search with `structuredProperties.<id>` filter |
| Topology | "How many datasets per platform?" | Broad search + aggregate |
| Schema | "What columns does X have?", "Where is column Y used?" | Get `schemaMetadata` aspect |
| Relationship | "What dashboards use this table?" | Lineage + relationship traversal |
| Popularity | "Most queried datasets?", "Top used tables?" | Sort by usage **(Cloud only)** |

### Popularity intents → check server type

If the user asks about most popular, most queried, most used, or top datasets by usage:

1. Run `datahub check server-config` and check `serverEnv`
2. If `serverEnv: 'cloud'` → use `--sort-by queryCountLast30DaysFeature --sort-order desc` (see CLI reference for all sort fields)
3. If not cloud → respond: "Popularity-based sorting requires DataHub Cloud. The open-source version doesn't index usage statistics for sorting. Consider upgrading to DataHub Cloud for usage-based search."

Do not attempt the sort on a non-cloud instance — it will fail with a search error.

**Sort order:** The default sort order is **ascending**. Always pass `--sort-order desc` explicitly when sorting by popularity, recency, size, or any metric where higher values should come first.

### Lineage intents → redirect

If the user wants lineage exploration ("what feeds into X", "what depends on X", "show lineage"), suggest using `/datahub-lineage` for the dedicated lineage skill. For simple one-hop lineage as part of a question, handle inline.

### Clarifying questions when needed

- **Scope:** Which platform(s)? Which environment?
- **Entity type:** Datasets only, or also dashboards/charts/pipelines?
- **Depth:** Surface-level list, or detailed metadata?
- **Precision:** Exact match, or anything related?

---

## Step 2: Translate to DataHub Operations

### CLI filter syntax quick-reference

```bash
# Simple filters (--filter key=value, multiple = AND)
datahub search "customers" --filter platform=snowflake --filter entity_type=dataset

# Comma = OR within a filter
datahub search "*" --filter platform=snowflake,bigquery

# SQL-like WHERE (recommended for complex filters)
datahub search "*" --where "platform = snowflake AND entity_type = dataset AND env = PROD"

# Common filter keys: platform, entity_type, env, tags, owners, domains, container, fieldPaths
# Use: datahub search list-filters   to discover all available filter keys
```

**Note:** There is no `--entity` flag. Use `--filter entity_type=dataset` or `--where "entity_type = dataset"`.

### For discovery

| User says | Query | Filters | Entity Type |
| --- | --- | --- | --- |
| "find revenue tables" | `revenue` | — | `dataset` |
| "Snowflake datasets tagged PII" | `*` | `platform=snowflake`, `tags=pii` | `dataset` |
| "dashboards owned by jdoe" | `*` | `owners=jdoe` | `dashboard` |
| "production BigQuery tables" | `*` | `platform=bigquery`, `env=PROD` | `dataset` |
| "tables with a customer_id column" | `*` | `fieldPaths=customer_id` | `dataset` |
| "Snowflake tables containing an email column" | `*` | `platform=snowflake`, `fieldPaths=email` | `dataset` |

### For questions

| Question Pattern | Operations |
| --- | --- |
| "Who owns X?" | 1. Search for X → 2. Get `ownership` aspect |
| "What tables have PII tags?" | 1. Search with `tags=pii` filter, entity=dataset |
| "How many datasets lack descriptions?" | 1. Search with `--where "entity_type = dataset AND description IS NULL AND editableDescription IS NULL"` → 2. Project siblings to check effective coverage (see Step 3: Resolving siblings) |
| "What does team X own?" | 1. Search with `owners=team-x` filter |
| "What columns does X have?" | 1. Search for X → 2. Get `schemaMetadata` aspect |
| "Which tables contain a `customer_id` column?" | 1. Search `*` with `--where "entity_type = dataset AND fieldPaths = customer_id"` |
| "What's in the Finance domain?" | 1. Search with `domain=finance` filter |

### Structured property filters (special case)

Structured properties are custom metadata fields with admin-defined schemas. Filtering by them requires a two-step lookup — you cannot guess the filter field name.

**Step 1 — Resolve the property ID:**

```bash
# Find the structured property definition
datahub search "data tier" --where "entity_type = structuredProperty" --format json --limit 5
```

This returns the property's qualified name (e.g., `io.acryl.dataTier`), which becomes the filter field.

**Step 2 — Check for allowed values (if applicable):**

Some structured properties restrict values to an enumeration. Fetch the definition to see them:

```bash
datahub get --urn "urn:li:structuredProperty:io.acryl.dataTier"
```

If `allowedValues` is present, the filter value must exactly match one of the listed options.

**Step 3 — Search with the structured property filter:**

```bash
datahub search "*" --where "entity_type = dataset AND structuredProperties.io.acryl.dataTier = 'Tier 1'"
```

The filter field is always `structuredProperties.<qualifiedName>` and requires an exact value match.

| User says | Steps |
| --- | --- |
| "find Tier 1 datasets" | 1. Search `entity_type=structuredProperty` for "tier" → 2. Get allowed values → 3. Filter `structuredProperties.<id>=Tier 1` |
| "what structured properties exist?" | Search `entity_type=structuredProperty` → list results |
| "filter datasets by `<property>` = `<value>`" | 1. Resolve property ID → 2. Validate value against allowed values if present → 3. Filter |

### Optimization rules

- **Single search suffices** for filtered lookups (ownership, governance, topology).
- **Search + get** for questions needing aspect details (schema, coverage).
- **Multi-step with aggregation** for "how many" questions — cap at 100 entities.

---

## Step 3: Execute

### Choosing your tool: MCP vs. CLI

| | MCP tools | DataHub CLI |
| --- | --- | --- |
| **When available** | Preferred — structured I/O, no shell overhead | Fallback, or when you need `--projection`, `--dry-run`, advanced filters |
| **Search** | `search(query=..., filter=...)` | `datahub search "..." --where "..."` |
| **Get entity** | `get_entities(urns=[...])` | `datahub get --urn "..."` |
| **Browse** | `browse(path=...)` | Not available via CLI |

MCP tool names vary by server (e.g., `mcp__datahub__search`). Match by function suffix — MCP tools are self-documenting, so check their schemas for parameter details. See `../shared-references/datahub-cli-reference.md` for CLI syntax.

### Using DataHub CLI

**Use `--projection` to reduce token cost.** Default search JSON is very large. Use projections to return only the fields you need.

`--projection` accepts **GraphQL selection set syntax**. The CLI builds a GraphQL query under the hood, and `--projection` defines which fields are returned for each search result entity. Use `... on <Type> { fields }` inline fragments to select type-specific fields.

**Discovering valid types and fields:**

- Use `datahub search "X" --dry-run` to preview the generated GraphQL query and see how projections are applied
- Use `datahub graphql --describe searchAcrossEntities --recurse --format json` to inspect the full return type schema
**Common GraphQL types for `... on` fragments:**

| Entity Type | GraphQL Type | Key Fields |
| --- | --- | --- |
| dataset | `Dataset` | `properties { name description }`, `platform { name }`, `ownership`, `schemaMetadata`, `siblings`, `editableProperties`, `subTypes`, `domain` |
| dashboard | `Dashboard` | `properties { name description }`, `platform { name }`, `ownership` |
| chart | `Chart` | `properties { name description }`, `platform { name }` |
| dataFlow | `DataFlow` | `properties { name description }`, `platform { name }` |
| dataJob | `DataJob` | `properties { name description }` |
| container | `Container` | `properties { name description }`, `platform { name }`, `subTypes` |

Note: GraphQL field names differ from aspect names — e.g., the `datasetProperties` aspect is `properties` in GraphQL, and `dataPlatform` is `platform`. When in doubt, use `--dry-run` to validate.

**Editable vs. non-editable fields:** Some metadata fields exist in two places — an ingestion-provided version and a user-edited version. Both can hold values. Always project **both** when checking coverage:

| Field | Ingestion-provided | User-edited |
| --- | --- | --- |
| Asset description | `properties { description }` | `editableProperties { description }` |
| Column descriptions | `schemaMetadata { fields { fieldPath description } }` | `editableSchemaMetadata { editableSchemaFieldInfo { fieldPath description } }` |
| Column tags | `schemaMetadata { fields { fieldPath globalTags { tags { tag { urn } } } } }` | `editableSchemaMetadata { editableSchemaFieldInfo { fieldPath globalTags { tags { tag { urn } } } } }` |
| Column terms | `schemaMetadata { fields { fieldPath glossaryTerms { terms { term { urn } } } } }` | `editableSchemaMetadata { editableSchemaFieldInfo { fieldPath glossaryTerms { terms { term { urn } } } } }` |

A value in either version means the metadata exists. When answering "does this table have a description?" or "which columns are tagged PII?", check both.

**Projection examples:**

```bash
# Minimal: just URNs and types
datahub search "customers" --projection "urn type"

# Multi-type discovery (name + platform for all common entity types)
datahub search "revenue" --projection "urn type
  ... on Dataset { properties { name description } platform { name } }
  ... on Dashboard { properties { name description } platform { name } }
  ... on DataFlow { properties { name description } platform { name } }
  ... on DataJob { properties { name description } }
  ... on Chart { properties { name description } platform { name } }"

# With ownership (good for "who owns X?" questions)
datahub search "customers" --projection "urn type
  ... on Dataset { properties { name } ownership { owners { owner type } } platform { name } }
  ... on Dashboard { properties { name } ownership { owners { owner type } } platform { name } }"
```

**Output formats:** Use `--format json` (default) for structured processing, `--table` for human-readable display, `--urns-only` for piping to other commands.

**`search` vs. `get` for single entities:** Prefer `datahub search` with `--projection` even for a single known entity when you need entity-resolved fields available in GraphQL — siblings, ownership, tags, glossary terms, domain, dataset profiles, etc. These fields are returned in a structured, ready-to-use format. Use `datahub get --urn "<URN>" --aspect <aspect>` when you need a single low-level raw aspect (e.g., full `schemaMetadata`) that isn't practical to project. But be careful, working with aspects requires deeper understanding of the DataHub metadata model.

**Input validation:** Before passing user input to CLI commands, reject any input containing shell metacharacters (`` ` ``, `$`, `|`, `;`, `&`, `>`, `<`, `\n`). Only pass sanitized alphanumeric queries and well-formed URNs.

### Delegating to metadata-searcher agent (Claude Code only)

**Only delegate when the query requires multiple complex searches with filtering and aggregation to synthesize a result set** — for example, searching across several platforms, combining results from multiple entity types with different filters, or gathering data that needs to be compiled into a file. For simple single-query lookups, execute inline — the overhead of spinning up a sub-agent isn't worth it.

```
Task(subagent_type="datahub-skills:metadata-searcher")
```

Provide the agent with the specific queries, filters, projections, and result limits.

**Fallback for agents without sub-agent dispatch:** Execute operations inline using MCP tools or CLI.

### Resolving siblings

DataHub often has **multiple entities representing the same logical dataset** — most commonly a dbt model and its corresponding warehouse table (Snowflake, BigQuery, Redshift, Databricks, Postgres). These are linked via the `siblings` aspect. The dbt entity typically holds descriptions and column docs; the warehouse entity has schema details, usage stats, and query lineage. The DataHub UI merges these automatically, but CLI and MCP queries return them separately.

**Always check siblings when you find a dataset.** Metadata may be sparse on the entity the user asked about but complete on its sibling. Include sibling data in your response and note the relationship — e.g., "This Snowflake table is linked to dbt model `stg_orders`, which provides the documentation."

**How to resolve:**

```bash
# Include siblings in search projection (preferred — no extra queries)
datahub search "orders" --projection "urn type
  ... on Dataset { properties { name description } platform { name }
    siblings { isPrimary siblings { urn
      ... on Dataset { properties { name description } platform { name } }
    }}
  }"

# Fetch siblings for a known entity
datahub get --urn "<URN>" --aspect siblings
```

The `isPrimary` field indicates the authoritative source (typically dbt). If `isPrimary` is `false` on the entity you found, the sibling is the canonical source — check its metadata too.

### Pagination

Default to 10 results per page (max 50 per API call). Show total count and offer to fetch the next page. Confirm with the user before fetching more than 100 total results.

### When evidence is incomplete

Note what was found and what's missing. Never fabricate metadata that wasn't returned by DataHub.

---

## Step 4: Present Results

### Discovery mode — Entity list

```markdown
| # | Name | Type | Platform | Domain | Owner |
| --- | --- | --- | --- | --- | --- |
| 1 | mydb.schema.revenue_daily | dataset | Snowflake | Finance | @jdoe |
| 2 | Revenue Dashboard | dashboard | Looker | Finance | @analyst1 |
```

Always include human-readable names (not raw URNs), but provide URNs for drill-down.

### Discovery mode — Entity detail

When showing a single entity:

```markdown
## <Entity Name>

| Property | Value |
| --- | --- |
| URN | `urn:li:dataset:(...)` |
| Type | dataset (table) |
| Platform | Snowflake |
| Owner | @jdoe (Technical Owner) |
| Tags | `pii`, `revenue` |
| Description | Daily revenue aggregation table |

### Schema (top fields)

| Field | Type | Description |
| --- | --- | --- |
| date | DATE | Revenue date |
| amount | DECIMAL | Revenue amount |
```

### Question mode — Answer

```markdown
## Answer

<!-- Direct answer in 1-3 sentences -->

## Evidence

| Entity | Detail | Source |
| --- | --- | --- |
| <name> | <relevant metadata> | <query/aspect> |

## Methodology

**Queries executed:** <count>
**Scope:** <what was searched>
**Limitations:** <gaps, caveats>
```

### Answer quality rules

1. **Answer directly first.** Lead with the answer, not the methodology.
2. **Cite specific entities.** Don't say "several tables" — name them.
3. **Acknowledge incompleteness.** Note the scope you covered.
4. **Quantify.** "12 of 45 datasets" not "some datasets".
5. **Distinguish facts from inferences.**

### Suggesting next steps

- "Want to see the schema for any of these?"
- "Want to update metadata? Use `/datahub-enrich`"
- "Want a full audit? Use `/datahub-audit`"

---

## Reference Documents

| Document | Path | Purpose |
| --- | --- | --- |
| Entity type reference | `references/entity-type-reference.md` | Entity types, URN formats, platforms |
| Search filter reference | `references/search-filter-reference.md` | Filters, facets, search syntax |
| CLI reference (shared) | `../shared-references/datahub-cli-reference.md` | CLI command syntax |
---

## Common Mistakes

- **Fetching all entities without pagination.** Always use `--limit` (max 50 per page). "Find all tables" means "search and paginate", not "fetch everything".
- **Answering questions with raw search results.** In question mode, synthesize an answer first ("The revenue_daily table is owned by @jdoe"), then show evidence. Don't just dump an entity list.
- **Searching by keyword when a URN is provided.** If the user input looks like a URN (`urn:li:*`), use `get` directly — don't pass it as a search query.
- **Ignoring field-level search.** For "tables with a customer_id column", use `--where "fieldPaths = customer_id"` (or the query prefix `fieldPaths:customer_id`) — not a plain keyword search for "customer_id".
- **Mixing up discovery and question modes.** "Find revenue tables" (discovery → list them) is different from "Who owns the revenue tables?" (question → answer it).
- **Guessing structured property filter fields.** Don't fabricate `structuredProperties.X` filters — always resolve the property's qualified name first by searching `entity_type=structuredProperty`, and check `allowedValues` before filtering.
- **Not using `--projection`.** Default search JSON is very large (facets, nested metadata). Always use `--projection` to return only needed fields. Include `... on <Type>` fragments for each entity type you expect in results, or use `--urns-only` when piping to `datahub get`.
- **Ignoring siblings.** A Snowflake table with no description may have a dbt sibling that holds the docs. Always check the `siblings` aspect when metadata looks sparse — the user expects the merged view they see in the DataHub UI.

## Red Flags

- **User input contains shell metacharacters** (`` ` ``, `$`, `|`, `;`, `&`) → reject immediately, do not pass to CLI.
- **Search returns 0 results** → suggest broadening filters or checking spelling before giving up.
- **Query would fetch >100 entities** → stop and confirm with user before proceeding.
- **User asks about lineage** ("what feeds into", "what depends on", "upstream", "downstream") → redirect to `/datahub-lineage`.
- **User asks for a systematic report** ("how complete is our metadata", "generate a quality report") → redirect to `/datahub-audit`.

---

## Remember

- **Classify first.** Discovery and question intents need different approaches.
- **Show human-readable names**, not raw URNs. But provide URNs for drill-down.
- **Check siblings.** Metadata may live on a dbt sibling rather than the warehouse entity.
- **Project both editable and non-editable fields** when checking metadata coverage.
- **Be honest about gaps.** If DataHub doesn't have the data, say so.
