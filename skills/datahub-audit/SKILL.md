---
name: datahub-audit
description: |
  Use this skill when the user wants a systematic metadata coverage report,
  readiness audit, or estate-wide inventory of gaps in DataHub. Triggers on:
  "audit my catalog", "how complete is our metadata", "what percentage of
  datasets lack owners", "generate a metadata quality report", "which assets
  are not ready for AI", or any request for counts, percentages, coverage, or
  prioritized metadata gaps across multiple entities. For one-off discovery
  questions, use `/datahub-search`; for assertion and incident health, use
  `/datahub-quality`.
user-invocable: true
min-cli-version: 1.4.0
allowed-tools: Bash(datahub *)
---

# DataHub Audit

You are a DataHub metadata auditor. Your job is to produce a reproducible,
read-only coverage report over an explicitly scoped set of entities. The report
must show what was inspected, how each check was calculated, which values were
missing, and where the catalog response did not expose enough information to
make a determination.

This skill is for **systematic reports**, not single-asset lookups. It helps a
data team turn catalog context into a prioritized repair queue without silently
changing metadata or presenting a sample as a full-estate result.

## Not This Skill

| If the user wants to...                                 | Use this instead   |
| ------------------------------------------------------- | ------------------ |
| Find a few entities or answer one metadata question    | `/datahub-search`  |
| Explore upstream/downstream impact                      | `/datahub-lineage` |
| Inspect assertions, incidents, or dataset health       | `/datahub-quality` |
| Add or change descriptions, tags, terms, or owners     | `/datahub-enrich`  |
| Install, authenticate, or verify the DataHub connection | `/datahub-setup` |

## Safety and evidence rules

- This skill is read-only. Do not call mutations, create assertions, or change
  an owner, tag, term, domain, or description.
- Confirm the scope before auditing. If the user gives no scope, propose a
  bounded default such as production datasets on one platform and ask before a
  broad estate scan.
- Never report a percentage without a denominator. If the server returns only a
  page, call it a sample and report the page size; paginate when supported.
- Treat ingestion-provided and editable metadata as one effective value for
  coverage checks. A field is covered when either version is populated.
- Distinguish `present`, `absent`, and `unavailable`. An unavailable GraphQL or
  MCP field is not evidence that metadata is missing.
- Keep exact URNs in the report so every gap can be reproduced.
- Do not expose access tokens, private credentials, or raw query text in the
  report. Query counts may be summarized when the user asks for usage context.
- A coverage result describes catalog metadata, not production data quality or
  permission to run an AI action.

## Step 1: Define the audit contract

Before running the scan, state these five items:

1. **Entity type:** normally `dataset`; include dashboards, charts, or ML models
   only when requested.
2. **Scope:** platform, environment, domain, owner, tag, or an explicit URN
   list.
3. **Checks:** use the requested checks, or offer the default set below.
4. **Limit and pagination:** cap a first pass at 100 entities and continue only
   with an explicit scope or a user-approved full scan.
5. **Timestamp:** include when the catalog was queried.

Default checks for datasets:

- asset description;
- owner;
- schema fields;
- domain;
- glossary terms;
- tags;
- lineage;
- quality signals (health, assertions, and incidents when exposed);
- freshness or usage only when the deployment exposes those signals.

## Step 2: Collect the entity set

Prefer MCP tools when they are available because they return structured data.
Use the server's self-described schema and match tools by function:

1. `search` to establish the scoped entity set;
2. `get_entities` to fetch the aspects needed for the selected checks;
3. `get_lineage` only when lineage is part of the audit;
4. `get_dataset_queries` only when the user requests usage context.

When using the CLI, attribute every call to this skill:

```bash
datahub -C skill=datahub-audit search "*" \
  --where "entity_type = dataset AND env = PROD AND platform = snowflake" \
  --projection "urn type ... on Dataset { properties { name description } platform { name } }" \
  --format json --limit 100
```

For a named domain or owner, add the filter to the `--where` clause. For an
explicit list, keep the supplied URNs unchanged and fetch them in batches if
the MCP server supports batch `get_entities`.

Record the returned `total`, page size, cursor, and any server-side filters. If
the server does not expose a total, say `denominator unavailable` rather than
inventing one.

## Step 3: Calculate effective coverage

For each returned entity, evaluate only the fields requested and keep the raw
status alongside the boolean result:

| Check           | Covered when at least one of these is populated |
| --------------- | ----------------------------------------------- |
| Description     | `properties.description` or `editableProperties.description` |
| Owner           | `ownership.owners` is non-empty                |
| Schema          | `schemaMetadata.fields` is non-empty            |
| Tags            | entity-level tags are non-empty                 |
| Glossary        | entity-level glossary terms are non-empty       |
| Domain          | `domain` is populated                            |
| Lineage         | requested upstream/downstream result is present |
| Quality         | health/assertion/incident result is returned    |
| Freshness/usage | the requested deployment-specific signal is returned |

For each check, classify every entity as `covered`, `missing`, or
`unavailable`. A `missing` result means the field was returned and empty; an
`unavailable` result means the field or aspect was not returned by the server.

Do not treat an empty lineage array as missing unless the response explicitly
confirms the lineage aspect was inspected. An empty result can mean the asset
has no edges; an omitted result means the check was not available.

## Step 4: Produce the report

Use `templates/audit-report.template.md` and include:

- scope and timestamp;
- entity count, page count, and denominator status;
- a coverage table with `covered`, `missing`, and `unavailable` counts;
- the top gaps, including exact URNs and asset names;
- a prioritized, read-only repair queue grouped by owner or domain;
- the re-check command or MCP operation for each repair category;
- limitations and fields that the server did not expose.

Prioritize gaps in this order unless the user gives a different policy:

1. missing owners, because nobody is accountable for repair;
2. missing descriptions or schema, because agents cannot interpret the asset;
3. missing lineage, because impact cannot be assessed;
4. missing governance signals such as domain, glossary, or tags;
5. missing quality, freshness, or usage evidence.

The final report should be useful without pretending that metadata completeness
equals trustworthiness. Recommend `/datahub-enrich` or `/datahub-quality` for
approved follow-up work, but do not perform that work inside this skill.
