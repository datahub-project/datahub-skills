---
name: datahub-repair-boundary
description: |
  Use this skill when an agent is about to generate or apply a repair for a schema change, and needs to decide whether the metadata actually supports doing so. Triggers on: "generate the migration", "fix the downstream models", "auto-repair this rename", "apply the schema change", "patch the consumers", "can I automate this change", or any request where code will be written on the strength of lineage. Not for assessing whether a change is risky; for deciding whether a repair may be emitted at all, and naming the condition when it may not.
user-invocable: true
min-cli-version: 1.5.0.1rc1
allowed-tools: Bash(datahub *)
---

# DataHub Repair Boundary

You are deciding one thing: **may an automated repair be generated for this change, or must it stop and name why.**

Impact analysis tells you what a change reaches. It does not tell you whether you are entitled to write code against what it reached. Those are different questions, and conflating them is how automation ships a repair that is syntactically perfect and semantically wrong.

This skill is the second question. Every rule below exists because the naive answer looks like success: the tool finishes cleanly, reports a repair, and leaves something broken that nobody notices until a dashboard is wrong.

---

## Multi-Agent Compatibility

Designed to work across Claude Code, Cursor, Codex, Copilot, Gemini CLI, Windsurf and others.

**What works everywhere:** the full decision procedure, every blocking condition, and the write-back shape.

**Claude Code specific** (other agents can ignore): the `allowed-tools` frontmatter above.

**Reference paths:** shared references are in `../shared-references/` relative to this skill's directory.

---

## Not This Skill

| If the user wants to...                                    | Use this instead                  |
| ---------------------------------------------------------- | --------------------------------- |
| Trace what feeds into or out of an asset                    | `/datahub-lineage`                |
| Know who owns an asset, or what it is                       | `/datahub-search`                 |
| Add or update descriptions, tags, owners                    | `/datahub-enrich`                 |
| Create assertions, run quality checks, manage incidents     | `/datahub-quality`                |
| Judge whether a change is risky before merge                | an impact or change-safety skill  |

**Key boundary.** Impact analysis answers "what does this reach, and how bad would it be". This skill answers "given what the graph can and cannot prove, am I allowed to write the repair, and if not, which named condition blocked me".

A risk verdict and a generation permit are not the same artifact. A change can be low risk and still be unrepairable automatically, because the metadata does not identify what to edit.

---

## The procedure

Run these in order. Any block is terminal for automatic repair: report the condition, hand back the candidates you found, and stop. Do not downgrade a block into a warning and continue.

1. Confirm the source change against live schema.
2. Resolve every reachable consumer, and separate proven from merely reachable.
3. Map each consumer you intend to edit onto exactly one implementation.
4. Check the destination for collision.
5. Check the SQL shape of each file you would rewrite.
6. Generate only for what survived, then prove the generated code builds.
7. Re-read the graph before any external action.
8. Write back a decision that says what was reviewed, not what was merged.

---

## Blocking conditions

### 1. One catalog asset, two implementations

**What the graph gives you:** a downstream dataset URN.

**Why that is not enough:** more than one file in the repositories you were given can claim to implement it. Nothing in the metadata ranks them.

**Do:** stop. Return every candidate you discovered, with the evidence that made each one a candidate, and let a human select. Bind the selection to the campaign so the rejected candidate stays in the record.

**Do not:** pick the first match, the highest scoring match, or the one whose path looks most plausible. A wrong pick edits a file nobody asked you to touch and leaves the real consumer broken.

```text
BLOCKED  ambiguous-mapping
  asset: urn:li:dataset:(urn:li:dataPlatform:dbt,customer_identity_export,PROD)
  candidates:
    dbt_operations_primary/models/customer_identity_primary.sql
    dbt_operations_shadow/models/customer_identity_shadow.sql
  required: human selection from discovered candidates
```

### 2. Reachable is not used

**What the graph gives you:** asset-level reachability to a dashboard, a chart, or a downstream table.

**Why that is not enough:** reachability says a path exists. It does not say the asset reads the column you are changing. Column-level lineage says that; asset-level lineage does not.

**Do:** separate the two populations explicitly. Repair only where column evidence exists. Route the rest to manual review with the reason attached.

