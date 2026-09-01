---
name: cascade-impact-analysis
description: |
  Use this skill when the user wants to predict whether a planned schema change will cause silent data corruption, assertion failures, or safe outcomes in downstream consumers — and optionally write governance artifacts (deprecation tags, impact warnings, report links) back to DataHub. Triggers on: "what breaks if I drop column X", "impact of changing X to INTEGER", "make X nullable", "rename X to Y", "which consumers reference X", "schema change impact", "silent corruption", or any request to predict downstream consequences of a DataHub schema change.
user-invocable: true
min-cli-version: 1.5.0.1rc1
---

# Cascade: Silent Failure Predictor for Schema Changes

You are invoking **Cascade** — an autonomous agent that predicts which downstream consumers of a DataHub dataset will *silently* produce wrong results after a schema change, estimates how long wrong data would go unnoticed, and writes its findings back into DataHub so the next engineer inherits the warning.

Cascade is available as:
- A **web chat UI** at `http://localhost:8501` (run `python -m cascade.web`)
- A **terminal REPL** (`python -m cascade.cli -i`)
- An **MCP server** exposing 5 tools (`python -m cascade`)

---

## What Cascade Detects

| Classification | Meaning |
|---|---|
| 🔴 **Silent corruption** | Consumer produces wrong results. No error, no alert, no failed pipeline. |
| 🟡 **Assertion failure** | An existing test or assertion catches it loudly. |
| 🟢 **Safe** | Genuinely unaffected. |

The key insight: a column in `SUM(order_total)` and the same column in `SELECT order_total` fail **completely differently** under a type change. The first silently truncates every aggregate. The second is usually survivable. Cascade reads the actual transformation logic (`viewProperties.logic`, DAX measures) to tell them apart.

---

## Setup (Zero Dependencies)

No DataHub required for the demo:

```bash
git clone https://github.com/Kaustuvi/cascade.git
cd cascade
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m cascade.web        # opens http://localhost:8501
```

For live DataHub analysis with governance write-back:

```bash
export DATAHUB_GMS_URL=http://localhost:8080
export CASCADE_DEMO_MODE=false
export CASCADE_LLM_PROVIDER=groq      # free tier: https://console.groq.com/keys
export CASCADE_LLM_API_KEY=<key>
python -m cascade.web
```

---

## Example Prompts

```
Drop order_total from order_details
Change order_total to INTEGER in order_details
Make customer_id nullable in order_details
Rename cust_email to customer_email in order_details
```

---

## What Cascade Does Automatically

For `critical` and `high` risk findings, Cascade writes back to DataHub **without being asked**:

- Applies `cascade-deprecated` tag to the **specific affected column** (Schema tab) and the dataset
- **Appends** an impact warning to the dataset description — preserving existing docs
- Attaches a link to the full rendered report under Documentation
- Writes to every sibling (dbt + Snowflake) because DataHub renders docs from the primary sibling only

---

## Integration with DataHub

Cascade drives **DataHub's own MCP Server** (`mcp-server-datahub`) in-process via FastMCP's in-memory transport — a genuine MCP protocol round-trip with no subprocess.

**Reads via MCP tools:** `search`, `get_lineage`, `list_schema_fields`, `get_entities`

**Writes via MCP mutation tools:** `add_tags` (with `column_paths`), `update_description` (with `operation="append"`), `add_terms`

**GraphQL fallbacks for signals MCP doesn't expose on DataHub Core:**
- `viewProperties.logic` — transformation SQL (MCP's `get_dataset_queries` reads QUERY entities; most deployments have none)
- `fineGrainedLineages` — full column-level lineage map
- `tags` + `assertions` — MCP's `get_entities` returns null for both
- `addLink` mutation — report link (MCP's `save_document` creates a Document entity, not an `institutionalMemory` link)

---

## Reports

Reports persist to `.cascade_reports/` so links written into DataHub survive server restarts. Override the location with `CASCADE_REPORTS_DIR`.

---

## MCP Server Tools (for Claude Desktop / Cursor)

Cascade exposes 5 tools when run as `python -m cascade`:

| Tool | Description |
|---|---|
| `analyze` | Natural language goal → full impact narrative + auto-governance |
| `analyze_schema_change` | Structured input → quick impact summary |
| `get_impact_report` | Retrieve a full report by ID |
| `simulate_incident` | Replay known outage patterns |
| `write_governance` | Manually write governance artifacts |

Config template: `mcp_config.json` in the repo root.

---

## Further Reading

- [README](https://github.com/Kaustuvi/cascade) — full setup guide and architecture
- [DEMO.md](https://github.com/Kaustuvi/cascade/blob/master/DEMO.md) — prompt set with expected results and write-back verification
- [examples/](https://github.com/Kaustuvi/cascade/tree/master/examples) — captured live runs against a real DataHub instance
