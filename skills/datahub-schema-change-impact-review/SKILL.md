---
name: datahub-schema-change-impact-review
description: |
  Use this skill when the user wants to review a proposed dataset schema change before merge by combining DataHub lineage, metadata, deterministic risk evidence, approval requirements, and migration safeguards. Triggers on: "rename column", "drop column", "change data type", "schema migration review", "what will this schema change break", "is this safe to merge", or requests for pre-merge schema impact assessment. For general lineage exploration, use `/datahub-lineage`; for ordinary metadata updates, use `/datahub-enrich`.
user-invocable: true
min-cli-version: 1.5.0.1rc1
allowed-tools: Bash(datahub *)
---

# DataHub Schema Change Impact Review

Review a proposed column change against real DataHub context, explain an
authoritative deterministic decision, generate review-only safeguards, and keep
all mutation behind a separate human-confirmed step.

## Prerequisites

- A reachable DataHub OSS or DataHub Cloud instance with lineage already
  ingested.
- A configured DataHub CLI authenticated to that instance.
- Permission to read the reviewed asset, schema, lineage, ownership, tags,
  glossary terms, and available quality evidence.
- Separate write permission only if the user later requests and explicitly
  confirms write-back.

No paid LLM key is required. Prefer deterministic orchestration of DataHub read
tools. Treat optional model-generated prose as non-authoritative.

## Inputs

Require:

- Root asset URN or an unambiguous asset name.
- Affected column.
- Change type: `rename`, `drop`, `type_change`, or `add`.
- New column name or data type for all operations except `drop`.

Accept an optional human rationale. Reject malformed URNs, an unchanged rename,
or a missing new value when one is required.

## Outputs

Produce:

- Resolved root identity and evidence provenance.
- Unique affected assets classified by type, platform, hop, and dependency
  level.
- Fixed risk factors, raw and capped score, risk level, and `ALLOW`, `REVIEW`,
  or `BLOCK` decision.
- Real owner-based approval labels when DataHub provides owners.
- Migration, compatibility, tests, rollback, and review-summary artifacts.
- A sanitized DataHub CLI execution trace with requested commands, successes,
  failures, fallback, duration, and evidence URNs.
- A separate write-back preview and receipt only when requested and confirmed.

## Evidence and Authority Boundaries

Keep these three layers explicit:

1. **DataHub-retrieved evidence:** entity metadata and lineage returned by read
   tools. Preserve URNs and report missing evidence as unavailable.
2. **Deterministic calculations:** de-duplication, classification, points,
   thresholds, decision, approvals, and artifact templates. These are
   authoritative.
3. **Agent narrative:** a concise explanation based only on layers 1 and 2. It
   cannot add lineage or alter points, decisions, approvals, or mutation state.

Read [references/risk-policy.md](references/risk-policy.md) before scoring and
[references/safety-policy.md](references/safety-policy.md) before proposing any
write-back.

## Workflow

### 1. Resolve the Source Asset

If the user supplies a URN, use it directly. Otherwise search DataHub, show the
best matches with readable name, platform, type, and URN, and require a choice
when the name is ambiguous. Confirm that the chosen root is the asset under
review.

### 2. Inspect Root Schema and Metadata

Use the DataHub CLI to retrieve the root schema and metadata:

```bash
datahub get --urn "<ROOT_URN>" --aspect schemaMetadata
datahub get --urn "<ROOT_URN>" --aspect ownership
datahub get --urn "<ROOT_URN>" --aspect globalTags
```

Verify the affected column when the schema is available. Do not conclude that a
column is absent when a response is truncated, timed out, or permission-limited.

### 3. Inspect Governance and Quality Evidence

From the root and downstream entities, retain only real values for:

- Owners and ownership roles.
- Tags and glossary terms.
- Schema fields and descriptions.
- Structured properties.
- Identifiable assertion or quality results.
- Usage only when DataHub exposes a defensible normalized value.

Normalize referenced URNs into readable labels, retain the original URNs, and
deduplicate values. Use `unknown` for quality and `0` with `unavailable`
provenance for usage when reliable signals are absent.

### 4. Traverse Column Lineage First

For a dataset field, request downstream column lineage before entity lineage:

```bash
datahub lineage --urn "<ROOT_URN>" --column "<AFFECTED_COLUMN>" \
  --direction downstream --hops 2 --count 60 --format json
```

Record the exact tool operation and duration. Treat zero returned results as no
fine-grained evidence, not proof that no dependencies exist.

### 5. Fall Back Honestly to Dataset Lineage

