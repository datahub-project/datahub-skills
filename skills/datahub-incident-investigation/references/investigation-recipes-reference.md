# Investigation Recipes Reference

Copy-paste CLI and GraphQL recipes for `datahub-incident-investigation`, in the order an investigation needs them. All commands pass `-C skill=datahub-incident-investigation` for usage attribution; drop the flag if your CLI does not recognize it.

Placeholders: `<AFFECTED_ASSET_URN>`, `<SUSPECT_URN>`, `<ROOT_CAUSE_URN>`, `<INCIDENT_URN>`, `<COLUMN>`, `<PLATFORM>`.

For general CLI syntax see `../shared-references/datahub-cli-reference.md`. For assertion and subscription mutations see `../datahub-quality/references/`.

---

## 1. Find the Affected Asset

```bash
# From a name the reporter used
datahub -C skill=datahub-incident-investigation search "<NAME>" \
  --where "entity_type = dataset" --urns-only --limit 5

# From existing health signals, when the reporter has no specific asset
datahub -C skill=datahub-incident-investigation search "*" \
  --where "hasActiveIncidents = true OR hasFailingAssertions = true" \
  --projection "urn type ... on Dataset { properties { name } platform { name }
    health { type status message } }" \
  --format json --limit 20

# Column-name entry point: which datasets even contain the affected field?
datahub -C skill=datahub-incident-investigation search "*" \
  --where "entity_type = dataset AND fieldPaths = <COLUMN>" \
  --urns-only --limit 20
```

`health` is returned as a **list** of health entries (one per health type, e.g. `INCIDENTS`, `ASSERTIONS`), not a single object. Iterate it.

---

## 2. Retrieve the Contract

One query for meaning, ownership, and current health. The field descriptions are the contract you will test data against.

```bash
cat > /tmp/context.graphql << 'EOF'
query {
  dataset(urn: "<AFFECTED_ASSET_URN>") {
    urn
    properties { name description customProperties { key value } }
    editableProperties { description }
    ownership {
      owners {
        owner { ... on CorpUser { urn } ... on CorpGroup { urn } }
        ownershipType { urn }
      }
    }
    schemaMetadata { fields { fieldPath type nativeDataType description } }
    health { type status message }
  }
}
EOF
datahub -C skill=datahub-incident-investigation graphql --query /tmp/context.graphql --format json
rm /tmp/context.graphql
```

Gotchas:

- **Two description fields.** Ingestion writes `properties.description`; humans write `editableProperties.description`. Either can be `null` while the other is populated. Query both before concluding a field is undocumented.
- **`customProperties` often names the producer** — build tool, pipeline name, source system. That is your first hint about who owns the defect.
- **Long queries go in a file.** Inline `--query` strings past a certain length get read as file paths and fail with `File name too long` / `Errno 63`. Write to a temp file and pass the path; the CLI auto-detects.

Aspect-level fallback when you only need one thing:

```bash
datahub -C skill=datahub-incident-investigation get --urn "<AFFECTED_ASSET_URN>" --aspect schemaMetadata
datahub -C skill=datahub-incident-investigation get --urn "<AFFECTED_ASSET_URN>" --aspect ownership
```

---

## 3. Localize with Lineage

```bash
# Upstream suspect set
datahub -C skill=datahub-incident-investigation lineage \
  --urn "<AFFECTED_ASSET_URN>" --direction upstream --hops 3

# Column-level: only the assets that feed the affected field
datahub -C skill=datahub-incident-investigation lineage \
  --urn "<AFFECTED_ASSET_URN>" --column "<COLUMN>" --direction upstream --hops 3

# Downstream blast radius, once a cause is confirmed
datahub -C skill=datahub-incident-investigation lineage \
  --urn "<ROOT_CAUSE_URN>" --direction downstream --hops 3 --format json

# Confirm a specific route
datahub -C skill=datahub-incident-investigation lineage path \
  --from "<SUSPECT_URN>" --to "<AFFECTED_ASSET_URN>"
```

Output notes:

- The summary line reports entity count, max hop depth, and whether results were **capped**. If capped, raise `--count`.
- `hops` in the output is distance from the queried URN; hop 1 is the immediate neighbour.
- `datahub lineage` returns URN, name, type, platform, and hop only. It does **not** support `--projection` — enrich separately (next recipe).
- Zero edges means lineage was never ingested for that asset. Report that as a gap, not as "no dependencies."

### Batch-enrich the frontier

One call instead of N. Quote the URNs — they contain parentheses and commas.

