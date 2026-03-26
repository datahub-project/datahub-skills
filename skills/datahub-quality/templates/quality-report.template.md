# Quality Report: {entity_name}

**URN:** `{entity_urn}`
**Platform:** {platform}
**Overall Health:** {health_status}

---

## Health Summary

| Health Type | Status | Details |
| --- | --- | --- |
| Assertions | {assertion_health} | {assertion_summary} |
| Incidents | {incident_health} | {incident_summary} |

---

## Assertions ({assertion_total} total)

| # | Type | Description | Last Result | Last Run | Source |
|---|------|-------------|-------------|----------|--------|
| 1 | {type} | {description} | {result} | {timestamp} | {source} |

### Recent Failures

| Assertion | Failure Time | Error Details |
| --- | --- | --- |
| {assertion_name} | {time} | {error} |

---

## Active Incidents ({incident_count})

| # | Type | Title | Priority | Stage | Raised | Assigned To |
|---|------|-------|----------|-------|--------|-------------|
| 1 | {type} | {title} | {priority} | {stage} | {created} | {assignees} |

---

## Subscriptions

| # | Subscriber | Change Types | Channels |
|---|-----------|-------------|----------|
| 1 | {actor} | {change_types} | {channels} |

---

## Recommendations

- {recommendation_1}
- {recommendation_2}
