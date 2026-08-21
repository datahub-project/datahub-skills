# Drift Finding — {{CHANGED_COLUMN}}

**Change:** `{{CHANGED_COLUMN}}` was **{{CHANGE_TYPE}}** {{#detail}}({{DETAIL}}){{/detail}}
**Severity:** `{{SEVERITY}}` ({{hard_break = breaks outright | silent_break = miscomputes, no error}})

## Impacted report columns ({{N}})

| Report column | Derived via   | Hops  |
| ------------- | ------------- | ----- |
| {{col}}       | {{transform}} | {{h}} |

## Business impact

{{One or two sentences: what the wrong numbers mean downstream — e.g. a regulatory margin
report over/under-stating available margin is a compliance breach.}}

## Proposed data contract

```
{{Enforceable contract on the changed upstream column: name, type, constraints.}}
```

## Remediation

{{The single most important next step.}}

## Written back to DataHub

- Tagged {{N}} columns `drift-at-risk` + `drift-{{SEVERITY}}`
- Set `drift_status` structured property on each impacted schemaField
- Replaced each impacted column's description with the proposed contract