```bash
datahub -C skill=datahub-incident-investigation search "*" \
  --where 'urn IN ("<SUSPECT_URN_1>", "<SUSPECT_URN_2>")' \
  --projection "urn ... on Dataset { properties { name }
    ownership { owners { owner { ... on CorpUser { urn } } } }
    health { type status message } }" \
  --format json --limit 50
```

`urn` is a passthrough filter rather than a named one, but it works and avoids the N+1 fetch.

---

## 4. Date the Change

```bash
# Schema changes with compatibility classification
datahub -C skill=datahub-incident-investigation timeline \
  --urn "<SUSPECT_URN>" --category technical_schema --start 30daysago

# Contract drift — did the documentation change instead of the data?
datahub -C skill=datahub-incident-investigation timeline \
  --urn "<SUSPECT_URN>" --category documentation --start 30daysago

# Ownership handoffs often bracket a behaviour change
datahub -C skill=datahub-incident-investigation timeline \
  --urn "<SUSPECT_URN>" --category owner --start 30daysago
```

Categories: `technical_schema`, `documentation`, `owner`, `tag`, `glossary_term`.

Timeline output is one block per version stamp, each line prefixed `ADD` / `MODIFY` / `REMOVE` with the affected field and a compatibility note. Match those timestamps against the last-good → first-bad window from Step 1.

When the pipeline source is in a readable repository, bracket the same window in version control:

```bash
git log --since="<LAST_GOOD_DATE>" --until="<FIRST_BAD_DATE>" --oneline -- <TRANSFORM_DIR>
git diff <LAST_GOOD_COMMIT>..<FIRST_BAD_COMMIT> -- <TRANSFORM_FILE>
git blame -L <START>,<END> -- <TRANSFORM_FILE>
```

Read the transformation that produces the affected column before proposing anything. A cause you cannot point at in code is a cause you cannot fix.

---

## 5. Quantify (Your Warehouse, Not DataHub)

DataHub holds metadata; the values live in your warehouse or query engine. This skill emits SQL for the user or their own approved data tooling to run, and records the returned numbers as evidence. Keep it portable ANSI SQL so it runs anywhere.

### Segmented profile — the workhorse

```sql
SELECT
  <PERIOD_COLUMN>       AS period,
  <SEGMENT_COLUMN>      AS segment,
  COUNT(*)              AS row_count,
  AVG(<SUSPECT_COLUMN>) AS mean_value,
  MIN(<SUSPECT_COLUMN>) AS min_value,
  MAX(<SUSPECT_COLUMN>) AS max_value,
  SUM(CASE WHEN <SUSPECT_COLUMN> IS NULL THEN 1 ELSE 0 END) AS null_count
FROM <SUSPECT_TABLE>
WHERE <PERIOD_COLUMN> >= <WINDOW_START>
GROUP BY 1, 2
ORDER BY 1, 2;
```

### Onset detection — first period that leaves the band

```sql
SELECT <PERIOD_COLUMN> AS period,
       SUM(<METRIC_COLUMN>) AS actual,
       AVG(SUM(<METRIC_COLUMN>)) OVER (
         ORDER BY <PERIOD_COLUMN> ROWS BETWEEN 14 PRECEDING AND 1 PRECEDING
       ) AS trailing_mean
FROM <TABLE>
GROUP BY 1
ORDER BY 1;
```

The first period where `actual / trailing_mean` leaves its historical band is the onset. Every candidate change dated outside `[last_good, first_bad]` is eliminated.

### Contract ratio check — semantic failures

```sql
SELECT <SEGMENT_COLUMN>,
       AVG(<SUSPECT_COLUMN>) / NULLIF(AVG(<REFERENCE_COLUMN>), 0) AS ratio_to_reference
FROM <SUSPECT_TABLE>
GROUP BY 1;
```

A ratio clustering on a round factor (100, 1000, 60, 1024) in exactly one segment is a unit, scale, or encoding defect.

### Fan-out check — where row counts multiply

```sql
SELECT '<STAGE_NAME>' AS stage, COUNT(*) AS row_count,
       COUNT(DISTINCT <GRAIN_KEY>) AS distinct_grain
FROM <STAGE_TABLE>;
```

Run once per stage on the path. The hop where `row_count` diverges from `distinct_grain` is where the join fanned out.

---

## 6. Read Existing Quality Signals

Assertion history tells you when a check first failed — often a sharper onset than any profile.

