# Cascade reference workflow

Cascade (Apache-2.0) is a reference agent implementing this skill for the DataHub Agent Hackathon.

## One-command fixture demo

```bash
pip install -e .
cascade demo --out artifacts/demo
```

Produces:

- `artifacts/demo/generate/impact_report.json` + rewritten SQL
- `artifacts/demo/apply/pr_comment.md`
- `artifacts/demo/apply/downstream_pr.diff`
- `artifacts/demo/apply/datahub_writeback.json` / `ml_writeback.json` / `migrated.json`

## CLI map

| Step | Command |
| ---- | ------- |
| Impact | `cascade impact --urn … --diff …` |
| Generate | `cascade impact … --generate --out …` or `cascade generate` |
| Act | `cascade apply --report … --out …` |

## Tags

| Tag | Meaning |
| --- | ------- |
| `cascade:breaking-pending` | Source dataset has an open coordinated migration |
| `cascade:migrated` | Remediations merged; pending cleared |
| `cascade:retrain-suggested` | ML model should be retrained after feature/schema break |
