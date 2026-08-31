# Evidence state and impact reference

## Evidence states

| State      | Meaning                                     | Forensic rule                                   |
| ---------- | ------------------------------------------- | ----------------------------------------------- |
| `OBSERVED` | Captured from runtime telemetry/tool result | Strongest recorded use; still not factual truth |
| `DECLARED` | Supplied by owner/configuration             | Do not describe as runtime-observed             |
| `INFERRED` | Derived by a named rule and confidence      | Report rule/version and confidence              |
| `UNKNOWN`  | Provenance is missing or unresolved         | Preserve uncertainty; never auto-clear          |

Roles (`INPUT`, `REFERENCE`, `CONSTRAINT`, `POLICY`, `MEMORY`, `OUTPUT_TARGET`)
describe how evidence influenced the run. A glossary or freshness change is more
likely material when the matching evidence was a constraint or policy.

## Closed impact states

- `UNAFFECTED`: requires positive exclusion proof.
- `STALE`: a recorded material dependency changed.
- `AT_RISK`: impact is plausible but evidence or field lineage is incomplete.
- `UNKNOWN`: the available graph cannot support a classification.
- `SUPERSEDED`: a newer verified receipt already replaces the decision.

Never use absence from an incomplete index as proof of `UNAFFECTED`.

## High-value reason codes

- `OBSERVED_MATERIAL_DEPENDENCY_CHANGED` → `STALE`.
- `MATCHED_DEPENDENCY_NOT_OBSERVED` → `AT_RISK`.
- `FIELD_LINEAGE_INCOMPLETE_OR_WILDCARD_UNKNOWN` → `AT_RISK`.
- `COMPLETE_FIELD_LINEAGE_PROVES_FIELD_UNUSED` → `UNAFFECTED`.
- `UNRESOLVED_DEPENDENCY_PREVENTS_ASSET_EXCLUSION` → `UNKNOWN`.
- `RECEIPT_ALREADY_SUPERSEDED` → `SUPERSEDED`.
- `MATCHED_POST_CHANGE_SNAPSHOT` → `UNAFFECTED` for that change snapshot.

Use a configured deterministic classifier for exact results. The table explains
output; it is not a replacement implementation.