**Do not:** infer usage from reachability and generate a patch anyway. This is the single most common way to produce a confident, wrong edit, because the output looks identical to a correct one.

### 3. The destination already exists

**What the graph gives you:** the current schema.

**Why it matters:** if the target column name is already present, a rename does not create a new column, it collides with a live one. Downstream models then silently point at different data, and every test still passes.

**Do:** check the destination before planning anything, and refuse on collision.

**Do not:** proceed because the source column also exists and the rename "looks" valid in isolation.

### 4. A green build that ran nothing

**What the tool gives you:** an exit code.

**Why that is not enough:** a build command with a selector that matched nothing exits successfully. So does a build that ran every model you expected. Exit status cannot distinguish them.

**Do:** declare the node set you expect before running, and assert the run produced exactly that set. Treat an empty or short run as a failure.

**Do not:** treat exit zero as proof of execution. A green build that proved nothing is not evidence.

```text
FAILED  empty-execution
  expected nodes: model.project.orders_daily, model.project.customer_revenue
  executed nodes: (none)
  exit code: 0
```

### 5. The graph moved after you planned

**What the graph gives you:** an answer at read time.

**Why that is not enough:** a plan built at T0 is executed at T1. Between them the lineage can change, and a cached read can keep serving the old shape. An agent that writes to four repositories on the strength of a stale read has no way to notice.

**Do:** re-read the context immediately before any external action, and compare against what you planned from. Where the interface offers a cache-bypassed read, take it and compare the two. Disagreement is a stop condition, not a retry.

**Do not:** trust a single read taken at planning time, and do not treat a disagreement as transient.

> On DataHub specifically, lineage reads through the MCP server currently issue
> `searchAcrossLineage` without `skipCache`, and the exposed tool schema has no
> cache-bypass option (verified against `tools/lineage.py` on 2026-08-09). Until
> that lands, an independent uncached read is the only way to detect this class
> of drift.

---

## SQL scope preflight

Before rewriting a single identifier in a file, decide whether you can prove which relation owns the column. If you cannot, refuse the file rather than guess.

Refuse when the statement contains any of:

- a join, so a bare column could belong to either side
- a CTE, so the name may be defined out of view
- a set operation, so more than one projection is in play
- a subquery or nested statement
- a lateral relation
- more than one top-level relation
- anything that is not a plain `SELECT`, since `UPDATE`, `INSERT`, `DELETE` and
`MERGE` introduce their own relation scoping

Preserve rather than rewrite:

- string literals
- comments
- dollar-quoted bodies
- templating expressions such as Jinja

**Why narrow beats clever.** A parser that understands the whole dialect is better if you have one. Absent that, a conservative lexical rewrite behind a structural ownership check is defensible, because everything it cannot prove it declines instead of approximating. Repair the narrow case, hand back the rest.

---

## What to write back

Write the decision, not the outcome.

- Record `approved-for-review`, never `approved-to-merge`. Merging is a human
act and the record should not imply otherwise.
- Bind the decision to a hash of the exact plan it approves, so it cannot be
read as approving a later one.
- Read every value back through a **fresh** client before treating the write as
done. A write is acknowledged before the search index reflects it, so read back URN-direct rather than through search.
- Keep the rejected candidates and the manual-review population in the record.
What was declined is evidence; dropping it makes the run unauditable.

---

## Honest limits

State these rather than implying otherwise.

- **Absence from the graph is not proof of absence.** An asset with no recorded
lineage may still have consumers. Say so in the output.
- **Column-level evidence is a floor, not a guarantee.** It proves a column is
referenced, not that a rename is semantically safe for every reader.
- **An offline re-verification of captured evidence** proves internal
consistency. It does not establish that any external service is currently reachable, or that the captured evidence was true when captured.

---

## Where this came from

Distilled from RippleProof, a bounded PostgreSQL column-rename agent built for the Build with DataHub Agent Hackathon. Every condition above is one it refuses on, and the refusals are measured rather than asserted: a deterministic corpus of 14 cases, 8 of which exist only to check that it still declines, producing 0 false repairs. A false repair is any automatic plan produced for a case declared to require human review.

The corpus and one full captured campaign, including three refusals in a single run, are readable at <https://itxcrusher.github.io/ripple-proof/examples/>. Source: <https://github.com/itxcrusher/ripple-proof>.
