# {{CASE_ID}}: {{HEADLINE}}

**Subject model:** `{{MODEL_URN}}`
**Verdict:** {{FAILURE_CLASS}} — root cause `{{ROOT_CAUSE_URN}}`
**Confidence:** {{CONFIDENCE}}
**Investigated:** {{DATE}} by {{AGENT_OR_USER}}

## Failure path

`{{root_cause}}` → `{{stage_2}}` → `{{stage_3}}` → … → `{{model}}`

## Evidence chain

| #   | Asset       | Finding               | Observed     | Expected     | Basis (breadcrumb or probe) |
| --- | ----------- | --------------------- | ------------ | ------------ | --------------------------- |
| 1   | `{{asset}}` | {{kind}}: {{summary}} | {{observed}} | {{expected}} | {{breadcrumb_or_probe}}     |

<details><summary>Probe SQL executed</summary>

- `{{asset}}`: `{{probe_sql}}`

</details>

## Blast radius

{{comma_separated_downstream_assets}}

## Recommended fix

1. {{fix_step_1}}
2. {{fix_step_2}}

## Related cases

- {{PRIOR_CASE_ID}} — {{relation_note}}

---

_Every claim above cites either catalog metadata or the SQL probe that
produced it. Incident raised: `{{INCIDENT_URN}}`._
