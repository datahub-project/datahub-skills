---
name: datahub-change-impact
description: >
  Analyzes the downstream blast radius and risk of a proposed schema or asset
  change (rename, drop, deprecate) using DataHub's lineage and quality
  context, and proposes a mitigation plan tailored to the change type. Use
  when a user asks what breaks if they rename, drop, or deprecate a column,
  table, or dataset, or asks about the blast radius or risk of a planned
  change before making it. Triggers on: "what breaks if I rename X", "impact
  of dropping column Y", "is it safe to deprecate table Z", "blast radius of
  changing W", "risk of this schema change", "who's affected if I remove X".
---

# DataHub Change Impact skill activated.

**Follow this workflow in order.** Do not skip steps or guess at lineage —
every claim about downstream impact must trace back to an actual
`datahub-lineage` result, and every risk tier must be explainable from named
signals, not asserted.

## 1. Classify the change

Determine which of these the user is describing:

- **Rename** — a column or field is being renamed (old name → new name)
- **Drop** — a column or field is being removed
- **Deprecate** — a whole dataset/table is being sunset

If the request doesn't clearly map to one of these three, ask the user to
clarify rather than guessing — the risk heuristic and recommendations below
are calibrated per change type, and a wrong classification produces a
misleading risk score.

## 2. Resolve the target asset

Use `datahub-search` (see `datahub-search/SKILL.md` in this repo) to resolve
the plain-English reference to a canonical DataHub asset. If the target is a
specific column/field, confirm it against the resolved asset's schema.

If search returns multiple plausible candidates, **stop and ask the user to
disambiguate** — do not silently pick the top match. Show the candidates with
enough context (platform, owner, description) for the user to choose
correctly.

## 3. Trace the downstream blast radius

Use `datahub-lineage` (see `datahub-lineage/SKILL.md`) to trace downstream
from the resolved asset, scoped to the specific field when the change is
column-level. Note explicitly whether column-level lineage was available or
whether the trace had to fall back to table-level — this affects how
confident the resulting risk assessment can be, and that caveat should be
surfaced to the user, not silently dropped.

Compile the downstream footprint: total count, entity types (dataset, job,
dashboard, chart), and which of those are business-facing (dashboards and
charts are business-facing; jobs and datasets are typically not, unless
ownership metadata says otherwise).

## 4. Score the risk

Apply this heuristic. It must stay transparent — every tier you report needs
the specific signals that produced it, stated in plain language, not just the
tier name.

Signals, and their effect on risk:

- **Downstream count** — more affected assets increases risk
- **Business-facing assets** (dashboards, charts) in the downstream set —
  increases risk, since breakage is visible to end users, not just engineers
- **Jobs/pipelines** in the downstream set — increases risk of silent
  operational breakage
- **Missing owner metadata** on affected assets — increases risk, since
  there's no clear person to coordinate with
- **Column-level lineage unavailable** — does not itself raise or lower risk,
  but should lower your stated confidence in the assessment; say so explicitly

Illustrative tiers (starting point — use judgment, but never emit a tier
without at least one concrete, named reason):

- **Low** — 1-2 downstream assets, ownership present, no business-facing
  assets affected
- **Medium** — several downstream assets, or at least one job/dashboard
  affected, or some ownership gaps
- **High** — broad downstream footprint, multiple business-facing assets
  affected, and/or critical assets with unclear ownership

If `datahub-quality` is available and the user's DataHub instance supports it,
optionally check whether any downstream assets have open incidents or failing
assertions — an existing quality issue on an already-fragile asset raises the
tier further. Treat this as an enhancement: if the quality check fails or
times out, fall back to the lineage-only assessment rather than blocking on
it.

## 5. Propose a mitigation plan

Tailor recommendations to the change type, tied to what was actually found —
not generic best-practice boilerplate:

- **Rename** — alias/dual-write period, owner review, dashboard mapping
  verification, phased cutover for High-risk cases
- **Drop** — owner notification, downstream consumer check before removal,
  deprecation window if business-facing assets are affected
- **Deprecate** — stakeholder sign-off, migration path for downstream
  consumers, sunset timeline communication

Scale the number and urgency of recommendations to the risk tier — a High
case should include a phased/delayed-cutover recommendation; a Low case can
be brief. Each recommendation needs a rationale referencing the specific
impacted assets, e.g. "3 dashboards depend on this column" — not a generic
statement disconnected from this analysis.

## 6. Present the analysis, then offer to persist it

Show the user: resolved asset, downstream footprint, risk tier with reasons,
and the mitigation plan. Then ask whether they want this analysis written
back into DataHub as durable context (e.g. a structured property or
description note on the affected asset) so future users inherit it.

**Only hand off to `datahub-enrich` on explicit confirmation.** Never write
back automatically — this workflow is read-and-recommend by default; write-
back is an opt-in action the user takes deliberately, following
`datahub-enrich`'s own propose-then-confirm pattern.

## Notes for implementers extending this skill

- This skill composes `datahub-search`, `datahub-lineage`, optionally
  `datahub-quality`, and `datahub-enrich` — it does not duplicate their
  underlying tool calls, and should degrade gracefully if any of them are
  unavailable in a given DataHub deployment (fall back to a narrower
  assessment and say what was skipped, rather than failing outright).
- The risk heuristic in step 4 is intentionally simple and explainable rather
  than statistical — resist the temptation to replace it with a model. The
  value of this skill is that a data engineer can audit _why_ a change was
  scored the way it was.
