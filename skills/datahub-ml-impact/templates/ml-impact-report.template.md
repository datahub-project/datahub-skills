# ML impact — answer template

Structure to present a column-impact result. Lead with the value: the scariest,
most-deployed, trained-on finding first. Keep the trained-vs-inference distinction
explicit — it is the reason this skill exists.

---

## ML blast radius of changing `{table}.{column}`

**Summary:** {N} model(s) affected — {counts, e.g. "1 critical, 1 high, 2 medium"}.
{One sentence: this change won't raise an error, so the impact is silent.}

{If nothing is impacted but the column resolved:}
> ✅ No downstream ML impact — `{table}.{column}` resolves to a real column, and no ML
> feature, model, or deployment depends on it.

{If the analysis was incomplete (unresolved / truncated):}
> ⚠️ Analysis incomplete — do **not** treat this as a clean bill of health. {why}

### Impacted models (most severe first)

For each model:

- **{🔴/🟠/🟡} {severity} — `{model}`** ({owner or "unowned"}{, tags})
  - **Training:** {trained on the changed column | reads it at inference only} ← call this out
  - **Deployment:** {deployment(s) + status | not deployed}
  - **Path:** `{table}.{column}` → `{feature}` → `{model}`
  - **Why:** {the one-line severity rationale from the finding}

### Recommended next step

- Prefer a **deprecate-then-drop**: add the replacement column, backfill, migrate every
  downstream feature + training pipeline, verify the feature store, then remove
  `{column}` in a follow-up.
- Optionally **record this in DataHub** (incident + `pending-upstream-change` tag +
  knowledge-base document) by running with `TOOLS_IS_MUTATION_ENABLED=true`.
- To gate this on the actual PR, run Blastradar's CI agent:
  `blastradar analyze --changes <pr-changeset.json>`.
