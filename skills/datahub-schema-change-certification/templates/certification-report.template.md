# DataHub schema-change certification

## Decision summary

- Run: `{{run_id}}`
- Target: `{{target_urn}}`
- Requested change: `{{requested_change}}`
- Direct-request verdict: `{{risk_verdict}}` (`{{risk_score}}/100`)
- Safe strategy: `{{migration_strategy}}`
- Workflow state: `{{workflow_state}}`
- Evidence boundary: `{{live_fixture_or_unavailable}}`
- Evidence class: `{{LIVE_VERIFIED_NON_LIVE_OR_UNKNOWN}}`
- Mutation eligibility: `{{PASS_OR_NOT_RUN}}` — `{{reason_code}}`
- Coverage: `{{complete_or_limited_with_reason}}`
- Exact target matches: `{{must_be_1}}`
- Schema pagination complete: `{{true_or_false}}`
- Lineage pagination complete / missing paths: `{{true_or_false}}` / `{{count}}`
- Risk evaluated at / hash: `{{timestamp}}` / `{{risk_hash}}`

## Why the direct request is unsafe

| Finding            | Severity       |       Weight | Deterministic evidence   |
| ------------------ | -------------- | -----------: | ------------------------ |
| `{{finding_code}}` | `{{severity}}` | `{{weight}}` | `{{artifact_or_entity}}` |

## Downstream impact

| Target       | Platform/type       |       Hops | Exact path                    | Owner       | Coverage    |
| ------------ | ------------------- | ---------: | ----------------------------- | ----------- | ----------- |
| `{{entity}}` | `{{platform_type}}` | `{{hops}}` | `{{source -> ... -> target}}` | `{{owner}}` | `{{state}}` |

## Generated safe package

- Descriptor hash: `{{descriptor_hash}}`
- Manifest recomputed from current files: `{{PASS_OR_FAIL}}`
- Credential-value scan: `{{PASS_OR_FAIL}}`

| File       | Kind       | SHA-256      | Structural validation | Execution   |
| ---------- | ---------- | ------------ | --------------------- | ----------- |
| `{{path}}` | `{{kind}}` | `{{sha256}}` | `{{state}}`           | `{{state}}` |

## Evidence ledger

| Claim       | State                                      | Artifact       | Boundary       | Reproduce             |
| ----------- | ------------------------------------------ | -------------- | -------------- | --------------------- |
| `{{claim}}` | `{{PASS/WARN/FAIL/NOT_RUN/STALE/FIXTURE}}` | `{{artifact}}` | `{{boundary}}` | `{{command_or_tool}}` |

## MCP and mutation preflight

- MCP initialization/server/protocol: `{{state_server_protocol}}`
- Raw evidence hash / call count: `{{sha256}}` / `{{count}}`
- Raw tool types: `{{exact_tool_names}}`
- Query retrieval: `{{state}}`; executed `{{true_or_false}}`; total `{{count}}`; returned `{{count}}`; pages `{{count}}`; complete `{{true_or_false}}`; truncated `{{true_or_false}}`
- Tool inventory hash: `{{sha256}}`
- Preflight recomputed from captured schemas: `{{PASS_OR_FAIL}}`
- Analysis ready: `{{true_or_false}}`
- Write-back state: `{{PASS_or_NOT_RUN}}`
- Tool schemas verified: `{{tool_names_or_gaps}}`
- Permitted ordered mutations: `{{tool_names_or_none}}`
- Structured-property bindings: `{{verified_roles_or_omitted}}`
- Runtime mutation exposure: `{{true_or_false}}`

## Approval scope

- Scope hash: `{{scope_hash}}`
- Scope version: `{{scope_version}}`
- Created at: `{{timestamp}}`
- Planned target: `{{target_urn}}`
- Bound raw evidence hash: `{{sha256_or_not_applicable}}`
- Bound tool inventory hash: `{{sha256}}`
- Bound artifact descriptor / manifest: `{{sha256}}` / `{{sha256}}`
- Planned mutations hash: `{{writeback_plan_hash}}`

## Human decision

- Decision: `{{APPROVE_OR_REJECT}}`
- Reviewer: `{{reviewer}}`
- Identity verification: `{{AUTHENTICATED_OR_SELF_ASSERTED}}`
- Note: `{{decision_note}}`
- Decided at: `{{timestamp}}`
- Approved scope hash: `{{scope_hash}}`
- Scope accepted: `{{true_or_false}}`

## Change passport

- Passport ID: `{{passport_id}}`
- Manifest hash: `{{manifest_hash}}`
- Policy version/hash: `{{policy_version_and_hash}}`
- Context hash: `{{context_hash}}`
- Live-evidence hash: `{{live_evidence_hash_or_not_applicable}}`
- Valid until: `{{valid_until}}`
- Pre-write verification: `{{state}}`

## DataHub write-back

| Operation             | Arguments hash                 | Receipt     | Durable verification | Retry action                     |
| --------------------- | ------------------------------ | ----------- | -------------------- | -------------------------------- |
| Decision document     | `{{sha256}}`                   | `{{state}}` | `{{state}}`          | `{{created_updated_or_skipped}}` |
| Structured properties | `{{sha256_or_not_applicable}}` | `{{state}}` | `{{state}}`          | `{{upserted_or_omitted}}`        |
| Description marker    | `{{sha256}}`                   | `{{state}}` | `{{state}}`          | `{{appended_or_skipped}}`        |

## Remaining boundaries

- `{{NOT_RUN, STALE, WARN, FAIL, or FIXTURE claim}}`

The passport does not attest to its own persistence. The outer receipts and exact read-back above are the authority for DataHub write-back.
