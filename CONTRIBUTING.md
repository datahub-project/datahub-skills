# Contributing

## Local development setup

Install [pre-commit](https://pre-commit.com/) so the same hooks CI runs also run on every `git commit`:

```bash
pip install pre-commit
pre-commit install
```

This wires up `prettier` (markdown formatting), `markdownlint-cli2`, `ruff`, and a handful of basic file checks. The exact set lives in `.pre-commit-config.yaml`. CI re-runs them via `.github/workflows/lint.yml` — installing locally just saves you a push round-trip when a hook would have rejected the change.

To run every hook against the whole repo without committing:

```bash
pre-commit run --all-files
```

## Commit conventions

We use [Conventional Commits](https://www.conventionalcommits.org/). Your PR title becomes
the commit message on squash-merge, so format it like this:

| Prefix   | Effect             | Example                               |
| -------- | ------------------ | ------------------------------------- |
| `feat:`  | Minor version bump | `feat: add Snowflake connector skill` |
| `fix:`   | Patch version bump | `fix: correct table formatting`       |
| `feat!:` | Major version bump | `feat!: redesign skill structure`     |
| `docs:`  | No release         | `docs: update README`                 |
| `ci:`    | No release         | `ci: add linting workflow`            |

PR titles are enforced by CI — see the `Lint PR Title` check.

## Releasing

Releases are handled by [Release Please](https://github.com/googleapis/release-please).
You don't need to manage versions yourself.

1. Merge PRs with conventional titles into `main`
2. Release Please opens a release PR with a changelog and version bump
3. Edit the release PR if you want, then merge it
4. A git tag and GitHub Release are created on merge

### Don't

- Manually edit the version in `plugin.json` or `.release-please-manifest.json`
- Create git tags by hand
- Write `CHANGELOG.md` by hand — it's auto-generated (but you can edit it in the release PR before merging)
