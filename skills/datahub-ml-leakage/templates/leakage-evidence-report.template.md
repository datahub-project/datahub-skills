# Leakage Check: {model_name}

**URN:** `{model_urn}`
**Platform:** {platform} · **Version:** {model_version}
**Verdict:** {verdict} — `{reason_code}`

---

## Policy Applied

| Setting         | Value             |
| --------------- | ----------------- |
| Forbidden tags  | {forbidden_tags}  |
| Forbidden terms | {forbidden_terms} |
| Max hops        | {max_hops}        |
| Confirmed by    | {policy_source}   |

---

## Traversal Summary

| Metric              | Value               |
| ------------------- | ------------------- |
| Features examined   | {feature_count}     |
| Fields visited      | {visited_count}     |
| Deepest hop reached | {max_hop_reached}   |
| Lineage resolution  | {resolution_status} |
| Unresolved hops     | {unresolved_count}  |

`{resolution_status}` must be `fully resolved` for an `approved` verdict. Any
unresolved or truncated branch is a block — record it here rather than omitting it.

---

## Evidence Path

| Hop | Node        | Type   | Labels   |
| --- | ----------- | ------ | -------- |
| 0   | {node_name} | {type} | {labels} |

**Forbidden node reached:** `{violating_node}` (tag: `{violating_tag}`)
**Entry feature:** `{entry_feature}`

### Why this is leakage

{mechanism_explanation}

### Verify in DataHub

- Model: <{model_ui_url}>
- Violating column: <{violating_node_ui_url}>

---

## Additional Findings

| Feature   | Verdict           | Reason        | Depth   |
| --------- | ----------------- | ------------- | ------- |
| {feature} | {feature_verdict} | {reason_code} | {depth} |

---

## Write-Back

| Target   | Action   | Status   |
| -------- | -------- | -------- |
| {target} | {action} | {status} |

Write-back status is independent of the verdict above. A failed mutation does not
change the decision.

---

## Remediation

- {remediation_1}
- {remediation_2}

Advisory only. This section does not affect the verdict.
