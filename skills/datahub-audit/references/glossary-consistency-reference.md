# Glossary Schema Consistency — Query Reference

Detailed query patterns, comparison algorithm, and cost thresholds for the Glossary Schema Consistency audit. See `SKILL.md` for the step-by-step workflow this supports.

## 1. Resolving names to URNs

Never guess a term, group, or dataset URN — always resolve by search first.

```bash
# Term
datahub search "Revenue" --where "entity_type = glossaryTerm" --urns-only --limit 5

# Group (glossaryNode)
datahub search "Finance" --where "entity_type = glossaryNode" --urns-only --limit 5
```

Glossary term URNs look like `urn:li:glossaryTerm:Revenue` (or a namespaced path, e.g. `urn:li:glossaryTerm:Finance.Revenue`, depending on how the term was created). Groups are `urn:li:glossaryNode:<id>`.

## 2. Excluding classification and sensitivity terms

This audit is for **business terms** — a term that names one specific quantity or attribute (`Revenue`, `Maturity Amount`, `Trade Date`), which should be represented identically everywhere it's used. It is not for classification/sensitivity tags (`PII`, `PHI`, `PCI`, `Confidential`, `Sensitive`, `Restricted`) — those are applied across structurally unrelated fields by design.

Before building the scope filter, check every resolved term's name (case-insensitive) against a starting keyword list: `PII`, `PHI`, `PCI`, `Confidential`, `Sensitive`, `Restricted`, `Classification`, `Sensitivity`, `GDPR`, `CCPA`, `HIPAA`. Extend it with obvious synonyms you encounter — it isn't exhaustive.

- Single term matches → tell the user this audit isn't designed for classification/sensitivity tags and stop, rather than running it.
- Group or full sweep → drop matching terms before building the Section 3 filter. Report which terms were excluded and why in the Methodology/Limitations section.

Confirmed against a real production instance: `PII` was applied to 25+ fields split roughly 18 `INT64` (ID columns) / 8 `STRING` (name columns), spanning dataset names with nothing in common (`pet_details.pet_fk`, `dog_rates_twitter.name`, `clicksandmortar_communities.pk`). That split is completely expected for a sensitivity tag and would be a false positive if compared as if `PII` named one quantity.

A term can slip past the name filter (unfamiliar or internal vocabulary). Section 7 keeps a lighter structural check as a safety net for exactly that case.

## 3. Building one filter for the whole scope

Never loop a query per term — one filter covers a single term, a whole group, or the whole glossary:

```bash
# Single term
--where "entity_type = dataset AND glossary_term = '<term urn>'"

# Group (child term URNs resolved in SKILL.md Step 1) — fine up to ~30 terms
--where "entity_type = dataset AND glossary_term IN ('<urn1>', '<urn2>', '<urn3>')"

# Full sweep, or a group too large for a clean IN list — filter by term client-side instead (Step 4 below)
--where "entity_type = dataset AND glossary_term IS NOT NULL"
```

For full-glossary context (not a gate — see Section 8), it's fine to also enumerate term count separately:

```bash
datahub search "*" --where "entity_type = glossaryTerm" --format json --limit 50 --offset 0
# repeat with --offset 50, 100, ... until a page returns fewer than 50 results
```

## 4. Checking the real cost before fetching schemas

```bash
datahub search "*" --where "entity_type = dataset AND <scope filter from Section 3>" --format json --limit 1
```

Read `count` from the response envelope — that's the exact number of datasets the next step will fetch full field-level schema for. This is a direct measurement of cost, not a proxy: a glossary with thousands of terms can still resolve to a handful of tagged datasets, so check this number before assuming a full sweep needs confirmation (see Section 8 for the threshold).

## 5. Field-level projection for the whole scope

Combine the scope filter from Section 3 with a projection that pulls both the ingestion-provided and user-edited term locations, plus type info, paginating 50 at a time:

