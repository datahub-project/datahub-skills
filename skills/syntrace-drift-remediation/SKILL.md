---
name: syntrace-drift-remediation
description: |
  Use this skill when the user wants to detect, assess, or fix schema drift in a DataHub-cataloged pipeline using Syntrace - the open-source autonomous agent (https://github.com/mrnetwork0001/Syntrace) that diffs DataHub's versioned schemas, traces column-level blast radius, rewrites the affected dbt/Airflow code, opens a remediation PR, and writes the fixed lineage back to DataHub. Triggers on: "schema drift", "breaking column change", "rename/dropped column impact", "a column was renamed/dropped upstream", "fix downstream dbt models", "remediation PR", "trace column lineage blast radius", "what breaks if this column changes", "run Syntrace", or "remediate the drifted dataset".
user-invocable: true
allowed-tools: Bash(python3 -m src.main *), Bash(.venv/bin/python scripts/seed_datahub.py *)
---

# Syntrace Drift Remediation

You are driving Syntrace, an autonomous schema-drift remediation agent built on live DataHub Core metadata. Your role is to detect breaking column changes on a watched dataset, report the column-level downstream blast radius, deliver fixed dbt/Airflow code (dry-run or real GitHub PR), and confirm the remediated lineage was written back to DataHub.

Everything Syntrace does is live: it reads versioned `schemaMetadata` aspects and column lineage from a running DataHub instance and writes lineage, schemas, tags, and documentation notes back to it. There is no mock mode - if DataHub is unreachable, the pipeline stops with an error.

---

## Multi-Agent Compatibility

This skill works in any coding agent that can run shell commands (Claude Code, Cursor, Codex, Copilot, Gemini CLI, Windsurf, and others). The `allowed-tools` entry in the frontmatter above is Claude Code-specific; other agents can safely ignore it.

All commands must be run from a checkout of the Syntrace repository root (the directory containing `src/`, `scripts/`, and `examples/`).

**Prerequisites:** clone [Syntrace](https://github.com/mrnetwork0001/Syntrace) (Apache-2.0) and follow its README quickstart (a running DataHub Core instance + the seeded demo scenario, or your own catalog). A hosted demo is available at <https://syntraceapp.xyz>.

---

## Not This Skill

| If the user wants to...                                        | Use this instead                                  |
| -------------------------------------------------------------- | ------------------------------------------------- |
| Explore lineage read-only, with no code fix or write-back      | the official `/datahub-skills:datahub-lineage`    |
| Search the catalog or answer "who owns X?"                     | the official `/datahub-skills:datahub-search`     |
| Hand-edit tags, owners, or descriptions in DataHub             | the official `/datahub-skills:datahub-enrich`     |

**Key boundary:** this skill is for the full detect → trace → fix → PR → write-back loop on schema drift. Syntrace fixes breaking *schema* changes (renamed/dropped/added columns, type changes); it does not fix row-level data-quality defects.

---

## Step 1: Check DataHub is reachable

Syntrace talks to DataHub GMS at `http://localhost:8080` by default (override with `--gms-url <url>` or the `DATAHUB_GMS_URL` env var). The guided demo performs the health check for you:

```bash
python3 -m src.main demo
```

- It first prints `pre-flight: checking DataHub GMS at http://localhost:8080 ...` and either `pre-flight: GMS is up` or a clear error telling you to start the DataHub quickstart stack (see the repo README) and rerun.
- It then verifies the pinned demo scenario is seeded and drifted, seeding any missing stage automatically via the SDK venv, waits for DataHub's search index to catch up, and runs the full pipeline.
- Running `python3 -m src.main` with no arguments is equivalent to `demo`.

Exit codes for both subcommands: `0` success, `1` pipeline/server error, `130` interrupted.

## Step 2: Seed or reset the demo scenario (optional)

The pinned scenario lives in the live catalog: a Postgres `raw.orders` dataset feeding dbt models `stg_orders` → `fct_orders` and an Airflow `load_orders` job. Seeding runs under the repo's SDK venv (never system Python):

```bash
.venv/bin/python scripts/seed_datahub.py --stage baseline   # healthy v1 world + lineage
.venv/bin/python scripts/seed_datahub.py --stage drift      # overwrite raw.orders schema with v2 (the drift)
.venv/bin/python scripts/seed_datahub.py --stage reset      # hard-delete all seeded entities
```

- The only flags are `--stage {baseline,drift,reset}` and `--gms-url <url>`.
- To replay the demo from scratch (e.g. after a remediation run has already "healed" the catalog), run the stages in order: `reset`, then `baseline`, then `drift`.
- Same-stage replays are no-ops. `baseline` refuses to roll a drifted schema back - run `reset` first.
- Prefer `python3 -m src.main demo` when unsure: it decides which stages are missing and runs only those.

## Step 3: Run the pipeline

```bash
python3 -m src.main run
```

Real flags of `run` (there are no others):

| Flag | Meaning |
| --- | --- |
| `--dataset-urn <urn>` | Upstream dataset to inspect (default: `urn:li:dataset:(urn:li:dataPlatform:postgres,raw.orders,PROD)`) |
| `--gms-url <url>` | DataHub GMS URL (default: `$DATAHUB_GMS_URL`, then `http://localhost:8080`) |
| `--create-pr` | Open a real GitHub PR (needs `GITHUB_TOKEN` + `SYNTRACE_REPO`, see Step 6) |
| `--llm` | LLM-assisted code generation when available (needs `OPENAI_API_KEY`) |
| `--output-dir <dir>` | Where artifacts are written (default: `examples/`) |

If the user prefers a browser, the same pipeline is available as a local web app:

```bash
python3 -m src.main ui            # serves http://127.0.0.1:8642 until Ctrl-C (only flag: --port; env SYNTRACE_UI_PORT)
```

`/` is a landing page (its Launch App button opens the dashboard) and `/app` is the dashboard itself. The dashboard has a Run button with a live step timeline, drift cards, the impact table, the diffs and PR body, and the write-back log with DataHub deep links; seeding/reset is available from the page too. One operation runs at a time. The dashboard drives the identical pipeline - Steps 4–7 below apply unchanged.

## Step 4: Interpret the output

The run prints six banners (`━━ Step N/6 ━━`) followed by a Summary:

1. **Detecting schema drift** - one line per detected change, e.g. `COLUMN_RENAMED customer_id -> customer_uuid`. Change types: `COLUMN_RENAMED`, `COLUMN_DROPPED`, `COLUMN_ADDED`, `TYPE_CHANGED`. If it prints `No schema drift detected`, the latest schema version equals the previous one - the catalog is healthy or already remediated (re-seed per Step 2 to replay).
2. **Tracing column-level impact** - the impact report. Each impacted asset shows `[HIGH|MEDIUM|LOW]` severity, the asset name, its type (`DBT_MODEL`, `AIRFLOW_DAG`, `DATASET`), and hop distance from the changed dataset. In the pinned scenario: `[HIGH] stg_orders (DBT_MODEL, 1 hop)`, `[HIGH] load_orders (AIRFLOW_DAG, 1 hop)`, `[MEDIUM] fct_orders (DBT_MODEL, 2 hops)`. Closer hops and renamed/dropped columns mean higher severity - report this tree to the user as the blast radius.
3. **Generating remediation code** - a colored unified diff per fixed file: renamed columns are substituted everywhere, and columns dropped upstream are stubbed at the first hop with `cast(null as <type>) as <column>` to preserve the downstream contract. Every fixed file carries an `AUTO-GENERATED FIX` banner comment.
4. **Opening remediation PR** - dry-run by default: `[dry-run] PR prepared but not opened` plus the branch name. With live credentials it prints `PR opened : <url> (#<number>)`.
5. **Writing example artifacts** - paths written under the output dir (see Step 5).
6. **Writing remediated lineage back to DataHub** - audit lines (`emit_schema_rename`, `emit_column_lineage`, `emit_tag 'syntrace:remediated' ... via mcp` - or `via graphql` when the MCP mutation path is unavailable - and `emit_remediation_note`) and a DataHub UI deep link to the dataset.

The final Summary block gives counts: schema changes detected, downstream assets impacted, files fixed, artifacts written.

## Step 5: Where artifacts land

By default under `examples/` (change with `--output-dir`):

| File | Content |
| --- | --- |
| `dbt_orders_remediated.sql` | Fixed dbt model for `stg_orders` |
| `fct_orders_remediated.sql` | Fixed dbt model for `fct_orders` |
| `airflow_orders_dag.py` | Fixed Airflow DAG for `load_orders` |
| `pr_body.md` | The full PR description Syntrace generated |

`examples/raw_orders_v2.sql` is a checked-in input (the drifted DDL) and is never overwritten. The fixes target the paths listed as `target:` in the Step 5 output; they are delivered via the PR - the local `demo_pipelines/` tree is left untouched.

## Step 6: Open the remediation PR for real

```bash
export GITHUB_TOKEN=<a GitHub token with repo scope>
export SYNTRACE_REPO=<owner>/<name>          # the GitHub repo to open the PR against
python3 -m src.main run --create-pr
```

- A live PR is opened only when `--create-pr` is passed AND both env vars are set; otherwise Syntrace prints a note and falls back to dry-run. Never export these secrets on the user's behalf - ask the user to set them.
- The live path uses the GitHub REST API via the optional `requests` package; if `requests` is not importable, Syntrace raises a clear error telling you to install it or unset the credentials.
- On success Step 4 prints the PR URL and number; the PR contains one branch (`syntrace/schema-drift-remediation-...`) with one fixed file per impacted asset and the generated body.

## Step 7: Verify write-back in the DataHub UI

Open the deep link printed at the end of Step 6 of the run output, or browse to `http://localhost:9002` (quickstart login `datahub` / `datahub`) and search for `raw.orders`. Confirm:

1. **Tags** - each impacted asset (`stg_orders`, `fct_orders`, `load_orders`) now carries the `syntrace-remediated` tag.
2. **Schema tab** - the impacted datasets' schemas show the renamed fields (e.g. `customer_uuid` instead of `customer_id`).
3. **Lineage tab** - column-level lineage anchors on the new column names (e.g. `customer_uuid → customer_uuid`), and mappings from dropped upstream columns are gone.
4. **Documentation panel** - the drifted dataset and each impacted asset carry a one-line `Syntrace: ...` remediation note (idempotent: re-runs replace the line rather than duplicating it; any human-written documentation is preserved).

All write-backs are synchronous, so they are visible in the UI immediately after the run; allow a couple of seconds only for search-index-backed views.
