# Decision record schema

Use this logical schema even when the storage implementation uses a different
serialization format.

| Field                  | Required | Purpose                                                 |
| ---------------------- | -------- | ------------------------------------------------------- |
| `id`                   | Yes      | Stable identifier for this revision                     |
| `title`                | Yes      | Human-readable decision title                           |
| `status`               | Yes      | Pending, approved, revalidation required, or superseded |
| `proposed_action`      | Yes      | Action awaiting or carrying approval                    |
| `evidence.fetched_at`  | Yes      | UTC retrieval time                                      |
| `evidence.source`      | Yes      | Live DataHub MCP, another explicit source, or fixture   |
| `evidence.tools`       | Yes      | Exact tools used                                        |
| `evidence.snapshot`    | Yes      | Governed values used by the analysis                    |
| `dependencies`         | Yes      | DataHub asset URNs and relevant field paths             |
| `analysis`             | Yes      | Query, bounded result, chart, assumptions, and warnings |
| `approval`             | Yes      | Approval state, actor when available, and timestamp     |
| `supersedes`           | No       | Prior decision revision identifier                      |
| `datahub_document_urn` | No       | Verified DataHub write-back target                      |
| `projection_status`    | Yes      | Not configured, pending, synced, or retry required      |

## Evidence rules

- Store facts and reproducible artifacts, not hidden reasoning.
- Preserve exact URNs and field paths.
- Mark unavailable signals explicitly.
- Bound large query results and record that truncation occurred.
- Use a new record for new evidence; never rewrite the old snapshot.
