# Privacy operations evidence contract

Use this contract to distinguish what DataHub can prove from what an external data-plane executor
must prove.

## Contents

- [Authority map](#authority-map)
- [Normalized evidence](#normalized-evidence)
- [Completeness rules](#completeness-rules)
- [Approval scopes](#approval-scopes)
- [DataHub write-back](#datahub-write-back)

## Authority map

| Claim                         | Authority                             | Minimum evidence                                            |
| ----------------------------- | ------------------------------------- | ----------------------------------------------------------- |
| Dataset exists                | DataHub `get_entities`                | Exact URN returned without entity error                     |
| Field is PII or a subject key | DataHub schema metadata               | Exact field plus explicit tag, term, or structured property |
| Asset is downstream           | DataHub `get_lineage`                 | Bounded path from a seed with complete page metadata        |
| Asset owner                   | DataHub entity metadata               | Explicit owner URN                                          |
| Handling or retention policy  | Organization-defined DataHub metadata | Exact value plus policy-source reference                    |
| Legal hold                    | Organization-defined DataHub metadata | Explicit hold value and source                              |
| Source-system action executed | Named external executor               | Job/transaction receipt bound to the approved scope         |
| Postcondition holds           | Named external executor               | Exact check plus residual count                             |
| DataHub accepted write-back   | MCP mutation response                 | Explicit non-error response for each exact target           |
| DataHub write-back is durable | Fresh read-only MCP session           | Exact tag, property, and document read-back                 |

DataHub metadata is never proof that a row was deleted from a warehouse or application database.

## Normalized evidence

Keep normalized evidence in ignored private storage when it contains tenant-specific metadata.
Public examples must be synthetic.

```json
{
  "caseId": "DSR-EXAMPLE-0042",
  "subjectHash": "sha256-or-hmac-hex",
  "observedAt": "2026-07-16T12:00:00Z",
  "boundary": "LIVE_DATAHUB_MCP",
  "bounds": {
    "maxAssets": 100,
    "maxFieldsPerAsset": 100,
    "maxLineageHops": 1
  },
  "coverage": {
    "assets": 7,
    "lineageEdges": 6,
    "piiFields": 19,
    "ownerCoveragePercent": 100,
    "paginationComplete": true,
    "truncated": false
  },
  "assets": [
    {
      "urn": "urn:li:dataset:(urn:li:dataPlatform:snowflake,db.schema.customers,PROD)",
      "owners": ["urn:li:corpGroup:privacy-engineering"],
      "subjectKeys": ["customer_id"],
      "piiFields": ["customer_id", "email"],
      "handlingRule": "ANONYMIZE",
      "policySource": "urn:li:document:privacy-policy-v3",
      "legalHold": false,
      "lineagePath": [
        "urn:li:dataset:(urn:li:dataPlatform:snowflake,db.schema.customers,PROD)"
      ],
      "evidenceRefs": ["mcp-call-03", "mcp-call-04"]
    }
  ],
  "provenance": {
    "mcpServer": "datahub",
    "toolCalls": 21,
    "toolInventoryHash": "sha256-hex",
    "rawEvidenceHash": "sha256-hex"
  }
}
```

The raw subject identifier is not a valid field in this object. Keep raw MCP payloads private,
hash them canonically, and reference their digest from the normalized evidence.

## Completeness rules

Treat transport success with an empty, malformed, truncated, or wrong-target payload as failure.

- `search`: record `offset`, returned count, explicit total when present, and active filter.
- `get_entities`: require every requested URN or an explicit per-URN error.
- `list_schema_fields`: paginate until the response proves completion; absence in the first page is
  not proof that a field does not exist.
- `get_lineage`: record direction, column, hop bound, result bound, offset, returned count, and
  whether more results exist.
- Related entity fetch: require metadata for every unique lineage URN before policy compilation.

If any required page or entity is missing, set `paginationComplete=false` or list the missing URNs
and stop with `BLOCKED`. Do not lower the count to the observed subset.

## Approval scopes

Create two independent canonical scopes.

### Execution scope

```json
{
  "caseId": "DSR-EXAMPLE-0042",
  "evidenceHash": "sha256-hex",
  "policyVersion": "privacy-policy-v3",
  "actions": [
    {
      "assetUrn": "urn:li:dataset:(...)",
      "action": "ANONYMIZE",
      "executor": "warehouse-privacy-runner",
      "postcondition": "matching_subject_rows = 0"
    }
  ],
  "protected": [
    {
      "assetUrn": "urn:li:dataset:(...)",
      "outcome": "RETAIN",
      "reason": "LEGAL_HOLD"
    }
  ]
}
```

### Write-back scope

```json
{
  "caseId": "DSR-EXAMPLE-0042",
  "executionScopeHash": "sha256-hex",
  "entityUrns": ["urn:li:dataset:(...)"],
  "tagUrns": ["urn:li:tag:PrivacyOperationVerified"],
  "propertyValues": {
    "urn:li:structuredProperty:privacy.caseId": ["DSR-EXAMPLE-0042"]
  },
  "document": {
    "urn": "urn:li:document:privacy-operation-dsr-example-0042",
    "title": "Privacy operation DSR-EXAMPLE-0042",
    "contentDigest": "sha256-hex"
  }
}
```

Canonicalize each scope as UTF-8 JSON with lexicographically sorted object keys, arrays sorted by
stable identifiers where order is not semantic, and no insignificant whitespace. Reject `NaN`
and infinite numbers. Hash with SHA-256.

Approval must include the exact current hash. A changed action, executor, policy, entity set,
property value, or document digest requires a new approval.

## DataHub write-back

Write back only non-sensitive operational evidence:

- case ID or opaque case reference;
- outcome state and observation time;
- approved scope hash;
- protected exception counts and owner routing;
- executor receipt references or digests;
- evidence document URN.

Never write:

- raw subject identifiers or reversible subject tokens;
- source-system row data;
- credentials or connection strings;
- private query text;
- legal analysis presented as organization policy.

Use `add_tags`, `add_structured_properties`, and `save_document` only after write-back approval.
Verify through `get_entities`, `search_documents`, and `grep_documents` from a fresh mutation-disabled
MCP session. Verify exact values, not merely document existence.
