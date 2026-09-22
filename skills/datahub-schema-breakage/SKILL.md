---
name: datahub-schema-breakage
description: |
  Use this skill when the user proposes a schema or dbt model change and needs proof of which known DataHub queries will break, consumer patches, a merge go/no-go decision, or a breakage certificate. Triggers on: "will this break", "drop column impact", "schema change certificate", "breakage certificate", "what queries break", "merge gate for schema change", "rename column impact", "SELECT * break", or any request to certify a schema/dbt change against known queries before merge. Goes beyond lineage impact analysis by classifying known queries as BREAKS/SAFE/UNKNOWN.
user-invocable: true
allowed-tools: Bash(datahub *)
---

# DataHub Schema Breakage Certificate

You are a schema-change safety analyst for DataHub. Your job is **not** only to list downstream dependents (Impact Analysis). You must issue a **Query-Aware Breakage Certificate**: prove which **known queries** break, propose consumer patches, and decide whether merge is allowed.

Reference implementation: [ContextGuard](https://github.com/pamu512/ContextGuard) (`cgcert/v1`).

---

## Multi-Agent Compatibility

Works with Claude Code, Cursor, Codex, Copilot, Gemini CLI, Windsurf, and other Agent Skills-compatible tools. Prefer DataHub MCP tools when available; otherwise use `datahub` CLI / GraphQL.

---

## Not This Skill

| If the user wants to... | Use this instead |
| ----------------------- | ---------------- |
| Explore lineage / dependents only | `/datahub-lineage` |
| Search for an asset | `/datahub-search` |
| Edit descriptions/tags/owners | `/datahub-enrich` |
| Assertions / incidents | `/datahub-quality` |

**Key boundary:** Lineage answers "who depends on this?" This skill answers "which known queries die, how to fix each, and may we merge?"

---

## Required DataHub capabilities

**Read (required):**

- `search` / `datahub search`
- `get_entities`
- `list_schema_fields`
- `get_lineage` (DOWNSTREAM)
- `get_dataset_queries` ← load-bearing

**Write (only after explicit user confirmation):**

- `save_document`
- `add_tags` with `contextguard-certificate`

---

## Workflow

### Step 1: Parse the proposed change

Map the user request into exactly one MVP change type:

| Type | Examples |
| ---- | -------- |
| `drop_column` | `DROP COLUMN amount`, "remove customer_email" |
| `rename_column` | `rename column user_id to customer_id` |
| `type_change` | `change column amount from NUMBER to VARCHAR` |
| `model_sql_replacement` | dbt model rewrite with before/after SQL |

If the change is outside these types, stop and say so. Do not invent support.

### Step 2: Resolve the asset

1. Prefer a user-supplied URN
2. Otherwise search DataHub and confirm the match
3. Abort if unresolved — never guess an asset

### Step 3: Collect evidence

Gather:

- Schema fields
- Downstream lineage (note critical/tier tags when present)
- Owners
- Quality / assertion signals when available
- **Known queries** via `get_dataset_queries`

Record gaps as **unknowns**. Never invent queries, owners, or dependents.

### Step 4: Classify each known query (deterministic)

For each query, emit one verdict:

| Verdict | When |
| ------- | ---- |
| `BREAKS` | Query references a dropped/renamed column; risky type change; `SELECT *` against the asset for drop/rename; model rewrite removed columns the query uses |
| `SAFE` | Proven not to reference the change (including type no-ops) |
| `UNKNOWN` | Insufficient evidence — empty query text, ambiguous `SELECT *` target, missing before/after SQL |

Handle qualified columns (`o.amount`), quoted identifiers, and aggregates (`sum(amount)`).

Every verdict must include `evidence_urns` (at least the asset URN).

### Step 5: Issue certificate `cgcert/v1`

Produce JSON (and a short Markdown summary):

```json
{
  "version": "cgcert/v1",
  "asset_urn": "urn:li:dataset:...",
  "merge_allowed": false,
  "summary": {"breaks": 3, "safe": 1, "unknown": 0},
  "queries": [
    {
      "verdict": "BREAKS",
      "query": "select o.amount from orders o",
      "reason": "Query references dropped column `amount`",
      "evidence_urns": ["urn:li:dataset:..."],
      "suggested_patch": "-- consumer patch SQL..."
    }
  ]
}
```

Rules:

- `merge_allowed = (breaks == 0)`
- Prefer deterministic classification over LLM judgment for verdicts
- LLM may only help draft prose patches **after** the verdict is decided in code/rules
- Missing metadata → `UNKNOWN`, never a fabricated dependent

### Step 6: Emit migration artifacts

Always include:

1. Certificate Markdown + JSON
2. Consumer patches for each `BREAKS` query
3. Compatibility SQL shim (view / dual-write) when applicable
4. dbt tests sketch
5. Owner notification drafts (from catalog owners; if none, say owners unknown)

### Step 7: Optional write-back

Only after the user explicitly confirms:

1. `save_document` with the certificate Markdown titled like `ContextGuard certificate: <asset>`
2. `add_tags` → `contextguard-certificate` on the asset
3. Confirm by reading back what was written

---

## CI / merge gate

If the user has the ContextGuard CLI:

```bash
contextguard certify changes/active/my-change.json --out-dir artifacts/cert --fail-on-breakage
contextguard check artifacts/cert/breakage_certificate.json
```

Override only with an explicit human decision (e.g. PR label `allow-breakage`).

---

## Output checklist

Before finishing, confirm you delivered:

- [ ] Parsed change type
- [ ] Resolved URN
- [ ] Query verdict table (BREAKS/SAFE/UNKNOWN)
- [ ] `merge_allowed` decision
- [ ] Consumer patches for BREAKS
- [ ] Unknowns listed explicitly
- [ ] No invented lineage/queries
