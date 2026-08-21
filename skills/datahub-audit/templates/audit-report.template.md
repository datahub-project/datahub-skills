# Audit Report

**Audit type:** <!-- e.g. Glossary Schema Consistency -->
**Scope:** <!-- term / group / full glossary, with names -->
**Terms checked:** <!-- count, business terms only -->
**Terms excluded (classification/sensitivity tags):** <!-- count and names, e.g. "PII" -->
**Fields checked:** <!-- count -->

## Summary

<!-- Direct answer first: how many inconsistencies found, and the highest-severity one. -->

## Findings

| Term          | Fields Checked | Status                   | Details                                                               |
| ------------- | -------------- | ------------------------ | --------------------------------------------------------------------- |
| <!-- name --> | <!-- count --> | Consistent / **Flagged** | <!-- e.g. "3/4 fields NUMBER(38,4); orders.total is NUMBER(38,2)" --> |

### Flagged fields (detail)

| Dataset      | Field         | Term          | Native Type               |
| ------------ | ------------- | ------------- | ------------------------- |
| <!-- urn --> | <!-- path --> | <!-- name --> | <!-- e.g. VARCHAR(50) --> |

<!-- One row per field. Fields with the same nativeDataType naturally group visually; no need to label why values differ — the raw values show it. -->

## Methodology

**Queries executed:** <!-- count -->
**Scope covered:** <!-- what was actually searched -->
**Excluded as classification/sensitivity tags:** <!-- term names + why (keyword match or structural signal) -->
**Limitations:**

- Coverage of the `glossary_term` search filter for field-level (vs. dataset-level) term applications is unconfirmed against this instance.
- <!-- any other caveats: group child-term resolution fallback used, pagination cap hit, ambiguous term flagged as possible classification tag, etc. -->

## Suggested Next Steps

- Fix a flagged field's documentation or schema → `/datahub-enrich`
- Pin the expected type going forward with a schema assertion → `/datahub-quality`
