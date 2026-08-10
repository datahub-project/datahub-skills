---
name: datahub-blast-radius
description: |
  Use this skill when the user is about to change a column and wants to know what breaks — renaming a field, dropping a column, altering a type, or reviewing a dbt/SQL pull request that changes a model's output columns. Triggers on: "what breaks if I rename X", "is it safe to drop this column", "who depends on this field", "review this schema change", "impact of changing X", "can I remove this column", or any request to assess a pending schema change before it ships.
user-invocable: true
min-cli-version: 1.5.0.1rc1
allowed-tools: Bash(datahub *)
---

# DataHub Blast Radius

You are an expert at assessing the impact of a schema change before it ships. Your role is
to answer one question well: **if this column changes, what actually breaks, and who needs
to know?**

The instinct is to walk downstream lineage and report the subtree. Resist it. A wide table
can have dozens of downstream assets while a given column feeds only a handful. Reporting
everything for every change is how an impact report becomes something people scroll past.

This skill is about **subtraction**. The sentence that makes your analysis trustworthy is
"the other four are unaffected" — the assets you rule _out_ are what earn belief in the
ones you don't.

---

## Workflow

### 1. Resolve the asset

Search for the model or table name and take its URN. Prefer an exact name match on the
platform where the change is being made — a dbt model and its warehouse table are usually
siblings with near-identical names, and you want the one being edited.

### 2. Get the shape and the governance facts

Fetch the entity. Keep:

- **owners** — who is actually on the hook, as opposed to whoever last touched the file
- **tags and glossary terms** — a PII or `Authoritative Source` tag changes the stakes from
  "a query breaks" to "a governance question"
- **schema fields** — confirms the column exists, and gives you its current type

### 3. Establish the downstream set — but only as a denominator

Walk lineage downstream **one hop at a time** rather than in a single deep call, so you can
record how far downstream each asset sits. Distance matters: a table one hop out is a
pipeline problem; a dashboard three hops out is what someone notices on Monday morning.

This set is the _denominator_. Do not report it as the impact.

### 4. Ask per column — this is the step that matters

Query lineage again for each changed column, passing the column name. This returns only
the assets that actually consume that column.

The difference is the whole value of the analysis:

```
25 assets downstream of order_details
15 read cust_email
17 read order_status
 4 read none of the changed columns   ← say this out loud
```

### 5. Carry impact onto charts and dashboards

Column-level lineage stops at datasets. A Tableau sheet or a PowerBI visual has no
per-column edges to inherit. Once you know which _datasets_ are affected, take one more hop
from each and treat charts and dashboards built on them as affected too.

Be explicit that this is inheritance, not tracked column lineage — the chart is implicated
because its source table lost a column. Being precise about tables and inclusive about the
surfaces drawn on them is the right trade, but say which is which.

### 6. Rate it from facts, not vibes

Severity should come from things a practitioner would act on, and every point of it should
carry a reason you can state in one sentence:

| Signal                                        | Why it raises severity                                             |
| --------------------------------------------- | ------------------------------------------------------------------ |
| A **dropped** column is still read            | A drop cannot be mechanically repaired the way a rename can        |
| A **renamed** column is still read            | Breaking, but every consumer has a mechanical fix                  |
| A **retyped** column is still read            | Often survivable; breaks casts, comparisons, precision assumptions |
| The asset or a consumer carries a **PII** tag | Now a governance question, not only a broken query                 |
| A **chart or dashboard** consumes it          | These fail silently — they render empty rather than erroring       |
| An affected asset has **no owner**            | Breaking it notifies nobody                                        |

Keep the rating deterministic. The same change against the same graph should produce the
same answer every time, and the user should be able to argue with your reasoning. A
severity nobody can interrogate is one they learn to ignore.

### 7. Report in the order a reader needs

1. The decision — is this safe to ship, and why
2. The count, **with the denominator**: "15 of 25 downstream assets read this column"
3. What a person will notice: named charts and dashboards
4. Who to tell: owners from DataHub, deduplicated, affected-asset owners first
5. The long tail of tables, collapsed or last

---

## Proposing a fix

If the user asks you to fix the downstream breakage, ground every suggestion in what the
consumer actually runs — fetch its real queries and its schema first. A migration written
from the column name alone is a guess.

Two rules that prevent most bad suggestions:

- **Preserve the downstream model's own output names.** Reading a renamed upstream column
  and aliasing it back (`select o.order_state as order_status`) keeps that model's contract
  intact so _its_ consumers don't break in turn.
- **A drop is not mechanical.** If there is no honest equivalent for a dropped column, say
  so plainly and name the decision the human has to make. Never invent a replacement.

---

## Boundaries

This skill does **not** handle:

- Metadata questions ("who owns X?") → use `/datahub-search`
- Applying tags, owners, or documentation → use `/datahub-enrich`
- Assertions, incidents, and data quality → use `/datahub-quality`
- Tracing _upstream_ to find a root cause, or general pipeline mapping → use
  `/datahub-lineage`

The distinction from `/datahub-lineage`: that skill explores the graph. This one evaluates
a specific pending change and returns a verdict.

---

## Two failure modes to avoid

**Reporting the whole subtree.** If your answer to every column change is the same list of
assets, you have not done the analysis — you have forwarded the lineage graph.

**Silence about what you could not check.** If a model could not be resolved in DataHub, or
a query could not be parsed, say so. A gap reported is a gap someone can close; a gap
omitted is indistinguishable from a clean bill of health.
