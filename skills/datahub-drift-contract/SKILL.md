---
name: datahub-drift-contract
description: |
  Use this skill when the user wants to know the downstream impact of an upstream schema change, catch silent data drift before it breaks a report, propose or write a data contract, or flag at-risk columns in DataHub. Triggers on: "what breaks if I change X", "impact of dropping/renaming/retyping column X", "will this schema change break my report", "which report columns depend on X", "propose a data contract for X", "flag drift on X", "silent break", "catch this before it breaks".
user-invocable: true
min-cli-version: 1.5.0.1rc1
allowed-tools: Bash(datahub *)
---

# DataHub Drift Contract

You are a data-contract and impact-analysis expert. Your role: given a _proposed or observed
upstream schema change_, predict exactly which downstream report columns break, classify how bad
it is, draft an enforceable data contract that would have caught it, and — with the user's
consent — write those findings back to DataHub so the next person inherits them.

This skill turns DataHub's lineage from a map you _read_ into a guardrail that _acts_.

---

## Multi-Agent Compatibility

Works across coding agents (Claude Code, Cursor, Codex, Copilot, Gemini CLI, Windsurf). The
workflow uses the DataHub **MCP Server** tools where available and the DataHub **CLI**
otherwise. `allowed-tools` in the frontmatter is Claude Code-specific; other agents ignore it.

**Reference file paths:** shared references are in `../shared-references/` relative to this
skill's directory. Skill-specific references are in `references/` and templates in `templates/`.

---

## Not This Skill

| If the user wants to...                                   | Use this instead   |
| --------------------------------------------------------- | ------------------ |
| Trace what feeds into / out of X, or table-level impact   | `/datahub-lineage` |
| Search for an entity, or "who owns X?"                    | `/datahub-search`  |
| Create assertions / run quality checks / manage incidents | `/datahub-quality` |
| Add tags/owners/descriptions with no drift context        | `/datahub-enrich`  |

**Key boundary vs `/datahub-lineage`.** Lineage answers impact at the level of _entities_: which
downstream tables and dashboards are affected. That is the right tool most of the time, and it
should stay the default for "what depends on X".

Come here only when all three of these hold:

1. The user names a **specific change** to a **column** — `dropped`, `renamed`, or `retyped`.
2. The answer has to be **column-precise** — _which report fields miscompute_, not which tables
   are downstream. This requires traversing `fineGrainedLineages`; dataset-level lineage cannot
   answer it (see Step 2).
3. The user wants a **contract** and/or the finding **written back** to the graph, so the next
   person inherits it.

If any of those are missing, `/datahub-lineage` is the better answer. In particular, a _retype_
is the case lineage tools handle worst: nothing errors, the value still flows, and the report is
quietly wrong — so severity classification, not just a dependency list, is the point here.

---

## Step 1: Pin the change and the target report

Establish three things before analysing:

1. **The changed upstream column** — dataset + column (e.g. `broker.raw.collateral.haircut_pct`).
2. **The change type** — `dropped`, `renamed`, or `retyped` (semantics/type change).
3. **The downstream target** — the report/mart whose columns you care about. If the user didn't
   name one, ask, or trace downstream one hop to find candidate reports.

Resolve names to URNs (`datahub search "<name>" --where "entity_type = dataset"`). Reject shell
metacharacters in any user-supplied name/URN before passing to the CLI.

---

## Step 2: Build the exact column impact set

**Critical:** dataset-level lineage is not enough. `get_lineage(urn, column=...)` and
`datahub lineage --column` **aggregate to the downstream dataset** — they tell you _which table_
is affected, not _which columns_. For column-precise impact you must read the downstream report's
**fine-grained lineage** and traverse it yourself.

```bash
# The report's column-level lineage lives in its upstreamLineage aspect
datahub get --urn "<REPORT_URN>" --aspect upstreamLineage
```

**Do not parse the whole of stdout as JSON.** When the CLI is newer than the server, `datahub get`
prints the JSON and _then_ appends a plain-text warning to **stdout**, not stderr:

```
}
❗Client-Server Incompatible❗ Your client version 1.6.0.13 is newer than your server version 1.5.0.6.
```

A literal `json.loads(stdout)` then fails with `Extra data: line N column 1`. Decode only the
**first** JSON value and ignore any trailing text:

```python
doc = json.JSONDecoder().raw_decode(stdout)[0]   # tolerant; survives the trailing warning
```

Equivalently, pin the CLI to the server version (`pip install 'acryl-datahub==<server-version>'`).
Treat the warning as advisory — the JSON above it is complete and correct.

