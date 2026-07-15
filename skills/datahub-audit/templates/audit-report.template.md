# DataHub Metadata Audit: <scope name>

**Audited at:** <timestamp>
**Scope:** <entity types, environment, platform/domain/container filters>
**Mode:** <core metadata / documentation / governance / custom>
**Coverage mode:** <full or sampled; sampling method if applicable>

## Executive Summary

<Two or three sentences with the population and most important evidence-backed findings.>

## Population Integrity

| Measure                   | Count | Notes                          |
| ------------------------- | ----: | ------------------------------ |
| Search total at start     |   <n> | <source query>                 |
| Physical entities fetched |   <n> | <pages succeeded / requested>  |
| Logical assets scored     |   <n> | <sibling policy>               |
| Unmeasured                |   <n> | <errors or unavailable fields> |

## Coverage

| Dimension                  | Covered | Eligible |    Coverage |        Target |      Gap |
| -------------------------- | ------: | -------: | ----------: | ------------: | -------: |
| Effective description      |     <n> |      <n> |        <x%> | <target or —> |      <n> |
| Ownership                  |     <n> |      <n> |        <x%> | <target or —> |      <n> |
| Domain                     |     <n> |      <n> |        <x%> | <target or —> |      <n> |
| <other measured dimension> |     <n> |      <n> | <x% or N/A> | <target or —> | <n or —> |

**Coverage score:** <only when explicitly requested; show formula and weights>

## Breakdown

| Platform or domain | Logical assets | Description | Ownership | Domain |
| ------------------ | -------------: | ----------: | --------: | -----: |
| <group>            |            <n> |        <x%> |      <x%> |   <x%> |

## Priority Gaps

| Priority | Asset  | Missing metadata | Evidence used             | URN     |
| -------: | ------ | ---------------- | ------------------------- | ------- |
|        1 | <name> | <dimensions>     | <tier/usage/lineage/etc.> | `<urn>` |

## Remediation Backlog

| Order | Action   |      Scope | Expected coverage change | Route             |
| ----: | -------- | ---------: | -----------------------: | ----------------- |
|     1 | <action> | <n assets> |    <dimension +n points> | `/datahub-enrich` |

## Methodology and Limitations

- **Effective metadata:** <editable, ingestion, and sibling precedence>
- **Sibling handling:** <physical count, logical grouping, canonical fallback>
- **Exclusions:** <policy-defined exclusions>
- **Sampling:** <none or exact reproducible method>
- **Unavailable dimensions:** <field/capability/permission reasons>
- **Query failures or count drift:** <details>
- **Interpretation:** This is a metadata coverage assessment, not regulatory certification.
