# MBOM / Quality Attestation

**Entity:** <!-- display name -->  
**URN:** <!-- urn -->  
**Date:** <!-- ISO date -->  
**Gate:** OPEN / BLOCKED / LIFTED  
**Risk:** <!-- 0–100 -->

## Summary

<!-- 2–4 sentences -->

## Findings

| Type | Severity | Evidence |
| --- | --- | --- |
| <!-- … --> | <!-- … --> | <!-- … --> |

## Blast radius

<!-- table or ASCII -->

## Quarantine state

- Tags:
- Structured properties:
- Consumer Gate policy: advisory metadata — not global MCP denial

## Remediation

- PR / patch path:
- Suggested SQL / dbt change (grounded in catalog queries):

## Lift criteria

1. Fix merged / applied  
2. Re-scan clean  
3. Remove quarantine tags + set `gate_status=LIFTED`
