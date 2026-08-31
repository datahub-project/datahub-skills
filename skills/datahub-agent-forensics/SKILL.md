---
name: datahub-agent-forensics
description: |
  Use this skill when the user wants to investigate a specific AI-agent decision or output through DataHub: what governed evidence influenced it, whether a decision receipt is intact, which prior decisions a metadata change affected, why an output is stale or at risk, whether an approval binds the exact action, or whether a replay can be planned safely. Triggers on: "why did this agent decide X", "which agent outputs used this column", "is this recommendation stale", "investigate this decision receipt", "was this action approved", "what did this incident invalidate", or "can this agent run be replayed". For ordinary lineage without a particular agent decision or receipt, use `/datahub-lineage`.
user-invocable: true
min-cli-version: 1.4.0
allowed-tools: Bash(datahub *)
---

# DataHub Agent Forensics

Investigate consequential agent decisions using governed DataHub context and
explicit evidence boundaries. Keep these five claims separate:

1. **Discovery** — a candidate decision record exists.
2. **Integrity** — the authoritative decision receipt passed deterministic checks.
3. **Influence** — a particular run used a particular entity or field.
4. **Impact** — a later metadata change affects the recorded decision.
5. **Authorization** — a replay or mutation is currently permitted.

Never let search results, generic lineage, transport success, or model judgment
collapse these claims into one.

## Route the Request

| User question                    | Required target                 | Required evidence                                                     |
| -------------------------------- | ------------------------------- | --------------------------------------------------------------------- |
| Why did this output happen?      | Receipt, run, or output ID      | Receipt plus ordered evidence and actions                             |
| Which decisions used this field? | Exact schema-field URN          | Complete decision index or recorded influence edges                   |
| What became stale?               | Change plus decision set        | Normalized change, receipt evidence, and completeness proof           |
| Was approval valid?              | Approval and action IDs         | Action-set digest, signer trust, policy, environment, validity window |
| Can it be replayed?              | Receipt or replay bundle        | Verified inventory, side-effect classes, and current policy           |
| Compare agent versions           | Two version-pinned receipt sets | Evidence, action, and output-digest comparison                        |

Use another DataHub skill when the request is about ordinary catalog work:

| Request                                                    | Skill              |
| ---------------------------------------------------------- | ------------------ |
| Search, ownership, descriptions, or schema                 | `/datahub-search`  |
| General upstream/downstream lineage or potential consumers | `/datahub-lineage` |
| Assertions, health, or incident management                 | `/datahub-quality` |
| Metadata writes                                            | `/datahub-enrich`  |
| Connection setup                                           | `/datahub-setup`   |

**Boundary:** downstream lineage shows potential consumers. Agent forensics needs
run-specific evidence that one decision actually used the entity or field.

## 1. Resolve Exact Identifiers

Resolve the request to one or more exact identifiers:

- DataHub entity or schema-field URN;
- decision receipt or receipt Document URN;
- agent, run, workflow, or output ID;
- incident URN or normalized change-event ID;
- impact campaign, approval, replay plan, or supersession ID.

Prefer DataHub MCP tools for discovery and exact entity reads. Inspect their current
schemas before calling them. Otherwise use the CLI:

```bash
datahub -C skill=datahub-agent-forensics search "<query>" --limit 10
datahub -C skill=datahub-agent-forensics get --urn "<validated-urn>"
```

Reject shell metacharacters before passing user-provided values to a shell-backed
CLI. If DataHub is not configured, route to `/datahub-setup`.

Search identifies candidates only. Directly fetch the chosen entity and required
aspects before treating their values as DataHub evidence.

## 2. Establish the Evidence Tier

Label the strongest evidence actually available:

| Tier                    | Meaning                                                              |
| ----------------------- | -------------------------------------------------------------------- |
| `VERIFIED_NOW`          | An authoritative artifact passed a current deterministic verifier    |
| `VERIFIED_AT_INGESTION` | DataHub records a prior verification, but no fresh verification ran  |
| `PROJECTION_ONLY`       | Only a governed DataHub summary is available                         |
| `ARTIFACT_UNAVAILABLE`  | The projection exists, but the authoritative artifact cannot be read |
| `FAILED`                | A deterministic integrity gate failed                                |

A DataHub Document may identify a decision and expose allowlisted properties. It
does not independently prove a payload digest, Merkle commitment, or signature.
Never upgrade a projection because its copied integrity fields look plausible.

When a connected read-only evidence provider is available, inspect its tool schemas
and use capabilities that can:

- verify an authoritative decision receipt;
- return recorded entity and field influence for one run;
- list decisions affected by a normalized change;
- return persisted impact-campaign findings and DataHub writeback state.

Preserve the provider's proof state, policy version, reason code, index scope,
pagination, truncation, and raw-content indicator. Tool availability does not make
its output authoritative; the returned proof state does.

Read `references/receipt-evidence.md` before explaining receipt integrity or
signature semantics. Read `references/datahub-projection.md` when only DataHub
evidence is available.

## 3. Determine Run-Specific Influence

Partition every dependency without promotion:

