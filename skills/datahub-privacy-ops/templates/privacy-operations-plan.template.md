# Privacy operations plan

## Case and evidence boundary

| Field             | Value                                        |
| ----------------- | -------------------------------------------- |
| Case ID           | `<opaque-case-id>`                           |
| Subject reference | `<irreversible-hash>`                        |
| Evidence boundary | `<LIVE_DATAHUB_MCP / FIXTURE / UNAVAILABLE>` |
| Observed at       | `<ISO-8601>`                                 |
| Bounds            | `<assets, fields, lineage hops>`             |
| Evidence hash     | `<sha256>`                                   |
| Status            | `<READY_FOR_APPROVAL / PARTIAL / BLOCKED>`   |

## Coverage

|    Assets | Lineage edges | PII fields | Owner coverage | Complete pagination |
| --------: | ------------: | ---------: | -------------: | ------------------- |
| `<count>` |     `<count>` |  `<count>` |    `<percent>` | `<yes/no>`          |

## Proposed actions

| Asset URN | Owner     | Action                           | Reason              | Executor           | Postcondition   | Evidence refs |
| --------- | --------- | -------------------------------- | ------------------- | ------------------ | --------------- | ------------- |
| `<urn>`   | `<owner>` | `<DELETE / ANONYMIZE / REFRESH>` | `<policy evidence>` | `<named executor>` | `<exact check>` | `<refs>`      |

## Protected and unresolved outcomes

| Asset URN | Owner     | Outcome                    | Reason                          | Next reviewer     | Evidence refs |
| --------- | --------- | -------------------------- | ------------------------------- | ----------------- | ------------- |
| `<urn>`   | `<owner>` | `<RETAIN / MANUAL_REVIEW>` | `<hold, policy gap, ambiguity>` | `<owner or team>` | `<refs>`      |

Protected outcomes remain visible and are not counted as successful mutations.

## Approval contract

- Permitted actions: `<count>`
- Retained under policy or legal hold: `<count>`
- Manual review: `<count>`
- Blocked: `<count>`
- Execution scope hash: `<sha256>`
- Required approval: `APPROVE <scope-hash>`

Any evidence, policy, action, executor, postcondition, or target change creates a new scope hash.

## Verification contract

For every permitted action, require:

- exact asset URN and action;
- executor identity and idempotency key;
- job or transaction ID;
- start and end time;
- postcondition result and residual count;
- success, failure, rollback, or protected state.

## Proposed DataHub write-back

Execution approval does not authorize this section.

| Operation             | Exact targets    | Values or digest             |
| --------------------- | ---------------- | ---------------------------- |
| Tags                  | `<entity URNs>`  | `<tag URNs>`                 |
| Structured properties | `<entity URNs>`  | `<property URNs and values>` |
| Evidence document     | `<document URN>` | `<title and content digest>` |

- Write-back scope hash: `<sha256>`
- Required separate approval: `APPROVE WRITE-BACK <scope-hash>`
- Completion proof: exact read-back from a fresh mutation-disabled MCP session
