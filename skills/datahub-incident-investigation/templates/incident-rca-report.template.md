# Incident RCA: {incident_title}

**Incident URN:** `{incident_urn}`
**Affected asset:** {affected_asset_name} (`{affected_asset_urn}`)
**Root cause asset:** {root_cause_asset_name} (`{root_cause_asset_urn}`)
**Priority:** {priority}
**Status:** {state} / {stage}
**Investigator:** {investigator}
**Opened:** {opened_at} — **Resolved:** {resolved_at}

---

## Symptom

| Element     | Value                                     |
| ----------- | ----------------------------------------- |
| Observable  | {affected_field} on {affected_asset_name} |
| Expected    | {expected_value}                          |
| Observed    | {observed_value}                          |
| Deviation   | {deviation}                               |
| Onset       | {first_bad_period}                        |
| Last good   | {last_good_period}                        |
| Reported by | {reporter}                                |

{symptom_statement}

---

## Root Cause

> {one_sentence_cause}

{full_explanation_with_magnitudes_and_onset}

**Why this and not something else:** {necessity_and_sufficiency_argument}

**Magnitude arithmetic:** {computation_showing_candidate_reproduces_symptom}

---

## Lineage Path

```
{ascii_flow_diagram_from_root_cause_to_affected_asset}
```

| Hop | Asset        | Platform   | Role in the defect |
| --- | ------------ | ---------- | ------------------ |
| {n} | {asset_name} | {platform} | {role}             |

---

## Hypotheses Considered

| #   | Hypothesis   | Class   | Verdict   | Confidence   | Evidence       |
| --- | ------------ | ------- | --------- | ------------ | -------------- |
| H1  | {hypothesis} | {class} | {verdict} | {confidence} | {evidence_ids} |

---

## Evidence

| ID   | Class   | Source   | Finding   |
| ---- | ------- | -------- | --------- |
| [E1] | {class} | {source} | {finding} |

{narrative_referencing_evidence_ids}

---

## Blast Radius

**Downstream entities affected:** {downstream_count} across {hop_depth} hops

| Type   | Count   | Entities   | Owners   |
| ------ | ------- | ---------- | -------- |
| {type} | {count} | {entities} | {owners} |

**Single-source consumers (no alternative path):** {critical_consumers}
**Owners notified:** {notified_owners}

---

## Remediation

**Layer:** {remediation_layer}
**Applied by:** {applier} on {applied_at}
**Scope:** {scope_statement}

```diff
{diff_or_replacement_block}
```

**Rejected alternatives:** {rejected_fixes_and_why}

---

## Verification

| Check               | Before   | After   | Expected   | Result   |
| ------------------- | -------- | ------- | ---------- | -------- |
| Symptom measurement | {before} | {after} | {expected} | {result} |
| Full test suite     | {before} | {after} | {expected} | {result} |

{verification_notes}

---

## Prevention

| Gap               | Action            | Owner   | Follow-up             |
| ----------------- | ----------------- | ------- | --------------------- |
| {gap_description} | {proposed_action} | {owner} | {ticket_or_reference} |

---

## Writeback

| Action             | Target             | Result   |
| ------------------ | ------------------ | -------- |
| Incident resolved  | `{incident_urn}`   | {result} |
| RCA link attached  | `{root_cause_urn}` | {result} |
| Contract corrected | `{field_path}`     | {result} |
| Check proposed     | `{root_cause_urn}` | {result} |

---

## Timeline

| Time   | Event   |
| ------ | ------- |
| {time} | {event} |
