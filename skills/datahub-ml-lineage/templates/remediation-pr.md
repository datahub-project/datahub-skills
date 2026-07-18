# Template: remediation PR description for an ML lineage finding

When you generate a code fix for a lineage finding (a dbt model diff, a
feature-pipeline change, a DAG edit), pair it with a PR description in this
shape so a human reviewer can evaluate it without re-deriving your evidence:

```markdown
## <one-line summary of the problem>

**Opened by:** <agent name> (automated)
**Severity:** critical | high | medium

### What was found

- <evidence bullet 1, referencing the DataHub entity/lineage path>
- <evidence bullet 2>

### Fix

<what the diff does and why it resolves the finding>

### Evidence trail

Full lineage evidence and DataHub write-back (tags, description update,
linked Analysis document) available on the affected entities:

- `<urn 1>`
- `<urn 2>`
```

## Principles

- **Link back to DataHub, don't duplicate it.** The PR description should
  point at the URNs/Analysis document rather than re-explaining the full
  graph traversal -- DataHub is the source of truth, the PR is the fix.
- **Diff the real file.** Generate an actual unified diff against the
  project's real dbt model / pipeline file, grounded in the schema you read
  from DataHub -- not a synthetic example. If you don't have write access to
  regenerate and test the model, still produce the diff and say so
  explicitly rather than silently skipping it.
- **One PR per finding.** Bundling multiple unrelated findings into one PR
  makes it harder to review and harder to roll back independently.
