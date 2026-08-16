---
name: datahub-sql-workflow
description: Ground text-to-SQL work in DataHub catalog evidence. Use when a user asks to write, draft, debug, or execute SQL; answer a data question that requires SQL; calculate a metric; query named tables; or investigate SQL results with DataHub MCP tools available. Always begin with find_sql_context, even when the user already supplied tables or dataset URNs.
license: Apache-2.0
compatibility: Requires DataHub MCP tools (find_sql_context and catalog metadata tools); SQL execution engine optional
metadata:
  author: datahub
  version: "2.0"
---

# DataHub SQL Workflow

Ground every query in DataHub evidence. Treat business context as the authority
for meaning, catalog metadata as the authority for physical shape, and historical
SQL context as evidence of analyst practice.

Require `find_sql_context` and DataHub metadata tools. If it is still unavailable,
stop and ask the user to enable the DataHub MCP tools — do not fall back to any other
evidence source (other discovery tools, local files, memory, web).

Treat every other tool as capability-dependent: if one is unavailable,
disclose the limitation and continue with the supported steps; never
replace missing evidence with guesses.

## 1. Find SQL context first

Call `find_sql_context(question=<user's complete question>)` before any other
catalog, drafting, probing, or execution tool. Do this even when the user names
tables or supplies Dataset URNs.

Read the response by shape and follow its `message`:

- Treat `user_edited` matches and their `instructions` as authoritative. They
  may intentionally contain no datasets, patterns, or snippets.
- Prefer curated `external:*` matches over generated history when they conflict.
- With usable matches, use their patterns and datasets as primary candidates.
  Cross-check `suggested_tables`; suggestions can appear even for a strong match.
- With no usable match but suggested tables, inspect those Dataset URNs and
  follow the message's drafting recommendation.
- With neither usable matches nor suggestions, continue business-context and
  catalog discovery. Call the drafting tool only with concrete Dataset URNs.
- If the message reports a persisted-anchor metadata retrieval error, retry
  `find_sql_context`. Do not reinterpret that failure as an anchor miss.

If two or more usable matches name disjoint datasets for the same metric or
question, resolve the tie through business meaning (step 2). Prefer a
dedicated metric or fact table over a same-named attribute column on an
entity table, and present both candidates if the tie survives.

Generated matches can contain partial document fragments. Call
`grep_documents(pattern=".*", start_offset=..., context_chars=...)` only when a
returned offset can recover context needed for the query.

Interpret `shared_snippets` as modeled sibling semantics, not proof of literal
warehouse values. Treat `suggested_tables[].evidence.source == "both"` as useful
corroboration from independent discovery surfaces, not automatic correctness.

## 2. Establish business meaning

Search business context after the first call when SQL context is weak or
absent, or whenever the canonical definition remains uncertain.

Business-context search is also required when:

- usable matches disagree with each other or with `suggested_tables` about
  which datasets to use; or
- the leading candidate table lives outside the modeled analytics schemas.

When a strong, unambiguous match exists, trust it — do not re-search for
context that is already grounded in the anchor. `search_documents` can
return anchor documents (subtype "Semantic Anchor"); skip these — they
contain the same evidence `find_sql_context` already provided. Focus on
glossary terms, domain alignment, and data products instead.

Search for business context relevant to the question's metric or concept — a
single targeted `search_documents` call is usually sufficient for
calculation rules, metric definitions, and required filters. Use `search`
with an `entity_type` filter for glossary terms, domains, or data products.

If a document or glossary definition names a table or calculation, follow it
unless live evidence exposes a concrete conflict. A catalog table that looks
more specific, newer, or better-named than the documented one is not by
itself a reason to deviate — verify with metadata before overriding. When
documentation and catalog results disagree, state the disagreement and
resolve it before writing SQL. When no business definition exists, state the
gap and ask the user — do not fill it with an inferred interpretation.

Prefer datasets that belong to a matching domain or data product over
identically-named tables outside them — data products mark the curated,
governed query surfaces.

## 3. Verify candidate datasets

When a strong, unambiguous match provides a pattern with sufficient column
and filter detail to draft SQL, go straight to step 5. Run the verification
steps below when the anchor pattern alone is not enough to draft
confidently: columns or join keys are unclear, the message is non-empty
(weak or no match), matches and suggestions name different tables, or the
query requires joining multiple tables.

1. Call `get_entities` on the candidate URNs. Read the metadata as intent
   signals: description, ownership, tags, glossary terms, domain, data
   product, table type, partition or clustering keys. Compare candidates on
   these signals, not by name.
2. Use targeted `list_schema_fields` calls to confirm relevant columns, types,
   and grain.
3. Prefer a governed table already at the requested grain over reconstructing
   the same metric from raw or event-level data. Schema naming conventions
   vary by org — treat a source-schema location as a hypothesis, not a
   conclusion.
4. Confirm that an "all X" question is not answered from a segmented subset.
5. Verify every proposed join key on both sides. Do not add a speculative inner
   join that could silently discard unmatched rows.
