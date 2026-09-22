# Incident memory record schema

One JSON document per resolved incident, stored as a value of the MULTIPLE-
cardinality structured property `io.datahub.incidentMemory` on every asset the
incident touched (affected asset + root-cause asset).

| Field | Type | Required | Purpose |
|---|---|---|---|
| `memory_id` | string | ✅ | Unique id (`im-<8 hex>`); cited on recall |
| `fingerprint` | string | ✅ | `sha256(failure_class \| lowercase(dataset_urn) \| sorted(columns))`, prefixed `fp-` — the exact-match key |
| `failure_class` | string | ✅ | Normalized taxonomy: `not_null`, `unique`, `accepted_values`, `relationships`, `freshness`, `missing_column`, `compilation_error`, `other` |
| `dataset_urn` | string | ✅ | Asset the symptom surfaced on |
| `columns` | string[] | — | Columns implicated (lowercased) |
| `source_incident` | string | ✅ | Incident id/urn this memory came from — recall must cite it |
| `root_cause` | string | ✅ | One-paragraph diagnosis, written for the next responder |
| `fix_summary` | string | ✅ | What actually fixed it (PR link, SQL, config change) |
| `blast_radius_urns` | string[] | — | Downstream assets affected, incl. ML features/models |
| `mttr_seconds` | number | — | Resolution time; lets recall report the expected saving |
| `created_at` | string | ✅ | ISO-8601; recency breaks match ties |

Design notes:

- **Why structured properties, not docs/tags:** machine-queryable, multiple
  records per asset, survives re-ingestion, visible in the UI Properties tab.
- **Why fingerprint + class ladder instead of embeddings:** recall must be
  explainable — "exact fingerprint match" and "same failure class on an
  upstream asset" are auditable claims a human can check; similarity scores
  are not.
- **Why write to the root-cause asset too:** the next incident may surface
  downstream on a *different* asset; the upstream walk finds the memory where
  the disease actually lives.
- **Consistency rule:** read memories with a direct entity get by URN. Search
  indexes update asynchronously after writes — search-based recall
  intermittently misses records written moments earlier.
