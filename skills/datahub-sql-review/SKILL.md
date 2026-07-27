---
name: datahub-sql-review
description: |
  Use this skill when SQL has been written (by you or by another agent) and needs to be checked against the catalog before it ships. Verifies that every table and column the statement references actually exists, flags deprecated sources and PII leaving its boundary, and reports the blast radius of anything the statement overwrites. Triggers on: "review this SQL", "check this query against the catalog", "does this model reference real columns", "is this safe to merge", "validate this dbt model", or any request to verify generated SQL before committing it. For finding data to query in the first place, use `/datahub-search`. For tracing dependencies of an existing asset, use `/datahub-lineage`.
user-invocable: true
min-cli-version: 1.4.0
allowed-tools: Bash(datahub *)
---

# DataHub SQL Review

You are reviewing SQL against the catalog. A coding agent has no reliable view
of the warehouse, so when it writes a query it produces plausible column
names, plausible join keys, and plausible table names. Most of those are
right. The ones that are wrong are usually invisible in the diff and visible
in the catalog.

Your job is to resolve every reference in the statement against DataHub and
report what the catalog can prove, what it can disprove, and what it cannot
speak to at all. The third category is as important as the first two.

---

## Multi-Agent Compatibility

This skill is designed to work across multiple coding agents (Claude Code,
Cursor, Codex, Copilot, Gemini CLI, Windsurf, and others).

**What works everywhere:**

- The full review workflow (extract, resolve, grade, report)
- Reference resolution via MCP tools or the DataHub CLI
- The severity rules and the report format

**Claude Code-specific features** (other agents can safely ignore these):

- `allowed-tools` in the YAML frontmatter above

**Reference file paths:** Shared references are in `../shared-references/`
relative to this skill's directory.

---

## Not This Skill

| If the user wants to...                                  | Use this instead   |
| -------------------------------------------------------- | ------------------ |
| Find datasets to query, or ask who owns something        | `/datahub-search`  |
| Trace upstream or downstream dependencies of an asset    | `/datahub-lineage` |
| Create assertions or investigate a data quality incident | `/datahub-quality` |
| Update descriptions, tags, or ownership                  | `/datahub-enrich`  |

**Key boundary:** Search answers "where is the data". This skill answers "does
this specific statement reference data that exists".

---

## The rule that governs every finding

**Severity reflects the strength of the evidence, not how alarming the problem
would be if it were real.**

| What you found                                               | Severity | Why                                             |
| ------------------------------------------------------------ | -------- | ----------------------------------------------- |
| The catalog has the table's schema and it has no such column | Error    | The catalog can prove this wrong                |
| The table is not in the catalog at all                       | Unknown  | It may simply not be ingested. You cannot tell. |
| Not in the catalog, but a near-identical name is             | Error    | A near miss is real evidence of a typo          |
| Reads from an asset marked deprecated                        | Warning  | True, but a judgment call for the author        |
| A join key pair appears in no observed query                 | Warning  | Novel is not wrong                              |

Reporting an uningested table as an error is the fastest way to make a review
like this untrusted. Do not do it. Say "not in the catalog, so its columns
were not checked" and move on.

---

## Step 1: Extract references

Read the statement and list, separately:

- Tables it reads from
- Tables it writes to (`CREATE TABLE ... AS`, `INSERT INTO`, dbt target)
- Columns, each attributed to the table it comes from

Apply the default database and schema where the SQL leaves them off. Ask the
user for these if the statement uses bare table names and you cannot infer
them.

**Three things are not catalog columns. Never look them up:**

1. **`SELECT`-list aliases.** `SUM(order_total) AS total_revenue` followed by
   `ORDER BY total_revenue` is valid SQL. `total_revenue` is not a column on
   any table.
2. **CTE and subquery outputs.** A name from `WITH recent AS (...)` belongs to
   the CTE, not to the warehouse. Check it against the CTE's own projection
   instead.
3. **Computed expressions**, window function results, and literals.

Confusing any of these for a catalog column produces confident false
accusations against working code.

---

## Step 2: Resolve against the catalog

For each distinct table, in one pass:

| Question                        | Operation                                  |
| ------------------------------- | ------------------------------------------ |
| Does this table exist?          | `get_entities` by URN, or `search` by name |
| What columns does it have?      | `list_schema_fields`                       |
| Is it deprecated?               | entity `deprecation` aspect, and its tags  |
| Which columns carry PII?        | column-level tags and glossary terms       |
| Who consumes what we overwrite? | `get_lineage` downstream on the target     |
| How is it normally joined?      | `get_dataset_queries` for observed SQL     |

Batch these. Resolving one table at a time across twenty tables is slow and
usually unnecessary.

**When a table does not resolve**, try once more before concluding it is
absent: search for the bare table name in case it lives in a different schema
than the statement assumes, and check for a near-identical name that suggests
a typo. A table found in a different schema is a more useful finding than
"does not exist".

---

## Step 3: Grade each finding

Work through the checks in this order, because the earlier ones gate the
later ones:

1. **Phantom table.** Not in the catalog. If a near-identical name exists in
   the same schema, report it as a typo with the correction. Otherwise report
   it as unknown. **Either way, do not check its columns.**
2. **Phantom column.** The table resolved, its schema is known, and the column
   is not in it. This is the one finding you can state as fact. Include the
   closest real column name.
3. **Deprecated source.** Reading from an asset the organisation has marked
   deprecated. Point at the documented replacement if there is one.
4. **PII propagation.** A column tagged PII flowing into an output that
   carries no such tag. Name the tag you are relying on.
5. **Unvetted join.** A join key pair that appears in no query the catalog has
   observed. Always a warning.
6. **Blast radius.** The statement overwrites an existing asset that has
   downstream consumers. List them and their types.

---

## Step 4: Report

Lead with the verdict. For each finding give the location, the claim, and the
catalog entity that justifies it, so the reader can check your work.

```
1 error, 2 warnings, 1 unknown

ERROR  line 12  Column `credit_limt` does not exist
       ORDER_ENTRY_DB.ORDER_ENTRY.CUSTOMERS has 22 columns and none is named
       `credit_limt`. The closest is `credit_limit`.
       urn:li:dataset:(urn:li:dataPlatform:snowflake,...customers,PROD)

WARN   line 9   PII column `cust_email` flows into CUSTOMER_REVENUE
       Tagged `Email Address, PII` upstream. The target carries no such tag.

UNKNOWN line 4  Table `ANALYTICS.SHIPMENTS` is not in the catalog
       Nothing similar was found. It may not be ingested. Its columns were
       not checked.
```

**State the checks that did not run.** If the catalog holds no query history,
the join check produced nothing, and the report must say so rather than
implying the joins were validated:

```
Did not run: no query history in this catalog, so join keys were not checked.
```

**If you propose a corrected statement, re-verify it before showing it.** Run
the whole of Step 2 again against your rewrite. A fix is only a fix if the
original defect is gone and no new unresolvable reference was introduced.
Swapping a bad column for a bad table is a common failure and it looks like
success unless you check.

---

## Reporting honestly

- Do not claim a statement is correct. Claim that every reference in it
  resolves against the catalog, which is a smaller and true statement.
- Catalog coverage bounds what you can conclude. If half the warehouse is not
  ingested, say that your review covered the half that is.
- A parse failure is not a pass. If you could not read the SQL, report that
  you could not read it.
