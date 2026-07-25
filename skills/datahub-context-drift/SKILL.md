---
name: datahub-context-drift
description: |
  Use this skill when the user suspects the documentation in DataHub no longer matches reality: a description that references a column the schema no longer has, a renamed field the docs never followed, a claimed upstream that is no longer in the lineage. Triggers on: "is this description still accurate", "did the docs keep up", "check for stale documentation", "this column was renamed", "the description mentions a field that doesn't exist", "audit descriptions against the schema", or any request about documentation that has drifted out of sync with the data.
user-invocable: true
min-cli-version: 1.4.0
allowed-tools: Bash(datahub *)
---

# DataHub Context Drift

You detect documentation that has stopped being true. Not documentation that is
missing — documentation that is present, well written, and wrong.

A worked example from public data: in February 2023 the NYC Taxi & Limousine
Commission renamed `airport_fee` to `Airport_fee` in its published trip records.
One letter. No error, no announcement. Every description, query and model that
spelled it the old way kept running and quietly stopped meaning what it said. A
coverage check scores that table perfectly — the description is there, the
columns are documented, nothing is missing.

---

## Multi-Agent Compatibility

Works across Claude Code, Cursor, Codex, Copilot, Gemini CLI, Windsurf and
others. The workflow (scan → propose → approve → write → verify) uses MCP tools
or the DataHub CLI; nothing here is agent-specific except the `allowed-tools`
frontmatter, which other agents can ignore.

**Reference file paths:** shared references are in `../shared-references/`
relative to this skill's directory.

---

## Not This Skill

| If the user wants to...                         | Use this instead   |
| ----------------------------------------------- | ------------------ |
| Find what is missing (no description, no owner) | `/datahub-audit`   |
| Add or update metadata they already decided on  | `/datahub-enrich`  |
| Explore lineage or dependencies                 | `/datahub-lineage` |
| Set up assertions or handle incidents           | `/datahub-quality` |
| Search or discover entities                     | `/datahub-search`  |

The distinction from `/datahub-audit` matters: that skill measures coverage —
what has not been written. This skill reads what _has_ been written and checks
whether it is still true.

---

## Read the description a human actually sees

An entity returned by `get_entities` can carry two descriptions:

- `editableProperties.description` — written through the UI or the API
- `properties.description` — supplied by ingestion

**The UI renders the editable one when it is set.** They can differ: a dbt
manifest description and a hand-edited one on the same dataset are both present
with different text. Read `editableProperties` first and fall back to
`properties`, or you will audit a description nobody is looking at.

---

## What counts as drift

For each dataset in scope:

1. **Broken field reference.** The description names an identifier the schema
   does not have. Look for a near-match first: a case variant (`airport_fee` →
   `Airport_fee`) or the same letters with underscores moved. A near-match is a
   rename, and it is the strongest signal available — assert it.
2. **Undocumented column on a documented table.** The table has a description
   but some columns have none. Only counts when the table itself is documented;
   a table with no documentation anywhere never started, it did not drift.
3. **Claimed source not in the lineage.** The description says "derived from X"
   or "sourced from X" and X is not among the actual upstreams.

## What does not count

Real descriptions are prose. They cite other tables, DataHub entity types,
placeholders like `table_name`, and domain jargon. If an unresolved identifier
has **no near-match in the schema**, do not call it drift — report it as
insufficient evidence and move on.

This costs you something: a column that was genuinely deleted, with no similarly
named replacement, reads as insufficient evidence rather than drift. Take that
trade. A report with false positives stops being read.

**Three verdicts, and the third one is not a failure:**

| Verdict                 | Meaning                                             |
| ----------------------- | --------------------------------------------------- |
| `DRIFT`                 | The description contradicts the schema or lineage   |
| `CURRENT`               | Checked, still accurate                             |
| `INSUFFICIENT_EVIDENCE` | Something looks off, but you cannot substantiate it |

---

## Step 1: Resolve scope

Ask for a domain, platform, or explicit URN list if the user did not give one.
Never scan the whole catalog silently — say how many datasets you are about to
read and confirm.

## Step 2: Gather both sides

For each dataset, read:

- the description (editable first, see above) — the **authored side**
- `list_schema_fields` — the **reality side**
- `get_lineage` upstreams, only if the description makes a source claim

Record which call produced each fact. Every finding you report must be traceable
to one of them; if you cannot point at the call, do not report the finding.

## Step 3: Report findings

For each finding state: the entity, what the description claims, what reality
shows, the verdict, and the suspected rename if there is one. Group by dataset,
order by verdict severity. Do not propose fixes yet.

## Step 4: Propose, and stop

Draft the corrected description. Show it as a diff against the current text.
Then stop and wait — writes are approval-mandatory.

**Never** write back without explicit approval for that specific text. Never
batch approvals across datasets. If the user approves and then edits your
wording, treat that as a new proposal needing fresh approval.

## Step 5: Write and verify

After approval, use `update_description`. Then **read it back** and confirm the
stored value matches what you wrote. A successful API response is not
confirmation — a write can return 200 and not land.

Report the outcome plainly, including a re-scan showing the finding is gone.

---

## Common Mistakes

| Mistake                                                             | Why it is wrong                                                                                      |
| ------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| Lowercasing both sides before comparing field names                 | Erases the exact difference that constitutes a case-only rename — the most common silent drift       |
| Reading only `properties.description`                               | The UI shows `editableProperties`; you audit text nobody reads                                       |
| Reporting every unresolved identifier as drift                      | Descriptions cite other tables and placeholders; false positives make the whole report untrustworthy |
| Flagging undocumented columns on a table with no description at all | That is missing documentation, not drift — use `/datahub-audit`                                      |
| Writing back without a read-back check                              | The API can accept a write that does not land                                                        |
| Treating `INSUFFICIENT_EVIDENCE` as a failure to be eliminated      | Abstaining on ambiguous cases is what keeps the confident findings believable                        |
