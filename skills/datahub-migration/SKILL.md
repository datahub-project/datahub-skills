---
name: datahub-migration
description: |
  Use this skill when the user wants to plan or execute a breaking schema
  change -- retyping, renaming, or deprecating a column -- and needs every
  downstream consumer found, migrated, and verified before the old column
  is retired. Triggers on: "retype X to Y", "rename column X", "deprecate
  X, move consumers to Y", "migrate this column", "what needs to change if
  I alter X", "safely change the type of X", or any request involving a
  column-level schema migration with real downstream impact.
user-invocable: true
min-cli-version: 1.5.0.1rc1
allowed-tools: Bash(datahub *)
---

# DataHub Migration

You are an expert at executing safe, verified schema migrations across a
data estate using DataHub's column-level lineage as the source of truth
for blast radius. Your role is not to analyze and report -- it is to
actually plan, migrate, and verify a real column change end to end,
using the expand -> migrate -> verify -> contract pattern.

---

## Multi-Agent Compatibility

This skill is designed to work across multiple coding agents (Claude
Code, Cursor, Codex, Copilot, Gemini CLI, Windsurf, and others).

**What works everywhere:**

- The full expand -> migrate -> verify -> contract workflow
- Column-level blast-radius traversal via MCP tools or the DataHub CLI
- The two-stage lineage traversal needed to catch BI/ML consumers (see
  Step 2)

**Claude Code-specific features** (other agents can safely ignore
these):

- `allowed-tools` in the YAML frontmatter above

**Reference file paths:** Shared references are in
`../shared-references/` relative to this skill's directory. Skill-specific
references are in `references/` and templates in `templates/`.

---

## Not This Skill

| If the user wants to...                                          | Use this instead      |
| ------------------------------------------------------------------ | ---------------------- |
| Just explore lineage or answer "what depends on X?" with no change | `/datahub-lineage`     |
| Search for entities by keyword or metadata                         | `/datahub-search`      |
| Add or update metadata with no schema change involved              | `/datahub-enrich`      |
| Create assertions or manage incidents unrelated to a migration     | `/datahub-quality`     |

**Key boundary:** Lineage answers "what depends on X?" as a read-only
question. Migration means the user actually wants X changed and every
consumer moved over safely -- real PRs, real verification, a real
deprecation. If nothing is going to change, this is the wrong skill.

---

## Step 1: Confirm the Migration Intent

Establish, precisely:

1. **Target column** -- exact entity URN and column/field name.
2. **What's changing** -- retype (old type -> new type), rename, or
   deprecate-and-replace. These have different risk profiles: a retype
   can often preserve the external name; a rename or deprecation cannot.
3. **New name, if any** -- the column name consumers should end up
   referencing. For a pure retype with no rename, this can be the same
   name; for a rename/deprecation it must be a new name.
4. **Sunset window** -- how long the old column stays queryable after
   consumers move off it (default 90 days if the user doesn't specify).

Ask for anything missing before proceeding -- do not guess a target
column from a vague description when more than one candidate exists.

---

## Step 2: Find the Real Blast Radius (Two-Stage Traversal)

Column-level lineage in DataHub only carries fine-grained (per-column)
edges on dataset-to-dataset `upstreamLineage`. BI charts, dashboards, and
ML feature tables only express **table-level** edges, because that's
what real BI tools and feature stores actually report. A single
column-scoped lineage call will silently miss them. Use two stages:

1. **Column-scoped traversal** from the target column, downstream, to
   find every dataset that is a genuine column-level consumer:

   ```
   get_lineage(urn=<target_urn>, column=<target_column>, upstream=false, max_hops=3)
   ```

   or via the CLI: `datahub lineage --urn "<target_urn>" --direction downstream`
   with column-level detail.

2. **Table-level fan-out** from every dataset found in stage 1, one hop,
   unscoped (no `column` argument), to catch charts/dashboards/ML
   features/other non-dataset entities riding on top of it:

   ```
   get_lineage(urn=<dataset_urn>, column=null, upstream=false, max_hops=1)
   ```

Merge both result sets, deduplicated by URN, into the blast radius.
Consumers found only in stage 2 don't need a code diff (see Step 4) --
they inherit correctness once their upstream dataset is migrated -- but
they still belong in the playbook and, where relevant, in the sunset
communication.

---

## Step 3: Sequence the Plan

Topologically order the blast radius by hop distance from the target --
never migrate a consumer before its own upstream. Frame the plan in four
phases:

1. **Expand** -- add the new column/field alongside the old one
   (additive DDL, backfilled). The old column is never touched yet.
2. **Migrate** -- one code change per consumer that has a real reference
   to rewrite, each pointing at the new name, sequenced by the
   topological order from above.
3. **Verify** -- prove every consumer's *whole propagated chain* correct
   before any of it goes live for real (see Step 4).
4. **Contract** -- only once every verification in the plan has passed:
   deprecate the old column with a sunset date and replacement pointer,
   and write a migration playbook back into the catalog.

---

## Step 4: Verify Before You Commit -- Chained Parallel-Run

A downstream consumer's rewritten code references its *immediate
parent's* new column, but that parent isn't actually redeployed yet at
verification time. Don't stage a real deploy at every hop just to prove
correctness -- that's unnecessary risk and complexity for what is
fundamentally a read-only proof. Instead, chain every migrated ancestor's
own old/new logic together (e.g. as CTEs) into one self-contained query
per consumer, with the root source virtually expanded via a cast until
the real expand DDL has actually run. Compare old vs. new row-for-row on
a real key column, not a synthetic one, before opening a single PR.

Only proceed to Step 5 once every consumer in the plan has a passing
verification result.

---

## Step 5: Execute -- Real PRs, Real Write-Back

This is the step that makes the migration real, not a report:

1. Run the actual expand DDL against the warehouse.
2. Open one real, mergeable PR per consumer that needs a code change,
   each with a clear description of what changed and why.
3. Re-run verification against the real warehouse now that the expand
   has actually happened.
4. If -- and only if -- every verification passes: deprecate the old
   column in the catalog (sunset date + replacement pointer) and save a
   migration playbook document on the target entity, linked to whatever
   application/agent identity is doing the migration.

If any verification fails, stop before the contract phase. A partially
migrated, unverified consumer is worse than an unmigrated one.

---

## Step 6: Write the Playbook

Every migration should leave behind a playbook the next person or agent
can find and reuse -- especially for a sibling migration on a related
column later. Include: why the change was made, the full blast radius
(with which consumers needed a code change vs. inherited it for free),
the verification results per consumer, the PRs opened, and what to do
differently for a sibling migration. See `templates/migration-plan.template.md`
and `references/expand-migrate-verify-contract.md`.
