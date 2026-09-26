---
name: datahub-sql-workflow
description: Ground text-to-SQL work in DataHub catalog evidence. Use when a user asks to write, draft, debug, or execute SQL; answer a data question that requires SQL; calculate a metric; query named tables; or investigate SQL results with DataHub MCP tools available. Always begin with find_sql_context, even when the user already supplied tables or dataset URNs, and call inspect_tables_for_sql on the chosen tables before writing SQL.
license: Apache-2.0
compatibility: Requires the DataHub MCP tools find_sql_context and inspect_tables_for_sql plus the catalog tools (search, get_entities, list_schema_fields, grep_documents, search_documents); a SQL execution tool is optional
metadata:
  author: datahub
  version: "3.0"
---

# DataHub SQL Workflow

Ground every query in DataHub evidence. Two tools carry that evidence:

- `find_sql_context(question)` routes: it returns a card with the documents your
  organization wrote about the question, the candidate tables, and the saved
  query patterns that touch them.
- `inspect_tables_for_sql(table_urns, question)` constructs: for the tables you
  chose it returns the conventions analysts apply to them, the curated document
  for each table, and, when one fits, a worked example to adapt.

The catalog tools (`get_entities`, `list_schema_fields`, `search`) confirm the
physical shape: that a column exists, its type, the grain. Business documents
say what is correct; generated history says what analysts did; the catalog says
what is there. Rank them in that order when they disagree (section 4).

Require `find_sql_context` and `inspect_tables_for_sql`. If either is missing,
stop and ask the user to enable the DataHub MCP tools; do not fall back to other
discovery tools, local files, memory, or the web. Treat every other tool as
optional: when one is unavailable, say so and continue with the steps it does
not affect. Never replace missing evidence with a guess.

## 1. Call `find_sql_context` first and read the whole card

Call `find_sql_context(question=<the user's complete question>)` before any
other tool, even when the user names tables or supplies dataset URNs. Pass the
question as the user wrote it; do not shorten it to keywords.

The card has five parts. Read them in this order.

1. `authoritative_instructions`: groups of `{call, results}`. Each `call` is a
   `search_documents(...)` call that already ran, or a user-edited anchor
   instruction, and `results` are the documents it returned, each as the excerpt
   that best matches your question. These are your organization's own words
   about the question: join keys, latest-row rules, required filters, "do not
   use this table" warnings. Read every group before anything else.
2. `authoritative_instructions_note`: how the groups were built and how to go
   beyond them. Follow it.
3. `candidate_tables`: tables the evidence points at, each with `tier`
   (`blessed` or `reviewed` means a human verified it, `external` means it was
   imported from a modeling tool, `draft` is generated),
   `measures` (aggregations seen on the table; `best_match: true` marks the one
   closest to the question), `joins` (tables it is joined with in saved
   queries), `docs` (documents that name it) and `anchors` (saved patterns that
   use it). A table with `source: "catalog_search (no query evidence)"` came
   from a name match only.
4. `anchors`: compact saved query patterns, each with `kind` (`metric`,
   `model` or `tableset`), `base_table`, `tier`, `support` and a description.
   A generated (`draft`) anchor is evidence of practice, not a rule.
5. `documents`: more documents, grouped by the search call that found them,
   each as a short `preview`.

Every excerpt carries `[start-end]` character offsets and a `grep_documents`
continuation. When an excerpt leaves a needed detail open, fetch that document
by its URN with `grep_documents` or `get_entities`. Never re-run a search call
the card already shows. The card also searched the catalog for tables: do not
`search` for a table it already lists, and do not list domains, data products or
anchors with a wildcard query. Fetch at most three full documents; the card is
already large, and its excerpts are usually enough to choose tables. The usual
budget for a grounded query is the card, one `inspect_tables_for_sql` call, and
at most three document fetches; every extra call spends context the answer
needs.

## 2. Choose the tables

Name every table the answer needs, then confirm each one appears in evidence
you retrieved: a card document, `candidate_tables`, an anchor, or a catalog
lookup. A table that appears in none of them is unverified; say so rather than
inventing its columns.

- **Follow redirects.** When a document says to prefer a different table for
  the concept you are querying, use that table as the primary candidate and
  read its documentation too. Routing advice states the default lane; it does
  not override an explicit requirement in the question (freshness, a named
  table, a grain the preferred table cannot serve). When the question forces a
  departure, say so and give the reason.
- **Take the governed table at the requested grain.** When a documented table
  already provides the requested measures at the requested grain, use its
  native columns instead of reconstructing them from lower-grain tables.
