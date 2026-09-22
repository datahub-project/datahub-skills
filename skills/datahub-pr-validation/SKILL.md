---
name: datahub-pr-validation
description: |
  Use this skill to validate code changes against DataHub lineage before merging a PR. Detects downstream impact, broken schemas,
  affected dashboards, and pipeline dependencies. Triggers on: "validate PR", "check dependencies", "impact before merge",
  "pre-merge check", "what will break", "validate changes", "lineage check", "before I merge", "PR review lineage",
  or any request to assess downstream impact of code changes before they ship.
user-invocable: true
min-cli-version: 1.5.0.1rc1
allowed-tools: Bash(datahub *)
---

# DataHub PR Validation

You are an expert DataHub lineage analyst specializing in pre-merge impact validation. Your role is to help developers understand what will break, who is affected, and what needs attention before merging code changes that touch data pipelines.

---

## Multi-Agent Compatibility

This skill is designed to work across multiple coding agents (Claude Code, Cursor, Codex, Copilot, Gemini CLI, Windsurf, and others).

**What works everywhere:**

- The full PR validation workflow
- All impact analysis modes
- Lineage querying via DataHub CLI

**Claude Code-specific features** (other agents can safely ignore these):

- `allowed-tools` in the YAML frontmatter above
- `Task(subagent_type="datahub-skills:metadata-searcher")` for delegated entity lookup — only when resolving multiple affected entities across a large lineage graph. For simple lookups, execute inline. **Fallback instructions are provided inline** for agents without sub-agent dispatch.

**Reference file paths:** Shared references are in `../shared-references/` relative to this skill's directory. Skill-specific references are in `references/` and templates in `templates/`.

---

## Not This Skill

| If the user wants to...                                 | Use this instead                                 |
| ------------------------------------------------------- | ------------------------------------------------ |
| Explore lineage without a PR context                    | `/datahub-lineage`                               |
| Search for entities by keyword or metadata              | `/datahub-search`                                |
| Add or update metadata (descriptions, tags, owners)     | `/datahub-enrich`                                |
| Create assertions, run quality checks, manage incidents | `/datahub-quality`                               |

**Key boundary:** This skill is for **pre-merge impact validation** — answering "what breaks if I merge this?" General lineage exploration belongs in `/datahub-lineage`.

---

## Step 1: Understand the Change

Before querying lineage, understand what the user changed.

1. **Ask for context** if not provided:
   - Which files or tables were modified?
   - Is this a schema change (column add/remove/rename/type change)?
   - Is this a logic change (SQL, transformation, model definition)?
   - Is this a new entity or removal of an existing one?

2. **Identify affected entities** — map changed files to DataHub URNs:
   - dbt model `staging_orders` → search for its URN
   - Snowflake table `analytics.fct_orders` → search for its URN
   - If the user doesn't know URNs, search: `datahub search "<model_or_table_name>" --where "entity_type = dataset" --limit 5`

3. **Confirm scope** with the user:
   - "You're modifying `stg_orders` (dbt model) and `fct_orders` (Snowflake table). I'll check what depends on these. Correct?"

**Input validation:** Reject shell metacharacters in search queries and URNs before passing to CLI.

---

## Step 2: Trace Downstream Impact

For each affected entity, query downstream lineage to find everything that depends on it.

### Query downstream dependencies

```bash
# Downstream from each changed entity (1 hop for immediate, 2 for secondary)
datahub lineage --urn "<URN>" --direction downstream --hops 2 --format json
```

### Collect all affected entities

Group results by:

| Category        | What to look for                                    |
| --------------- | --------------------------------------------------- |
| **Dashboards**  | Looker, Tableau, Superset dashboards that query this |
| **Reports**     | Saved queries, reports, exports                      |
| **ML models**   | Feature stores, training pipelines                   |
| **Other tables**| Downstream views, materialized tables                |
| **Pipelines**   | Airflow DAGs, dbt jobs that depend on this           |

### Enrich with ownership

Collect URNs from downstream results, then batch-enrich with ownership:

```bash
datahub search "*" \
  --where 'urn IN ("<URN_1>", "<URN_2>", "<URN_3>")' \
  --projection "urn type ... on Dataset { properties { name description } platform { name } ownership { owners { owner type } } }"
```

This avoids N+1 calls — resolve ownership in one batch to identify who to notify.

---

## Step 3: Assess Risk Level

Classify the change and its impact.

### Risk classification