6. After `list_schema_fields` on the chosen table, disposition every
   lifecycle and validity column it exposes — deletion markers, state or
   status columns, snapshot or partition dates, latest-row flags. Apply a
   guard only when the question's intended population, a standard-filter
   advisory, or an anchor pattern requires it; otherwise record the column
   as considered and omitted.

Use `standard_filters_by_table` from `find_sql_context` throughout verification:

- Apply applicable guards and date shapes unless the user explicitly overrides
  them.
- Preserve the exact JSON scalar type, casing, and whitespace of
  `declared_enum_values`.
- Treat observed `enum_values` as samples, not an exhaustive allowed set.
- Treat absent advisories as incomplete, not as evidence of no filters;
  response budgeting can omit lower-support details.

## 4. Run targeted probe queries

This step requires a SQL execution tool. If none is available, check
DataHub for data profiles or sample data on the candidate datasets via
`get_entities` — these can resolve column-value, null-rate, and
cardinality questions without a live query. If neither execution nor
profiles are available, skip to step 5 and note any assumptions that a
probe would have resolved.

Run a probe only when its result could materially change the table, join,
filter, grain, or time-window decision — skip it when metadata is already
decisive.

Recommend the cheapest row-shape probe first:

```sql
SELECT <needed_columns>
FROM <fully_qualified_table>
LIMIT 1
```

Use named columns when known. Use `SELECT * ... LIMIT 1` only when metadata
cannot identify the relevant fields. Omit `LIMIT 1` from aggregates that
already return one row.

Use other minimal read-only probes as needed:

- `COUNT(*)` or small grouped counts to test filter viability or grain;
- `COUNT(DISTINCT key)` and duplicate checks to test uniqueness;
- null counts or small grouped distributions to inspect candidate fields;
- `MIN`/`MAX` timestamps to check coverage and freshness;
- matched and unmatched counts to test join coverage;
- comparable aggregates to distinguish otherwise plausible tables.

Select only required fields, apply known guards, and constrain verified
partitions when appropriate. Never use a probe to manufacture a business rule.
Treat empty results, unexpected magnitudes, errors, and timeouts as evidence
about access, freshness, schema drift, table type, or candidate suitability.

If authoritative context and observed schema or data drift apart — the
definition's filter returns nothing, a named column is missing or behaves
differently than described, or the answer requires an assumption the
definition does not cover — use read-only probes only to characterize the
difference. Stop before the final answer query. Quote the definition
exactly, name the drift in one sentence, offer two or three plain-language
interpretations, and ask which matches the user's intent.

Allow at most three diagnostic rounds. Make each round test a new hypothesis;
do not guess-and-retry.

## 5. Draft and verify SQL

Draft directly from a verified anchor pattern when it clearly fits. Call
`draft_sql_for_tables` only when `find_sql_context`'s message explicitly
recommends it — a viable anchor pattern is always preferred over a
generated draft.

Pass the complete question, verified Dataset URNs, and actual SQL platform.
Treat the result as an untrusted draft. Inspect its confidence, explanation,
assumptions, ambiguities, suggested clarifications, tables used, and semantic
model summary. An empty SQL string is a failed draft.

Verify every table, field, join, literal, predicate, and aggregation against the
evidence gathered above. Reconcile the draft with `standard_filters_by_table`:
the tool's internal injection is best-effort, so add missing required predicates
and remove duplicates. Reconcile against the anchor pattern the same way:
carry every guard predicate the pattern applies into the final query, at the
same scope the pattern applies it, or record why it is intentionally
dropped.

Match the answer's shape to the question:

- A present-tense or point-in-time question pins to the latest valid
  snapshot and returns a single result; produce a trend or per-period
  breakdown only when the question asks for one.
- Default to the minimal query that answers the question. Add a join only
  when a required output column cannot come from the chosen table, and be
  able to state which requirement forces each join.

Before execution, ensure every predicate traces to the user's question,
authoritative business context, anchor instructions, a standard-filter advisory,
a verified join, or a probe finding that will be reported. Confirm that the
aggregation grain matches the question.

## 6. Execute safely and report

Execute only a single read-only `SELECT` statement, including read-only CTEs.
Reject DDL, DML, stored procedures, and side-effecting functions even if the
drafting tool merely lowers confidence instead of blocking them.

Execute the final query unless the user requested draft-only output. Do not carry
an exploratory `LIMIT 1` into the final query unless the user requested one row
or a sample. If execution fails, re-ground the next attempt in catalog evidence
or a targeted probe.

Treat a `truncated` result as a sample. Never compute complete totals or other
final aggregates from truncated rows; perform those calculations in SQL.

Return:

- the answer or execution limitation;
- the final SQL;
- the Dataset, anchor, document, glossary, domain, or data-product sources used;
- probe findings that changed the decision;
- assumptions and unresolved ambiguity.

Separate facts from documentation, facts from catalog metadata, and your own
inferences; never present an inference as a fact.

In draft-only mode, omit execution but retain context discovery, verification,
targeted probes when needed, ambiguity handling, and source reporting.

Report any discrepancies, gaps, or missing metadata discovered during the
workflow via `note_metadata_observation` — this includes missing glossary
definitions, wrong or outdated descriptions, anchor-vs-catalog conflicts,
and missing column documentation. The tool is fire-and-forget and does not
block the answer.
