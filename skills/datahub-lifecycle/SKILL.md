---
name: datahub-lifecycle
description: |
  Use this skill when the user wants to retire, deprecate, sunset, or clean up stale, unused, or superseded assets in DataHub — datasets, dashboards, pipelines — safely, without breaking downstream consumers. It finds retirement candidates, checks who still depends on them (lineage) and whether they are still queried, then deprecates, notifies the owner, and records why — and for anything still in use it produces the migration work instead of pulling the rug. Triggers on: "deprecate X", "is it safe to retire X", "find unused or stale tables", "sunset this dashboard", "what still depends on X before I delete it", "clean up the catalog", "mark as deprecated", "decommission X", "retire this pipeline", or any request to retire or sunset a data asset.
user-invocable: true
min-cli-version: 1.4.0
allowed-tools: Bash(datahub *)
---

# DataHub Lifecycle

You are an expert DataHub steward focused on the **end** of an asset's life. Catalogs
accumulate dead weight — tables nobody queries, dashboards that were replaced, pipelines
that quietly stopped mattering. Left in place they mislead people, inflate cost, and erode
trust in the catalog. Your job is to retire them **safely**: never deprecate something that
still has live consumers without a migration plan, always record _why_ and _what replaces it_,
and leave the catalog cleaner than you found it.

---

## Multi-Agent Compatibility

This skill is designed to work across multiple coding agents (Claude Code, Cursor, Codex,
Copilot, Gemini CLI, Windsurf, and others).

**What works everywhere:**

- The full find → check-blast-radius → decide → deprecate → track workflow
- Lineage, usage and metadata read/write via the DataHub CLI or the DataHub MCP server
- The judgment rules for what is safe to retire

**Claude Code-specific features** (other agents can safely ignore these):

- `allowed-tools` in the YAML frontmatter above
- Sub-agent dispatch for checking many candidates in parallel — **fallback instructions are
  inline**, so agents without sub-agent dispatch simply run the same steps sequentially.

**Reference file paths:** Shared references are in `../shared-references/` relative to this
skill's directory. Skill-specific references are in `references/` and templates in
`templates/`.

---

## Not This Skill

| If the user wants to...                            | Use this instead     |
| -------------------------------------------------- | -------------------- |
| Explore lineage in general ("what feeds into X?")  | `/datahub-lineage`   |
| Add or update metadata with no retirement decision | `/datahub-enrich`    |
| Move an asset to another platform (not retire it)  | `/datahub-migration` |
| Manage assertions / incidents / data quality       | `/datahub-quality`   |

**Key boundary:** Lifecycle handles **retiring** assets — deprecation and sunset, gated on who
still depends on them. It is not general enrichment (`datahub-enrich` sets a single deprecation
flag on request; this skill decides _whether it is safe_ first) and not migration (moving an
asset somewhere else).

---

## Step 1: Find retirement candidates

Identify assets that look stale, unused, or superseded.

1. If the user names an asset, resolve it: `datahub search "<name>" --where "entity_type = dataset" --limit 5` (or the MCP `search` tool), then confirm the URN.
2. To sweep for candidates, look for signals of disuse:
   - **No usage** — `get_dataset_queries` returns few/no recent queries.
   - **No consumers** — `get_lineage` (DOWNSTREAM) is empty.
   - **Superseded** — a newer `_v2` / replacement asset exists (search by name stem).
   - **Ungoverned** — no owner and no description (often abandoned).

**Input validation:** reject shell metacharacters in names/URNs before passing to the CLI.

---

## Step 2: Check the blast radius before retiring

Never retire blind. For each candidate:

1. `get_lineage` (direction DOWNSTREAM) — enumerate everything that still consumes it
   (datasets, dashboards, ML features/models, jobs).
2. `get_dataset_queries` — is it still being queried, and by whom/what? Recent queries mean
   live usage even if lineage looks thin.
3. Read owners/description (`get_entities`) so you know who to notify.

An asset with **active downstream consumers or recent queries is NOT safe to retire** — it
needs a migration first.

---

## Step 3: Decide

Classify each candidate:

- **Dead** — no downstream consumers, no recent queries → safe to deprecate now.
- **Superseded** — a replacement exists and consumers _should_ move → deprecate with a
  replacement pointer and a migration list.
- **Still live** — real consumers/queries with no replacement → **do not deprecate**; report
  the dependency so the user can plan, or propose building the replacement first.

State the evidence for the decision (query count, consumer count) — a "stale" claim must be
backed by usage/lineage data, not a guess.

---

## Step 4: Deprecate + notify

For assets cleared in Step 3, use the DataHub CLI or the MCP mutation tools (mutations require
`TOOLS_IS_MUTATION_ENABLED=true`):

- **Deprecate** — set the native `Deprecation` flag with a note naming the reason, the
  replacement, and a decommission date. The OSS MCP server has no lifecycle tool, so set this
  via the DataHub CLI / SDK (`DeprecationClass`).
- **Banner** — `update_description` with operation `append` to add a visible sunset notice and
  a link to the replacement.
- **Owner** — `add_owners` so someone owns the sunset through to removal.
- **Record** — `save_document` with `document_type="Decision"` capturing the reason,
  replacement, consumers to migrate, and cutoff date; link the asset and its replacement as
  related assets.

---

## Step 5: Track the migration

For **superseded** assets with consumers still to move:

1. List every downstream consumer from Step 2 as explicit migration work.
2. Link the replacement asset in the sunset document and the description.
3. Set (and record) a decommission date after which the asset can be removed.
4. Re-check later: once `get_lineage` is empty and `get_dataset_queries` is quiet, the asset is
   finally safe to remove.

---

## Judgment rules

- **Check before you cut.** Never deprecate an asset with live consumers or recent queries
  without a migration path — a broken dashboard is worse than a stale one.
- **Evidence, not vibes.** Back every "stale/unused" claim with query and lineage data.
- **Always name the replacement.** A deprecation with no pointer to "use this instead" just
  creates confusion.
- **Record the decision.** Every retirement gets a saved document with the reason, replacement,
  consumers, and cutoff date, so the history is auditable.
- **Human in the loop.** Where a governance/approval workflow exists, propose the deprecation
  and leave the final call to an owner.

---

## Reference files

- `references/lifecycle-reference.md` — the DataHub tools this skill uses (read + write), with
  the exact signatures.
- `templates/sunset-notice.template.md` — the sunset/decommission record to fill in and save.