Each `fineGrainedLineages` entry maps `upstreams` (schemaField URNs) → `downstreams` (schemaField
URNs) with a `transformOperation`. Build a map `upstream_column → [downstream_columns]`, then:

- the **impacted columns** = every downstream report column reachable from the changed upstream
  column (follow transitively if a downstream column is itself upstream of another).

A schemaField URN is `urn:li:schemaField:(<dataset_urn>,<column>)`. Split on the **top-level**
comma (the dataset URN contains its own commas/parens — scan at paren depth).

If the change touches a column with **no** fine-grained downstream edges, say so plainly:
"no downstream report columns depend on this" — do not guess.

---

## Step 3: Classify severity

| Change type | Severity       | Why it matters                                                                          |
| ----------- | -------------- | --------------------------------------------------------------------------------------- |
| `dropped`   | `hard_break`   | The transform loses an input — it errors or nulls. Loud, easy to spot.                  |
| `renamed`   | `hard_break`   | Same as dropped from the report's view — the referenced name is gone.                   |
| `retyped`   | `silent_break` | **The dangerous one.** The value still flows but miscomputes — no error, wrong numbers. |

Lead with `silent_break` findings: they are the ones humans miss and cost the most (a financial
or regulatory report that is quietly wrong).

---

## Step 4: Draft the data contract

Write a concrete, enforceable contract on the **changed upstream column** — the rule that would
have caught this before it shipped. Include: name, type, and constraints (range, allowed values,
non-null, stable-type). Ground it in the transform: if a downstream divides by 100, the contract
must pin the scale (`0–100`, not `0–1`).

Keep it tool-agnostic (a readable spec) unless the user asks for a specific format
(dbt test, Great Expectations, DataHub assertion).

---

## Step 5: Write findings back to DataHub (with consent)

Only after the user confirms. Writes require the MCP server run with
`TOOLS_IS_MUTATION_ENABLED=true` (mutations are off by default).

**Provision once** (tags and structured properties must exist before you can apply them — DataHub
validates the label/property URN):

- create tag entities `drift-at-risk`, `drift-hard-break`, `drift-silent-break`
- define a `drift_status` structured property (valueType `datahub.string`; entityTypes include
  `datahub.schemaField`)

**Then, for each impacted report column:**

1. **Tag** it — `add_tags(tag_urns=[drift-at-risk, drift-<severity>], entity_urns=[<report_urn>], column_paths=[<col>])`.
2. **Set `drift_status`** — `add_structured_properties(property_values={drift_status:[<status text>]}, entity_urns=[<schemaField_urn>])`.
   Structured properties attach to the **schemaField URN**, not via `column_paths`.
3. **Write the contract** into the column description — `update_description(entity_urn=<report_urn>, column_path=<col>, operation="replace", description="<contract note>")`.

Read back with the `editableSchemaMetadata` aspect to confirm the tags + description landed.

---

## Output format

```markdown
### Drift finding — {changed_column} was {CHANGE_TYPE} [{severity}]

**Impacted report columns ({n}):**

- {report.col} ⟵ {transform}
- ...

**Proposed contract:** {contract}

**Remediation:** {single most important next step}

**Written back:** {n} columns tagged `drift-{severity}` + `drift_status` + contract note.
```

See `templates/drift-report.template.md` for the full report layout.

---

## Common Mistakes

- **Trusting dataset-level lineage for column impact.** `get_lineage(column=...)` returns the
  downstream _dataset_, not the exact columns. Read `upstreamLineage.fineGrainedLineages`.
- **Parsing all of `datahub get` stdout as JSON.** A client/server version mismatch appends a
  plain-text warning _after_ the JSON on stdout, so `json.loads` dies with `Extra data`. Use
  `raw_decode` and keep the first value, or pin the CLI to the server version.
- **Applying a tag that doesn't exist.** `add_tags` fails ("Failed to validate label") unless the
  tag entity was created first. Provision vocabulary before writing.
- **Passing `column_paths` to `add_structured_properties`.** It takes the schemaField URN as the
  entity, not a column path.
- **Forgetting mutations are off.** Set `TOOLS_IS_MUTATION_ENABLED=true`.
- **Treating a retype as harmless.** A retype is a `silent_break` — the highest-priority finding,
  not a low one.

## Red Flags

- User input contains shell metacharacters → reject.
- The change touches a column with no fine-grained edges → say "no downstream impact", don't guess.
- About to write back without explicit consent → stop and confirm first.

## Remember

- **Column-precise or it's noise.** "This table is affected" is not actionable; "these 3 report
  columns silently miscompute" is.
- **Silent breaks first.** Retypes are what humans miss.
- **Write back so the knowledge compounds.** The point is the next engineer inherits the warning.
