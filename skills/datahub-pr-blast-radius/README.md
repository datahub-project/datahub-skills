# DataHub PR Blast Radius

Review SQL and dbt pull requests before merge using DataHub lineage.

## What it does

1. Fetches the PR diff and identifies changed data models and columns
2. Resolves every entity in the catalog (exact match only)
3. Traces downstream lineage and collects owners
4. Scores the change with deterministic rules
5. Posts a verdict comment with an impact table and a fix suggestion

## Capabilities

- **Blast radius review** - who breaks downstream if this PR merges?
- **Deterministic severity** - SAFE / RISKY / BREAKING from lineage facts, never model opinion
- **Owner surfacing** - the impact table names the people who need to know
- **Safe defaults** - missing lineage or unresolved entities never produce SAFE

## Rules that never bend

- Missing lineage, unresolved entities, unparseable diffs: never SAFE
- Entity resolution is exact-match only; collisions escalate to RISKY
- Severity is a rule table, not a judgment call

## Example

```
> Review PR 42 for blast radius before we merge it
```

Produces a comment: verdict, downstream assets with owners, hop distance,
severity per asset, and a deprecate-first fix suggestion.