```bash
cat > /tmp/health.graphql << 'EOF'
query {
  dataset(urn: "<AFFECTED_ASSET_URN>") {
    assertions(start: 0, count: 50) {
      total
      assertions {
        urn
        info { type description }
        runEvents(limit: 5) { runEvents { timestampMillis status result { type } } }
      }
    }
    incidents(state: ACTIVE, start: 0, count: 20) {
      total
      incidents {
        urn incidentType title priority
        incidentStatus { state stage message }
        created { time actor }
      }
    }
  }
}
EOF
datahub -C skill=datahub-incident-investigation graphql --query /tmp/health.graphql --format json
rm /tmp/health.graphql
```

Notes:

- There is **no top-level `incident(urn: ...)` query** on DataHub OSS — asking for one fails with `FieldUndefined`. Reach incidents through the owning entity's `incidents(...)` connection, or fetch the aspect directly:

  ```bash
  datahub -C skill=datahub-incident-investigation get --urn "<INCIDENT_URN>"
  # → { "incidentInfo": { "status": { "state": ..., "stage": ... }, "entities": [...] }, "incidentKey": {...} }
  ```

- Omit the `state:` argument on `incidents(...)` to see resolved history as well as active — prior resolved incidents on the same asset are the best possible prior.
- **No failing assertions does not mean healthy.** Semantic defects pass every threshold. Absence of an assertion signal is not evidence of correctness.

---

## 7. Write the Resolution Back

Incident mutations work on DataHub OSS as well as Cloud. Verified against OSS (`serverEnv: core`).

```bash
# Resolve, with the root cause in the message
datahub -C skill=datahub-incident-investigation graphql --query 'mutation {
  updateIncidentStatus(urn: "<INCIDENT_URN>", input: {
    state: RESOLVED, stage: FIXED,
    message: "Root cause: <ONE_SENTENCE_CAUSE>. Remediation applied at <LAYER>; verified <DATE>."
  })
}' --format json
# → { "updateIncidentStatus": true }
```

```bash
# Park an in-flight investigation without closing it
datahub -C skill=datahub-incident-investigation graphql --query 'mutation {
  updateIncidentStatus(urn: "<INCIDENT_URN>", input: {
    state: ACTIVE, stage: WORK_IN_PROGRESS,
    message: "Root cause confirmed; remediation pending owner approval."
  })
}' --format json
```

```bash
# Attach the RCA report as institutional memory on the origin asset
datahub -C skill=datahub-incident-investigation graphql --query 'mutation {
  addLink(input: {
    linkUrl: "<RCA_DOC_URL>", label: "RCA: <INCIDENT_TITLE>",
    resourceUrn: "<ROOT_CAUSE_URN>"
  })
}' --format json
# → { "addLink": true }
```

If no incident existed when you started, raise one so the diagnosis is recorded, then resolve it in the same pass (`raiseIncident` — see `../datahub-quality/references/incident-subscription-reference.md`).

Stages: `TRIAGE` → `INVESTIGATION` → `WORK_IN_PROGRESS` → `FIXED` / `NO_ACTION_REQUIRED`. Use `NO_ACTION_REQUIRED` for a verified "not an incident" outcome — it preserves the investigation without implying a defect existed.

Verify the writeback landed:

```bash
datahub -C skill=datahub-incident-investigation get --urn "<INCIDENT_URN>"
```

---

## 8. Close the Prevention Loop

| Finding                                   | Follow-up                                                       |
| ----------------------------------------- | --------------------------------------------------------------- |
| The contract was ambiguous or wrong       | Fix the field description — `/datahub-enrich`                   |
| No check would have caught this           | Propose an assertion at the origin asset — `/datahub-quality`   |
| Nobody was notified                       | Propose a subscription for the owning team — `/datahub-quality` |
| The origin asset had no owner             | Assign one — `/datahub-enrich`                                  |
| Lineage was missing and slowed the search | Flag the ingestion gap for the platform team                    |

Prevention proposals are recommendations, not writes. Present them and let the owners decide.

---

## GraphQL Practices for Investigations

1. **Introspect rather than guess.** `datahub graphql --describe <operation> --recurse --format json` shows the live schema. Never invent field names from memory.
2. **`--strip-unknown-fields` on reads only.** It silently drops unrecognized fields instead of failing — useful when a query spans OSS and Cloud. Never use it on mutations.
3. **`--variables` for URN-bearing mutations.** Dataset URNs contain `(`, `)`, and `,` which break shell escaping.
4. **Temp files for long queries.** Pass the path to `--query`; clean up with `rm`.
5. **Stop on the first error.** Report what succeeded, what failed, and ask before continuing.
6. **Do not disable telemetry.** Ignore telemetry prompts.
