# Evidence bundle contract

Use this contract for preview and pre-write revalidation. Omit volatile transport timing
from the hash while retaining semantic source and catalog versions.

```json
{
  "change": {
    "request": "replace controlled source with approved public benchmark",
    "purpose": "external research collaboration",
    "requested_by": "urn:li:corpuser:requester"
  },
  "policy": {
    "source_digest": "sha256:<64 lowercase hex characters>",
    "rules": [
      {
        "id": "RULE-4",
        "conditions": ["classification=controlled"],
        "path_conditions": ["reachable external_access=true"],
        "exceptions": ["exception_approved=true"],
        "evidence_ids": ["ev-section-4", "ev-section-7"]
      }
    ]
  },
  "catalog": {
    "source": "datahub-mcp",
    "complete": true,
    "warnings": [],
    "assets": [],
    "lineage_edges": []
  },
  "decision": {
    "status": "BLOCK",
    "exposure_score": 100,
    "evidence_confidence": 0.84,
    "affected_urns": [],
    "findings": []
  },
  "evidence": [],
  "mutation_plan": [
    {
      "tool": "add_tags",
      "arguments": {
        "tag_urns": ["urn:li:tag:AuditedChange.BLOCK"],
        "entity_urns": ["urn:li:dataset:(...)"]
      }
    },
    {
      "tool": "add_structured_properties",
      "arguments": {
        "property_values": {
          "urn:li:structuredProperty:auditedChange.decisionId": ["change-..."]
        },
        "entity_urns": ["urn:li:dataset:(...)"]
      }
    },
    {
      "tool": "save_document",
      "arguments": {
        "document_type": "Decision",
        "title": "Auditable data change change-...",
        "content": "# Decision\n...",
        "topics": ["Audited change"],
        "related_assets": ["urn:li:dataset:(...)"]
      }
    }
  ]
}
```

## Canonicalization

Serialize as UTF-8 JSON with sorted keys and separators `,` and `:`. Do not include the
digest inside the hashed object. Prefix the lowercase hex result with `sha256:`.

Observation timestamps may appear in the report, but exclude them from the semantic
bundle when an unchanged re-read must preserve the digest. Changes to policy content,
assets, graph completeness, findings, or mutation payloads must change the digest.

## Approval record

Store the digest, approver, approval time, execution state, and per-mutation result outside
the hashed bundle. Reserve the digest before the first mutation and reject duplicates.
If a response is ambiguous, require investigation instead of retrying automatically.
