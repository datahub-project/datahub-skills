# Metadata Coverage Audit

## Scope

| Parameter | Value |
| --- | --- |
| Entity type | <!-- dataset / dashboard / etc. --> |
| Platform | <!-- snowflake / bigquery / all --> |
| Environment | <!-- PROD / DEV / all --> |
| Domain | <!-- domain name or "all" --> |
| Total entities | <!-- N --> |
| Audit date | <!-- date --> |

---

## Coverage Summary

| Dimension | With | Without | Coverage % | Status |
| --- | --- | --- | --- | --- |
| Description | <!-- N --> | <!-- N --> | <!-- N% --> | <!-- 🟢 / 🟡 / 🔴 --> |
| Ownership | <!-- N --> | <!-- N --> | <!-- N% --> | <!-- 🟢 / 🟡 / 🔴 --> |
| Tags | <!-- N --> | <!-- N --> | <!-- N% --> | <!-- 🟢 / 🟡 / 🔴 --> |
| Glossary terms | <!-- N --> | <!-- N --> | <!-- N% --> | <!-- 🟢 / 🟡 / 🔴 --> |
| Domain assignment | <!-- N --> | <!-- N --> | <!-- N% --> | <!-- 🟢 / 🟡 / 🔴 --> |

**Overall score:** <!-- weighted average or summary -->

---

## Entities Needing Attention

### Missing Descriptions

| Entity | Platform | Owner | Tags |
| --- | --- | --- | --- |
| <!-- name --> | <!-- platform --> | <!-- owner or "unowned" --> | <!-- tags or "none" --> |

### Missing Owners

| Entity | Platform | Description | Tags |
| --- | --- | --- | --- |
| <!-- name --> | <!-- platform --> | <!-- snippet or "none" --> | <!-- tags or "none" --> |

### Missing Tags

| Entity | Platform | Owner | Description |
| --- | --- | --- | --- |
| <!-- name --> | <!-- platform --> | <!-- owner or "unowned" --> | <!-- snippet or "none" --> |

### Missing Domain Assignment

| Entity | Platform | Owner |
| --- | --- | --- |
| <!-- name --> | <!-- platform --> | <!-- owner or "unowned" --> |

---

## Field-Level Coverage (if measured)

| Entity | Total columns | Documented | Undocumented | Column coverage % |
| --- | --- | --- | --- | --- |
| <!-- name --> | <!-- N --> | <!-- N --> | <!-- N --> | <!-- N% --> |

---

## Recommendations

1. <!-- Highest-impact action — e.g. "Add descriptions to the 12 most-queried tables" -->
2. <!-- Second action — e.g. "Assign owners to unowned datasets in the Finance domain" -->
3. <!-- Third action — e.g. "Apply PII tags to columns identified in the schema audit" -->

## Next Steps

- To fix descriptions and ownership: use `/datahub-enrich`
- To set up quality assertions on critical tables: use `/datahub-quality`
- To explore lineage for undocumented tables: use `/datahub-lineage`
