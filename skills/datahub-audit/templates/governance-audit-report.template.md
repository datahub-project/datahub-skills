# Governance Audit Report

## Scope

| Parameter | Value |
| --- | --- |
| Entity type | <!-- dataset / all --> |
| Platform | <!-- platform or "all" --> |
| Environment | <!-- PROD / all --> |
| Audit date | <!-- date --> |
| Total entities | <!-- N --> |

---

## Governance Summary

| Check | Compliant | Non-compliant | Coverage % | Status |
| --- | --- | --- | --- | --- |
| Domain assignment | <!-- N --> | <!-- N --> | <!-- N% --> | <!-- 🟢 / 🟡 / 🔴 --> |
| Data product membership | <!-- N --> | <!-- N --> | <!-- N% --> | <!-- 🟢 / 🟡 / 🔴 --> |
| Deprecation hygiene | <!-- N clean --> | <!-- N at-risk --> | <!-- N% --> | <!-- 🟢 / 🟡 / 🔴 --> |
| PII classification | <!-- N --> | <!-- N --> | <!-- N% --> | <!-- 🟢 / 🟡 / 🔴 --> |

---

## Domain Assignment Gaps

Entities not assigned to any domain:

| Entity | Platform | Owner |
| --- | --- | --- |
| <!-- name --> | <!-- platform --> | <!-- owner or "unowned" --> |

---

## Data Product Gaps

Entities not in any data product:

| Entity | Platform | Domain | Owner |
| --- | --- | --- | --- |
| <!-- name --> | <!-- platform --> | <!-- domain or "none" --> | <!-- owner or "unowned" --> |

---

## Deprecation Risks

Deprecated entities with active downstream consumers:

| Entity | Platform | Deprecated Since | Active Consumers | Risk |
| --- | --- | --- | --- | --- |
| <!-- name --> | <!-- platform --> | <!-- date --> | <!-- N consumers --> | <!-- HIGH / MEDIUM --> |

---

## PII Classification Gaps

Datasets with PII columns but no entity-level PII tag:

| Entity | Platform | PII Columns | Entity Tagged |
| --- | --- | --- | --- |
| <!-- name --> | <!-- platform --> | <!-- column list --> | No |

---

## Recommendations

1. <!-- Highest-impact governance action -->
2. <!-- Second action -->
3. <!-- Third action -->

## Next Steps

- To assign domains and data products: use `/datahub-enrich`
- To tag PII entities: use `/datahub-enrich`
- To check lineage for deprecated entities: use `/datahub-lineage`
