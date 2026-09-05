# Cascade reference workflow

[Cascade](https://github.com/himxsh/Cascade) is an Apache-2.0 reference
implementation of the remediation loop. The registry skill does not require
Cascade; use it only when the user wants the packaged implementation or a
fixture-backed demonstration.

## Install and run the fixture path

```bash
git clone https://github.com/himxsh/Cascade.git
cd Cascade
pip install -e .
cascade demo --out artifacts/demo
```

This produces:

- `artifacts/demo/generate/impact_report.json` + rewritten SQL
- `artifacts/demo/apply/pr_comment.md`
- `artifacts/demo/apply/downstream_pr.diff`
- planned DataHub write-back JSON under `artifacts/demo/apply/`

## CLI map

| Step     | Command                                                     |
| -------- | ----------------------------------------------------------- |
| Impact   | `cascade impact --urn … --diff …`                           |
| Generate | `cascade impact … --generate --out …` or `cascade generate` |
| Dry run  | `cascade apply --report … --out …`                          |

## Implementation-specific metadata

Cascade can use the following namespaced tags:

- `cascade:breaking-pending`
- `cascade:migrated`
- `cascade:retrain-suggested`

These are Cascade conventions, not defaults for this skill. In another
organization, reuse approved tags or ask before creating new ones.

## Limitations

- The fixture proves orchestration, not the freshness or completeness of a
  production DataHub graph.
- Repository mappings and GitHub handles still require confirmation.
- Generated rewrites require the target repository's own checks and human
  review before merge.
