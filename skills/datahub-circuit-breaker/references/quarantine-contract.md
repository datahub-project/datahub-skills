# Quarantine contract (advisory circuit breaker)

## Canonical tags

| Tag URN | Meaning |
| --- | --- |
| `urn:li:tag:QUARANTINED` | Asset should not be trusted as clean context |
| `urn:li:tag:CIRCUIT_BROKEN` | Circuit breaker was tripped by an automated or human process |
| `urn:li:tag:MIDSPHERE_AUDIT` | Optional: audited by MidSphere-style swarm |

## Structured properties

| Property | Values | Meaning |
| --- | --- | --- |
| `midsphere.gate_status` | `OPEN` \| `BLOCKED` \| `LIFTED` | Consumer-facing gate state |
| `midsphere.risk_score` | number 0–100 | Optional blast-radius risk |
| `midsphere.job_id` | string | Optional audit / job correlation id |
| `midsphere.pr_url` | string | Optional remediation PR |

## What this does **not** mean

- DataHub MCP does not automatically refuse `get_entities` / `search` for tagged assets.
- Third-party agents only stop consuming dirty context if **they** filter tags / gate properties, or use a MidSphere-style Consumer Gate.

## Mutations

Requires MCP server with `TOOLS_IS_MUTATION_ENABLED=true`, or equivalent GraphQL / CLI write path. Tags and structured property definitions must exist before assignment.