If column lineage is empty, unsupported, or fails, record the fallback and
request downstream dataset lineage:

```bash
datahub lineage --urn "<ROOT_URN>" --direction downstream --hops 2 \
  --count 60 --format json
```

Label every dependent with the evidence actually used: column-level lineage or
dataset-level fallback. A fallback is not an error when fine-grained lineage is
simply unavailable.

### 6. Deduplicate the Blast Radius

Deduplicate by full entity URN before counting, scoring, displaying, or
requesting enrichment. Preserve one root asset separately. Respect configured
hop and result limits and report truncation.

### 7. Classify Affected Assets

Classify from the DataHub entity type and URN:

- Dataset and dataset-like storage entities.
- Data jobs and data flows as pipelines.
- Dashboards and charts as BI/reporting assets.
- ML models and feature tables as ML assets.

Do not infer owners, tags, terms, usage, or quality. Deterministic criticality
may be used only as a labeled fallback; never present inferred criticality as
explicit DataHub metadata.

### 8. Apply the Deterministic Risk Policy

Calculate every point from
[references/risk-policy.md](references/risk-policy.md). Show each factor label,
point contribution, and supporting evidence. Cap the final score at 100 and use
the documented thresholds exactly. No agent narrative or LLM may change a
factor, score, risk level, or decision.

### 9. Generate Review-Only Safeguards

Generate all of the following from the validated proposal:

- Migration SQL.
- Compatibility SQL or deprecation guidance.
- Schema/data tests.
- Rollback steps.
- Pull-request or change-review summary.

Mark SQL as review-only. Never execute migration SQL.

### 10. Present the Investigation

Lead with decision, score, affected count, platforms, and required approvals.
Then show lineage evidence, deterministic score composition, generated
safeguards, and the DataHub CLI trace. The narrative must state that the risk
engine remains authoritative.

### 11. Require Explicit Human Confirmation Before Write-Back

Analysis is read-only. A user asking to investigate is not authorizing a
mutation. Build an exact preview from the stored completed analysis, show the
root target and complete proposed metadata, and require explicit human
confirmation after the preview.

### 12. Write Only to the Reviewed Root Asset and Verify

After valid confirmation, write only the reviewed root asset through an
approved DataHub write-back path. Preserve unrelated documentation and replace or
append only the analysis-specific managed section. Re-read DataHub and verify
the exact result. Report applied, already applied, partial, failed, or unknown
outcomes honestly. Do not modify downstream assets.

### 13. Record the Safety Outcome

The final report and write-back record must state: **No migration SQL was
executed.** Include the analysis ID and UTC timestamp. Retain a sanitized trace,
not prompts, tokens, raw response bodies, or secrets.

## Failure States

- **Source unresolved:** show candidates or request a valid URN; do not guess.
- **Root entity missing:** preserve the URN fallback and mark entity evidence
  unavailable.
- **Column lineage empty:** perform and record dataset-level fallback.
- **One enrichment failure:** keep the lineage result and isolate the failure.
- **DataHub CLI unavailable or timed out:** return an honest degraded or
  unavailable trace and continue deterministic analysis when provider evidence
  exists.
- **Lineage provider unavailable:** stop the impact decision and report a
  retryable provider error; do not switch to fabricated demo results.
- **Quality or usage absent:** return `unknown` or unavailable; do not infer.
- **Write-back disabled or unconfirmed:** do not mutate.
- **Write-back transport uncertainty:** report unknown outcome and require
  inspection before retrying.

## Safety Guarantees

- Do not fabricate metadata, lineage, owners, tags, terms, assertions, usage,
  approvals, or mutation outcomes.
- Do not perform automatic mutation.
- Do not execute generated migration SQL.
- Do not modify downstream assets.
- Do not replace unrelated documentation.
- Do not leak credentials, access tokens, prompts, or secret-bearing raw
  responses.
- Do not present inferred criticality as explicit DataHub metadata.
- Do not let narrative override deterministic scoring or confirmation.

See [references/safety-policy.md](references/safety-policy.md) for the complete
write-back checklist.

## Examples

- [Rename a column](examples/rename-column.md)
- [Drop a column](examples/drop-column.md)

Example outputs are illustrative in shape, not hardcoded production evidence.
Replace every count and metadata value with the current DataHub response.

## Validation

Validate the contribution with the repository hooks:

```bash
pre-commit run --all-files
```

Then run a read-only live scenario. Verify that the trace lists `datahub get`
and `datahub lineage`, fallback is visible when used, the deterministic decision
is unchanged, and no DataHub mutation occurs until the separate confirmed
write-back action.
