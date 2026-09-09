# Code Guardian Report: {repository_or_change}

**Scope:** {changed_paths_or_whole_repository}
**Catalog:** {datahub_server} ({deployment_tier})
**Assets in play:** {asset_count}

---

## Already Known

What the catalog already recorded about these assets, read before anything was proposed.

| Asset        | Check   | State   | Since   | Last conclusion         |
| ------------ | ------- | ------- | ------- | ----------------------- |
| {asset_name} | {check} | {state} | {since} | {reason_or_repair_note} |

**Not reopened:** {checks_already_closed}
**Blocked by an earlier refusal:** {checks_with_refused_repair}

---

## Asset Map

| Source reference      | Resolved asset | Confidence               |
| --------------------- | -------------- | ------------------------ |
| `{file}:{line}` {ref} | {asset_urn}    | exact / ambiguous / none |

**Unresolved:** {unresolved_references}

---

## New Findings

| #   | Check   | File and line   | Finding   | Catalog evidence |
| --- | ------- | --------------- | --------- | ---------------- |
| 1   | {check} | `{file}:{line}` | {message} | {evidence}       |

---

## Repairs

| #   | Check   | Change             | Evidence        | Verified               |
| --- | ------- | ------------------ | --------------- | ---------------------- |
| 1   | {check} | {before} → {after} | {lineage_proof} | check re-run: {result} |

**Reported without a patch:** {findings_the_catalog_does_not_prove}

---

## Recorded Back

| Asset        | Verdicts   | Passing   | Failing   | Assertion identity |
| ------------ | ---------- | --------- | --------- | ------------------ |
| {asset_name} | {verdicts} | {passing} | {failing} | `{assertion_urn}`  |

**Report link attached:** {external_url}

---

## What a Person Still Has To Do

- {item_needing_a_human}
- {metadata_gap_to_hand_to_datahub_enrich}
