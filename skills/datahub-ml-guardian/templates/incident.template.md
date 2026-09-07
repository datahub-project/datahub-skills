# 🚨 Incident: {{ change_type }} on `{{ table }}.{{ column }}`

**Status:** at-risk · **Severity:** {{ severity }}
**Detected by:** DataHub ML Guardian

## Root cause

`{{ table }}.{{ column }}` — {{ detail }}

## Blast radius

- Features affected: {{ affected_features }}
- Models affected: {{ affected_models }}
- Lineage path: `{{ lineage_path }}`

## Measured impact

- {{ metric_name }} {{ metric_before }} → {{ metric_after }} (Δ {{ metric_delta }})

## Recommended action

{{ recommended_action }}

<!--
Filled in by the skill and saved back via save_document. Keep the lineage path and the
measured metric delta so the next agent can verify the reasoning before acting. Attach the
remediation PR link once opened.
-->