```bash
datahub search "*" --where "entity_type = dataset AND <scope filter from Section 3>" \
  --projection "urn type ... on Dataset {
    properties { name }
    platform { name }
    schemaMetadata {
      fields { fieldPath type nativeDataType glossaryTerms { terms { term { urn } } } }
    }
    editableSchemaMetadata {
      editableSchemaFieldInfo { fieldPath glossaryTerms { terms { term { urn } } } }
    }
  }" --format json --limit 50 --offset 0
```

Field name reminder (per the "editable vs. non-editable" convention already documented in `skills/datahub-search/SKILL.md`): a field carries a term if it appears in **either** `schemaMetadata.fields[].glossaryTerms` **or** `editableSchemaMetadata.editableSchemaFieldInfo[].glossaryTerms` for the same `fieldPath`. Check both — don't rely on one alone.

**Unconfirmed:** whether the `glossary_term` filter's index includes terms applied only at the field level, or only dataset-level term applications. Don't assume completeness — call this out in the audit report's Methodology section every time this audit runs.

For a group or full sweep, a field can carry more than one in-scope term — bucket it under every matching term, not just the first one found.

## 6. `nativeDataType` is the only comparison signal

`nativeDataType` is confirmed by this repo's docs (referenced in `standards/sql.md`, `standards/patterns.md`, `standards/testing.md` as the raw type string reported by the source system, e.g. `NUMBER(38,4)`, `VARCHAR(255)`). It is the comparison signal for this audit.

**`nullable` is deliberately excluded**, not just unconfirmed. Whether a field allows nulls legitimately varies by dataset and business context — a field required in one system may be optional in another for reasons unrelated to schema drift. Comparing it would produce false positives disguised as findings, not real inconsistencies. Discrete `precision`/`scale` fields (as opposed to reading them out of the `nativeDataType` string) are unnecessary for the same reason `nativeDataType` already usually encodes them — don't add a projection field just to duplicate what's already in the string.

## 7. Comparing `nativeDataType` strings

Group all matched fields (from Section 5) by term URN — every term here has already passed the Section 2 exclusion, so a divergence found now is a real candidate finding. Within a group:

1. Group fields by their **exact** `nativeDataType` string and count each distinct value.
2. If there's only one distinct value → consistent, no flag.
3. If there's more than one → report every distinct value with its field count and the specific dataset/field pairs, and stop there. Don't classify _why_ the values differ (base type vs. precision vs. length) — the raw values already show that to any reader. `NUMBER(38,2)` next to `NUMBER(38,4)` is legible as a precision difference without a label; `STRING` next to `DATE` is legible as a representation difference the same way.

**Why not parse `nativeDataType` into (base type, size)?** A fixed pattern like `TYPE(args)` doesn't hold universally — confirmed on a real instance, some sources populate `nativeDataType` with a plain descriptive label (`"Market Value"`, `"Maybe"`) instead of a DB type string, where there's nothing to parse at all. Grouping by exact string works identically in both cases; a parsing rule only works for one of them and silently produces nothing useful for the other.

**Safety net for terms that passed Section 2's name filter but still look like a tag:** if a term shows the same signals described there (15+ fields, no resemblance between field paths or dataset names) despite not matching the keyword list, don't assert a confident defect — report it as "possible classification tag, not confirmed as drift" instead.

## 8. Cost thresholds summary

There's one threshold, checked the same way regardless of scope: **candidate dataset count**, measured directly with the Section 4 `--limit 1` check before fetching any schemas.

| Scope         | Gate                | Action                                                                                                         |
| ------------- | ------------------- | -------------------------------------------------------------------------------------------------------------- |
| Single term   | dataset count > 100 | Stop, show count, confirm before fetching schemas (mirrors `/datahub-search`'s >100-entity threshold)          |
| Group         | dataset count > 100 | Same gate — the group's term count doesn't matter once it's one query                                          |
| Full glossary | dataset count > 100 | Same gate. Term count (Section 3) is useful context to show alongside it, but isn't what triggers confirmation |

Term count is no longer a gate on its own — it stopped being the cost driver once querying moved from "one call per term" to "one call for the whole scope." A glossary with thousands of terms but few tagged datasets costs almost nothing to sweep.
