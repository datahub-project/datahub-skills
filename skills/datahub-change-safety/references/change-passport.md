# Change Passport contract

Use this reference when producing or reviewing a change-safety result. The Passport is an evidence envelope, not a replacement for DataHub metadata or a generic test report.

## Required JSON shape

```json
{
  "schema_version": "1.0.0",
  "passport_id": "stable-content-derived-id",
  "verdict": "UNSAFE | SAFE_WITHIN_SCOPE | UNVERIFIED",
  "change": {
    "repository": "owner/repository",
    "base_revision": "full-sha-or-artifact-version",
    "candidate_revision": "full-sha-or-artifact-version",
    "changed_paths": ["models/orders.sql"],
    "facts": [
      {
        "kind": "expression_changed",
        "field": "net_revenue",
        "before": "...",
        "after": "..."
      }
    ]
  },
  "entity_resolution": [
    {
      "urn": "urn:li:dataset:(urn:li:dataPlatform:snowflake,db.schema.table,PROD)",
      "method": "dbt-manifest-unique-id",
      "environment": "PROD"
    }
  ],
  "context": {
    "provider": "datahub-mcp-or-cli-version",
    "retrieved_at": "RFC-3339",
    "fact_hashes": ["sha256"],
    "lineage_truncated": false,
    "coverage": "complete | incomplete",
    "gaps": [],
    "owners": ["urn:li:corpuser:owner"],
    "critical_consumers": ["urn:li:..."],
    "applied_protections": ["protection-id@version"]
  },
  "evaluations": [
    {
      "consumer_urn": "urn:li:...",
      "critical": true,
      "evaluator": "name@version",
      "status": "passed | failed | error | skipped",
      "started_at": "RFC-3339",
      "completed_at": "RFC-3339",
      "input_hash": "sha256",
      "baseline_output_hash": "sha256",
      "candidate_output_hash": "sha256",
      "observations": {},
      "summary": "short evidence-based statement"
    }
  ],
  "counterexample": {
    "fixture": {},
    "baseline": {},
    "candidate": {},
    "violated_invariant": "...",
    "replay_hash": "sha256",
    "minimization_attempts": []
  },
  "remediation": {
    "status": "none | proposed | verified",
    "patch_or_artifact": "path-or-link",
    "verification_evaluation_ids": []
  },
  "protection_proposal": {
    "protection_id": "stable-id",
    "version": 1,
    "status": "proposed | active",
    "source_passport_id": "...",
    "affected_entity_urns": [],
    "fixture_or_invariant": {},
    "approved_by": null,
    "approved_at": null
  },
  "limitations": [],
  "provenance": {
    "engine_version": "...",
    "tool_versions": {},
    "created_at": "RFC-3339",
    "requested_by": "..."
  }
}
```

Omit `counterexample`, `remediation`, or `protection_proposal` only when they do not apply. Do not omit context gaps or limitations.

## Verdict invariants

- `UNSAFE` requires at least one failed critical evaluation or violated active protection.
- `SAFE_WITHIN_SCOPE` requires complete context coverage, no errored/skipped critical evaluation, and every critical evaluation passed.
- `UNVERIFIED` requires at least one explicit context or execution gap and must not contain a verified remediation claim.
- `remediation.status = verified` requires references to executed passing evaluations.
- `protection_proposal.status = active` requires non-null approval identity and timestamp plus successful DataHub read-back evidence.

## Reviewer Check template

```markdown
## <VERDICT>: <one-sentence result>

**Changed asset:** <name and DataHub URN>
**Context coverage:** <complete/incomplete>; <N> critical consumers; <N> executed
**Evidence:** <failed/passed checks and minimal counterexample>
**Owner:** <DataHub owner(s)>
**Remediation:** <verified/proposed/not applicable>
**Protection memory:** <active/proposed/not applicable>
**Passport:** <immutable artifact link>

Limitations: <bounded scope and any gaps>.
```

## Integrity checks

Before publishing:

1. Recompute hashes for the exact source revisions, DataHub facts, fixtures, and outputs.
2. Confirm every critical consumer appears exactly once in the coverage ledger and has an evaluation or explicit gap.
3. Re-run a minimized counterexample independently when present.
4. Confirm the reviewer summary and machine-readable verdict agree.
5. Confirm any DataHub writeback can be read back and points to the same Passport ID.
