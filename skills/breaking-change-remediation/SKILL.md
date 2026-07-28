---
name: breaking-change-remediation
description: |
  Use this skill when the user wants to remediate a breaking schema change: column rename/drop/type change in a PR or warehouse, blast-radius analysis via DataHub lineage, strategy selection (rewrite / adapter_view / deprecate), rewriting downstream SQL, opening coordinated PRs, and writing tags/docs back to DataHub (including ML retrain-suggested). Triggers on: "breaking schema change", "column rename impact", "remediate downstream models", "cascade migration", "what breaks if I rename", "schema change PR remediation".
user-invocable: true
---

# Breaking Change Remediation

You are a DataHub-aware schema migration agent. Turn a **declared, uncoordinated** schema change (rename, drop, type change) into a **coordinated migration**: read lineage and schema from DataHub, reason about per-downstream strategy, rewrite mergeable SQL, open/update remediation PRs, and write the decision trail back to the graph.

This skill complements `/datahub-lineage` (impact visibility) and `/datahub-enrich` (tags/docs). You **act** — you do not stop at a blast-radius list.

---

## Multi-Agent Compatibility

Works across Claude Code, Cursor, Codex, Copilot, Gemini CLI, Windsurf, and other Agent Skills hosts.

**What works everywhere:**

- Fixture/offline demo path (no live GMS required)
- MCP or DataHub CLI for lineage, schema fields, owners, tags, documents
- Emitting rewritten SQL that passes a schema gate (no invented columns)

**Reference:** See `references/cascade-workflow.md` for the Cascade reference implementation.

---

## Not This Skill

| If the user wants to... | Use this instead |
| ----------------------- | ---------------- |
| Only explore lineage / "what depends on X?" | `/datahub-lineage` |
| Only add tags/descriptions without remediation | `/datahub-enrich` |
| Silent warehouse drift / freshness failures | `/datahub-quality` (different problem) |
| Text-to-SQL analytics Q&A | Analytics / search skills — not remediation |

**Key boundary:** This skill owns **coordinated migration of a declared schema break**, including codegen and write-back. Lineage alone is insufficient.

---

## Strategy Menu (agent judgment)

For each downstream node, choose one strategy with a one-line rationale:

| Strategy | When |
| -------- | ---- |
| `rewrite` | **Primary.** Downstream SQL projects/joins the changed column and a safe rename is derivable. Emit mergeable SQL. |
| `adapter_view` | Fallback migration window: no model file, or rewrite fails the schema gate. |
| `deprecate` | Hard `FIELD_REMOVED` with no replacement; fail-fast + owner note. |

Surface strategy + rationale in the PR comment and DataHub document so reasoning is auditable.

---

## Workflow

### 1. Detect the change

Parse the PR diff or user-described change into structured ops:

- `FIELD_RENAMED` — heuristic first (one removed + one added column); optional `# cascade: rename a -> b` / `-- cascade: rename a -> b` confirms/overrides
- `FIELD_REMOVED`
- `FIELD_TYPE_CHANGED`

Resolve the source dataset URN (search / config mapping).

### 2. Read DataHub context (tools)

Prefer MCP when available; else DataHub CLI / GraphQL:

1. `list_schema_fields` / schema on the source and downstream datasets
2. Downstream lineage (multi-hop as needed for demo; start with 1–3 hops)
3. Owners (for reviewers)
4. If a changed column feeds an `mlFeature` → linked `mlModel`, mark **retrain-suggested**

Build an ImpactReport: source, changes, downstream, severity, ml_impact, remediations[].

### 3. Reason + generate

For each downstream node:

1. Select strategy + rationale from context
2. If `rewrite`: edit SQL references (word-boundary rename for columns)
3. **Schema gate (hard fail):** reject any emitted file that references a column not present in DataHub schema fields (allow the *new* column name from a rename)

Never invent column names.

### 4. Act in GitHub

1. Comment on the source PR: blast radius + per-node strategy/rationale + ML impact
2. Open/update a downstream PR with rewritten files (or emit a unified patch artifact in dry-run)
3. Request reviewers mapped from DataHub owners when handles are known

### 5. Write back to DataHub

On the source dataset:

- Document: change plan including rationales
- Tag: `cascade:breaking-pending`
- Description: dated note that a breaking change is pending remediation

On affected `mlModel` (thin ML path):

- Tag: `cascade:retrain-suggested`
- Incident/doc on the model URN

On merge of remediations:

- Remove `cascade:breaking-pending`
- Add `cascade:migrated`

Prefer dry-run / approval before live mutations unless the user explicitly asks to apply.

---

## Offline / demo resilience

If MCP/GMS is unavailable, use a seeded fixture graph and still produce:

1. ImpactReport JSON
2. Rewritten downstream SQL
3. PR comment markdown
4. Write-back payloads as JSON artifacts

Judges and demos should prefer this path for reliability.

---

## Output checklist

- [ ] ImpactReport with severity and remediations (strategy + rationale)
- [ ] At least one **rewritten** SQL file (not shim-only) when rewrite applies
- [ ] Schema gate passed
- [ ] PR comment text includes agent reasoning
- [ ] Dataset + ML write-back actions listed (applied or dry-run)
- [ ] No invented columns