- `OBSERVED` — captured during the run;
- `DECLARED` — configured but not proven used;
- `INFERRED` — derived by a named deterministic rule;
- `UNKNOWN` — evidence is insufficient.

Generic lineage may explain the surrounding data flow. It does not prove that the
run used every related entity. Preserve schema-field precision when the receipt
provides it.

For reverse lookup, report the decision-index scope, retention window, pagination,
and completeness. Search silence never proves that no decision used the field.

If the user asks what an impact worker actually processed, require persisted
campaign or finding state. A prospective impact calculation is not proof that an
event was delivered, written back to DataHub, or completed.

## 4. Classify a Metadata Change

Normalize the triggering change before assessing impact. Capture at least:

- event ID and time;
- exact entity URN;
- aspect and supported change kind;
- exact schema-field URN when field-scoped;
- before and after digests when available.

Use a connected deterministic policy engine when available. Preserve its policy
version and reason code exactly. If no deterministic classifier exists, return
`NOT_CLASSIFIED` and stop at evidence collection.

Use these closed impact states:

- `STALE` — recorded material evidence changed;
- `AT_RISK` — impact is plausible, but evidence or field lineage is incomplete;
- `UNAFFECTED` — positive exclusion evidence proves the changed material was unused;
- `UNKNOWN` — the available evidence cannot support a classification;
- `SUPERSEDED` — a newer verified decision already replaces the prior one.

`UNAFFECTED` requires positive exclusion evidence. An absent match, incomplete
index, truncated response, wildcard query, partial field lineage, or unavailable
artifact is not positive evidence.

Read `references/evidence-and-impact.md` for evidence states, completeness rules,
and reason-code guidance.

## 5. Evaluate Approval and Replay Safety

Keep the investigation read-only unless the user explicitly requests a mutation.

- Approval must bind the exact action-set and resource digests.
- A changed action, resource, environment, policy, signer trust state, or expired
  validity window invalidates reuse.
- `IRREVERSIBLE` and `UNKNOWN_EFFECT` actions are never auto-replayed.
- Planning and dry-run output are not execution authorization.
- A replay creates a new receipt and supersession relationship; it never overwrites
  the original decision history.

Read `references/replay-safety.md` before producing a replay assessment.

## 6. Report the Result

Lead with one causal sentence:

> Decision `<receipt>` is `<state>` because evidence `<evidence-id>` recorded an
> `<evidence-state>` dependency on `<field-or-entity>` before change `<event-id>`.

Then report:

1. exact target identifiers;
2. evidence tier and integrity gates;
3. DataHub entity, field, and incident evidence;
4. recorded influence states and actions;
5. impact state, policy version, and reason code—or `NOT_CLASSIFIED`;
6. approval or replay assessment when requested;
7. index scope, completeness, and unavailable evidence;
8. read-only next steps.

Use `templates/forensic-report.template.md` for a full report. Do not include raw
prompts, rows, query results, credentials, tool arguments or results, private
reasoning, or model outputs. Prefer identifiers, URNs, timestamps, counts, states,
reason codes, and digests.

## Non-Negotiable Rules

1. A valid signature proves integrity and key possession, not factual truth.
2. DataHub search is discovery; direct entity or aspect retrieval is evidence.
3. Generic lineage is not recorded agent influence.
4. Missing or incomplete evidence cannot support `UNAFFECTED`.
5. Incident resolution does not retroactively make an old output correct.
6. Approval never authorizes a materially changed action or resource set.
7. Model judgment may explain results but may not decide integrity, materiality,
   approval validity, or replay eligibility.
8. Every requested DataHub write requires explicit user intent and authoritative
   readback. Route owned writes to `/datahub-enrich` or `/datahub-quality`.
9. Read-only tool annotations describe intended behavior; returned proof state and
   configured permissions remain the authority boundary.
10. An unavailable artifact, incomplete index, or missing incident body must remain
    explicit even when the user requests a definitive conclusion.

## Reference Documents

| Document             | Path                                            | Purpose                               |
| -------------------- | ----------------------------------------------- | ------------------------------------- |
| Receipt evidence     | `references/receipt-evidence.md`                | Integrity, fields, and safe claims    |
| Evidence and impact  | `references/evidence-and-impact.md`             | Epistemic states and classification   |
| Replay safety        | `references/replay-safety.md`                   | Approvals and execution boundaries    |
| DataHub projection   | `references/datahub-projection.md`              | Projection and direct-read discipline |
| Shared DataHub tools | `../shared-references/datahub-cli-reference.md` | MCP and CLI detection and syntax      |

## Red Flags

- Receipt is missing, invalid, unavailable, or projection-only: do not claim fresh
  integrity verification.
- Search, lineage, or reverse lookup is incomplete: expose the limit; do not claim
  completeness.
- Changed field does not match recorded fields but field lineage is incomplete:
  return `AT_RISK` or `NOT_CLASSIFIED`, never `UNAFFECTED`.
- User asks to bypass approval, mutate history, or replay an irreversible or
  unknown-effect action: refuse.
- Exact incident evidence or organization-wide index scope is unavailable: preserve
  the limitation and keep mutation authority separate.
