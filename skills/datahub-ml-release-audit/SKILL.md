---
name: datahub-ml-release-audit
description: |
  Audit an ML model or feature for target leakage and temporal leakage before release using DataHub lineage, schema, transformation, and availability-time evidence. Use when a user asks whether an ML model is safe to promote, why offline performance spiked, whether a feature existed at prediction time, or how to document and remediate suspected leakage. Triggers on: "target leakage", "temporal leakage", "point-in-time", "model release audit", "feature available at prediction", "AUC spike", and "safe to promote".
user-invocable: true
min-cli-version: 1.4.0
allowed-tools: Bash(datahub *)
---

# DataHub ML Release Audit

Audit whether every model input was legally available at prediction time. Treat DataHub metadata as evidence, not as a substitute for missing facts. An LLM may explain evidence but must never invent lineage, timestamps, or a release verdict.

## Compatibility and boundaries

This workflow works across Agent Skills-compatible clients. Prefer DataHub MCP tools when available; otherwise use the DataHub CLI or SDK. Check each tool's current schema before calling it.

Use another DataHub skill when the request is only general catalog search, lineage visualization, metadata enrichment, or assertion management. This skill owns the narrower release question: **could this model have learned from information unavailable at prediction time?**

Read-only investigation is the default. Never tag an asset, change a structured property, save a document, raise an incident, or alter production data without explicit user approval of the exact write plan.

## Evidence rules

1. Separate correlation from availability. Feature importance, correlation, SHAP, mutual information, and ablation can prioritize investigation but cannot prove leakage.
2. Require direction. Outcome ancestry must flow into the feature or training snapshot; a nearby label table is not enough.
3. Require time semantics. Compare each source record's authoritative `available_at` time with the model's `prediction_time` or cutoff. Event time alone may not represent availability.
4. Prefer column-level lineage and transformation text. Dataset-level proximity is insufficient when field lineage exists.
5. Do not convert missing metadata into a clean bill of health.
6. Run a legitimate, highly predictive pre-cutoff control. A detector that blocks the safe control solely because it is important is not calibrated.
7. Keep deterministic evidence and point-in-time reconstruction as independent confirmation routes.

Load [the verdict contract](references/verdict-contract.md) before assigning a verdict. If producing a machine-readable evidence bundle, validate it with:

```bash
python scripts/validate_evidence.py audit.json
```

## Workflow

### 1. Fix the audit scope

Resolve and state:

- model and, when available, model-version URN;
- training-run or snapshot identity;
- prediction target and outcome definition;
- prediction timestamp/cutoff and timezone;
- feature set or training dataset;
- intended release environment.

If the target entity is ambiguous, search and present candidates. If the prediction cutoff is unknown, continue collecting metadata but the final verdict cannot exceed `insufficient_metadata`.

Validate URNs before passing them to a CLI. Reject shell metacharacters in user-supplied CLI arguments.

### 2. Build the evidence graph

Prefer these MCP operations when exposed:

- `search` to resolve model, version, feature, dataset, and job entities;
- `get_entities` to batch-read descriptions, ownership, tags, custom properties, and transformation context;
- `get_lineage` for bounded upstream traversal;
- `get_lineage_paths_between` for a suspected outcome-to-feature path;
- `list_schema_fields` for exact field identities and types.

Begin at one hop and expand only as needed. Record truncation, absent lineage, and unresolved siblings. For every candidate feature, preserve the exact path:

```text
outcome field -> transformation/job -> derived feature field -> training snapshot -> model version
```

If MCP is unavailable, use `datahub search`, `datahub lineage --format json`, and `datahub lineage --column <field>` after checking the installed CLI help. Never claim that zero returned edges means no dependencies; ingestion may be incomplete.

### 3. Establish availability semantics

For each suspicious source and derived feature, identify:

- business event time;
- ingestion or processing time;
- authoritative availability time;
- prediction time;
- transformation predicate, join, window, and timezone;
- late-arrival or backfill behavior.

Classify each source as `pre_outcome`, `outcome`, `post_outcome`, or `unknown`. Quote the relevant transformation fragment when available and explain the direction of the comparison. A safe cutoff usually has semantics equivalent to `source.available_at <= prediction_time` for every joined record.

Do not infer availability from a column name such as `created_at`. If authoritative semantics are absent, record an evidence gap.

### 4. Test, do not merely score

Use statistical signals only to rank candidates. For a suspected feature:

1. Record observed offline performance and plain ablation as context.
2. Reconstruct the training view using the authoritative point-in-time cutoff.
3. Rerun the same evaluation protocol, split, seed, and metric.
4. Measure how much apparent advantage remains.
5. Repeat the comparison for a highly predictive pre-cutoff control.

Never choose a collapse threshold after seeing the result. State the configured policy, its owner, and the measured margin. Point-in-time collapse confirms leakage only when directional outcome lineage and an availability violation are already established.

### 5. Assign a calibrated verdict

Apply the lattice in `references/verdict-contract.md`. Summarize the decisive facts and missing facts separately. Never promote `needs_review` or `insufficient_metadata` to `clear_for_release` because no violation was found.

Required report shape:

```markdown
## ML release audit: <model/version>

Verdict: <verdict>
Release action: <allow | hold | block>
Prediction cutoff: <timestamp and timezone | unknown>

### Decisive evidence

- <exact lineage path>
- <availability comparison>
- <deterministic proof or qualified reconstruction, if any>

### Counter-evidence and controls

- <safe-control result>
- <alternative explanation tested>

### Evidence gaps

- <missing metadata and why it matters>

### Minimal remediation

- <smallest change that removes the violation>
```

### 6. Propose minimal remediation

Prefer the smallest reversible correction:

- add the missing point-in-time predicate;
- replace a post-outcome source with a pre-cutoff snapshot;
- remove only the offending field;
- backfill authoritative availability metadata;
- rebuild the affected snapshot and rerun the identical audit.

Do not automatically edit production transformations or retrain/promote a model. Show the proposed change and the verification test first.

### 7. Publish only after approval

Present an exact write plan containing target URNs, metadata types, values, and incident behavior. After explicit approval, use the available write tools—for example `add_tags`, `add_structured_properties`, or `save_document`—or the supported SDK/GraphQL equivalent. Then reread every mutation and report any mismatch.

Publication should be idempotent. Reuse an active incident for the same model version and audit fingerprint rather than creating duplicates. Never publish secrets, raw sensitive rows, or unsupported certainty.

## Stop conditions

- Unknown model/version or prediction cutoff: stop short of a release decision.
- Missing column lineage or authoritative availability time: report `insufficient_metadata` and the exact metadata needed.
- Correlation or ablation is the only signal: do not call it leakage.
- Directional outcome ancestry exists but the time violation is unproven: report `needs_review`.
- A requested write is not explicitly approved: return the dry-run plan only.
- Live results contradict cached evidence: prefer the live reread, disclose the conflict, and do not publish.

## Example requests

- "Audit `urn:li:mlModel:credit_default_v4` for target leakage before promotion."
- "Our AUC jumped overnight. Trace the top feature to its sources and check whether it existed at scoring time."
- "Reconstruct this training join point in time and compare it with a high-correlation safe control."
- "Prepare a DataHub audit document and write plan for this confirmed violation; do not publish yet."