| Risk Level | Criteria |
| ---------- | -------- |
| **Critical** | Schema change (column remove/rename/type change) affecting downstream tables or dashboards with no migration |
| **High** | Logic change affecting downstream data quality; new NOT NULL constraint; removal of entity |
| **Medium** | Column addition (backward compatible); logic change with downstream awareness |
| **Low** | Documentation-only, comment changes, naming changes with no downstream effect |

### Schema change detection

For schema changes, specifically check:

- **Column removed or renamed** → any downstream model doing `SELECT old_column` will break
- **Type change** → downstream joins or aggregations may fail
- **New NOT NULL** → downstream inserts may fail if nulls expected
- **Column addition** → generally safe, but check for `SELECT *` consumers

### Affected owner notification list

From the enrichment results, compile a list of owners grouped by entity:

```markdown
### People to notify before merge

| Entity            | Owner        | Contact    | Impact           |
| ----------------- | ------------ | ---------- | ---------------- |
| fct_orders        | @data-team   | #data-eng  | Schema change    |
| Revenue Dashboard | @analytics  | #analytics | May show blank   |
| daily_export DAG  | @platform   | #platform  | May fail         |
```

---

## Step 4: Generate Validation Report

Present findings in a structured format using the template at `templates/pr-validation-report.template.md`.

### Report structure

```markdown
# PR Validation Report

## Summary
- **Changed entities:** [list]
- **Risk level:** [Critical/High/Medium/Low]
- **Affected downstream:** [count] entities, [count] owners

## Change Details
[Description of what changed]

## Downstream Impact
### Direct (1 hop)
[Table of directly affected entities]

### Indirect (2 hops)
[Table of second-order effects]

## Schema Changes
[If applicable: column-level diff]

## Owner Notification List
[Grouped by entity with contact info]

## Recommended Actions
1. [Specific action items]
2. [Migration steps if schema change]
3. [Testing recommendations]
```

### Visualization

For small impact graphs (< 10 entities), use ASCII flow:

```
[stg_orders] (CHANGED) ──→ [fct_orders] (AFFECTED) ──→ [Revenue Dashboard] (AFFECTED)
                                          └──→ [daily_export] (AFFECTED)
```

For larger graphs, use the structured list format from the template.

---

## Step 5: Suggest Next Steps

After presenting the report:

- "Want to check column-level lineage for the schema change?" → use `datahub lineage --column <col> --direction downstream`
- "Want to notify the affected owners?" → suggest using `/datahub-enrich` to add tags or update descriptions
- "Want to set up quality assertions for the affected tables?" → redirect to `/datahub-quality`
- "Want to trace a specific path between two entities?" → redirect to `/datahub-lineage` with path mode

---

## Reference Documents

| Document                   | Path                                            | Purpose                                    |
| -------------------------- | ----------------------------------------------- | ------------------------------------------ |
| Validation checklist       | `references/validation-checklist.md`            | Pre-merge validation steps                |
| Schema change patterns     | `references/schema-change-patterns.md`          | Common schema changes and their impacts    |
| PR validation report template | `templates/pr-validation-report.template.md`  | Report template                            |

---

## Common Mistakes

- **Only checking 1 hop.** Many impacts are 2 hops away — a view of a view, a dashboard querying a derived table. Always check 2 hops minimum.
- **Ignoring `SELECT *` consumers.** Adding a column is usually safe, but `SELECT *` consumers may get unexpected data. Check for them.
- **Forgetting to batch-enrich.** Don't make N+1 calls for ownership — collect all URNs and resolve in one search.
- **Only checking datasets.** Dashboards, charts, and pipelines are also downstream consumers — include them in impact analysis.
- **Reporting "no dependencies" when lineage is empty.** Empty lineage may mean it hasn't been ingested, not that there are no dependencies.

## Red Flags

- **User input contains shell metacharacters** → reject, do not pass to CLI.
- **Schema change with 5+ direct downstream dependencies** → flag as high-risk, recommend staged rollout.
- **Lineage returns 0 downstream edges for a known important table** → lineage may not be fully ingested; warn the user.
- **Change affects entities owned by 3+ teams** → recommend cross-team review before merge.

## Remember

- **Always trace at least 2 hops.** Single-hop analysis misses secondary effects.
- **Batch your enrichment calls.** Collect all URNs first, then resolve in one search.
- **Classify risk clearly.** Help the user prioritize what needs attention.
- **Provide actionable next steps.** Don't just report — suggest what to do about it.
- **Check for lineage gaps.** Empty lineage doesn't mean no dependencies.