- **The question's grain decides between canonical sources.** When two curated
  documents both claim to be canonical, the one whose stated grain matches the
  grain the question asks for wins. Aggregate from a finer table only when no
  document matches the requested grain, and say so.
- **Take literals from the question, not from saved queries.** A literal id or
  value inside a saved query or notebook is one analyst's shortcut; do not copy
  it into a filter. Use the value the question gives, or a value a curated
  document or a declared value domain (section 3) confirms.
- **Do not simplify away a canonical join.** Treat the tables and joins of the
  closest saved pattern as a checklist: investigate an omitted join before
  dropping it. A table can be canonical for one purpose without being canonical
  for every column it carries; do not take an entity label or lifecycle field
  from a bridge or lookup table when evidence assigns it to the entity table.
- **Prefer governed surfaces.** Prefer a table inside a matching domain or data
  product over an identically named table outside them.
- **Metric tables over same-named attributes.** When two candidates carry the
  same metric name, prefer a dedicated metric or fact table over a same-named
  attribute column on an entity table, and present both if the tie survives.

When the card is thin (no authoritative document, only `draft` or
catalog-search candidates) or candidates disagree, establish the business
meaning before choosing: `search` with an `entity_type` filter for a named
glossary term, domain or data product that the question or a document mentions
and the card does not resolve; `get_entities` on the candidate URNs the card
left ambiguous, to read descriptions, ownership, tags, terms and table type as
intent signals; and `search_documents` only for an angle no card call covered,
worded around the
question's measures and grain in column-name style (`order_total units_sold per
region daily`) with `filter='subtype != "Semantic Anchor"'`. If the negated
filter returns nothing, re-run without the filter and skip anchor hits. When no
business definition exists, state the gap and ask the user; do not fill it with
an inferred interpretation.

Confirm columns and grain with targeted `list_schema_fields` calls when the
card and documents leave them open, and always before joining tables whose keys
no document states. Verify every join key on both sides; do not add a
speculative inner join that could drop unmatched rows. Confirm that an "all X"
question is not answered from a segmented subset.

## 3. Call `inspect_tables_for_sql` on the chosen tables, once

Before writing SQL, call
`inspect_tables_for_sql(table_urns=[<every table the SQL will SELECT FROM or JOIN>], question=<the user's complete question>)`
in one call, with the full dataset URNs from the card or the catalog. If a
document redirected you to a new table after the call, inspect that table too.
Skipping this call is the most common reason a query misses the filters
analysts always apply. The response has these parts:

- `instructions`: conventions for the tables you asked about. Follow them.
- `tables[]`, one per table with any known conventions:
  - `observed_guards`: predicates analysts apply on nearly every query of the
    table (soft-delete, latest-version, active-state, tenant scope), each with
    `support_pct`. Apply the ones that fit the question; skip one only when the
    question or a curated document says otherwise, and say which you skipped
    and why. Silently dropping a soft-delete, latest-version or active-state
    guard is the most common way the query is wrong.
  - `value_domains`: `declared` values (from tests, assertions and accepted
    values) and `observed` values (from past `WHERE` clauses) per column. Take
    literals from here, preferring declared over observed, and keep their exact
    type, casing and whitespace. Observed values are samples, not the full set.
  - `date_shapes`: how analysts filter dates on the table. Apply the one that
    fits a point-in-time or snapshot question.
  - `curated_documents`: the documents your organization wrote about this
    table, ranked for your question, each as an excerpt with `chars_shown` of
    `chars_total`. They are authoritative for the table's grain, required
    filters and column meanings. When an excerpt is cut before the rule you
    need, read the rest with `grep_documents` on its URN.
- `tables_without_advisory`: tables with no known conventions. That means no
  evidence, not "no filters": disposition the table's lifecycle and validity
  columns yourself from `list_schema_fields`.
- `worked_example`: at most one saved pattern over these same tables, with its
  `relevance`, `tables` and rendered `patterns`. It is a construction template:
  adapt its grain and filters to the question rather than copying it, and
  replace `<value>` and `<analyst picks: ...>` placeholders with literals chosen
  for this question.
- `message`: present when more than eight tables were passed; only the first
  eight were inspected. Pass just the tables the SQL uses.

If a `draft_sql_for_tables` tool is also present, you do not need it. It
predates this workflow; draft the SQL yourself from the evidence above.

## 4. When evidence disagrees

Rank the sources:

1. Human guidance: `authoritative_instructions`, `curated_documents`, and
   `blessed` or `reviewed` anchors. An anchor is distilled from what analysts
   ran, so a repeated mistake becomes a pattern; a curated document is the
   organization stating what is correct. When a document and a generated
   pattern differ on any element (table, column, join key, filter, the order of
   deduplication and filtering, units), follow the document.
2. Generated evidence: `draft` anchors, `observed_guards`, observed value
   domains and date shapes, the `worked_example`.
3. The catalog for physical shape. When a document names a column the schema
   does not have, or the definition's filter cannot be expressed, state the
   disagreement and resolve it before writing SQL. Never silently pick one.
4. Your own assumptions, stated as such.

This applies to a pattern's mechanics, not only its table choice: if a document
names a native column for a value the pattern derives, select the documented
column; if it states an order between operations, use that order; if it states
a unit or conversion the pattern omits, apply it. Do not invent `COALESCE`
fallbacks or other derivations when documentation is silent; nullable lifecycle
fields can encode state.

## 5. Probe with read-only queries when you can execute

This section applies only when a SQL execution tool is available. Without one,
check `get_entities` for data profiles or sample data on the candidate tables,
then continue to section 6 and record the assumptions a probe would have
settled.

Run a probe only when its result could change the table, join, filter, grain or
time-window decision; skip it when metadata is already decisive. Start with the
cheapest row-shape probe:

```sql
SELECT <needed_columns>
FROM <fully_qualified_table>
LIMIT 1
```

Use named columns when known and `SELECT *` only when metadata cannot identify
the relevant fields. Other minimal probes: `COUNT(*)` or small grouped counts
for filter viability and grain; `COUNT(DISTINCT key)` and duplicate checks for
uniqueness; null counts or small distributions for candidate fields; `MIN` and
`MAX` timestamps for coverage and freshness; matched and unmatched counts for
join coverage. Select only required fields, apply the known guards, constrain
verified partitions. Never use a probe to manufacture a business rule. Treat
empty results, unexpected magnitudes, errors and timeouts as evidence about
access, freshness, schema drift or table suitability.

When authoritative context and the data drift apart (the definition's filter
returns nothing, a named column is missing or behaves differently, the answer
needs an assumption the definition does not cover), probe only to characterize
the difference, then stop before the final query: quote the definition, name
the drift in one sentence, offer two or three plain-language interpretations,
and ask which matches the user's intent. Allow at most three diagnostic rounds,
each testing a new hypothesis.

## 6. Draft and verify the SQL

Draft the SQL yourself from the evidence. Start from the `worked_example` or the
closest saved pattern when one fits, and rewrite it for this question's grain,
filters and output. Before you return it, check every item:

- every table the SQL reads was inspected in section 3 and is cited;
- every predicate traces to the question, a curated document, an observed
  guard or date shape, a verified join, or a probe finding you will report;
  every guard the pattern or documents apply is carried at the same scope, or
  its omission is recorded with a reason;
- every literal comes from the question, a value domain or a document, never
  from a saved query's sample values;
- every join key is verified on both sides and each join is forced by a
  required output column;
- the aggregation grain matches the question: a present-tense or point-in-time
  question pins to the latest valid snapshot and returns one result, and a trend
  or per-period breakdown appears only when the question asks for one;
- the query is the minimal one that answers the question.

## 7. Execute safely and report

Execute only a single read-only `SELECT` statement, including read-only CTEs.
Reject DDL, DML, stored procedures and side-effecting functions. Execute the
final query unless the user asked for a draft only. Do not carry an exploratory
`LIMIT 1` into the final query unless the user asked for one row or a sample.
If execution fails, re-ground the next attempt in catalog evidence or a probe.
Treat a `truncated` result as a sample: compute totals and other final
aggregates in SQL, never from truncated rows.

Return:

- the answer, or the execution limitation;
- the final SQL;
- every source the answer relies on, each as a markdown link
  `[display name](urn:li:...)` using the URN a tool returned: the dataset URN
  (`urn:li:dataset:...`) of every table the SQL reads, plus the URN of each
  curated document, glossary term, domain or data product you relied on. A
  document about a table is a separate entity from the table; cite both. When
  the same table exists as a modeling-tool dataset (for example dbt) and as a
  warehouse dataset, the SQL reads the warehouse table: cite the warehouse
  dataset URN, looking it up with `search` when the card offered only the
  modeling copy, and name the modeling copy as an alternate;
- probe findings that changed a decision;
- any table used without corroborating evidence;
- assumptions, guards you skipped, and unresolved ambiguity.

Separate facts from documentation, facts from catalog metadata, and your own
inferences; never present an inference as a fact. In draft-only mode, omit
execution but keep every other step, including source reporting.

When `note_metadata_observation` is available, report discrepancies and gaps you
found (a missing glossary definition, a wrong or outdated description, a
document that contradicts the schema or an anchor, missing column
documentation) through it. It is fire-and-forget and does not block the answer.
