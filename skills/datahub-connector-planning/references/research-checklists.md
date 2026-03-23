# Research Checklists

## Contents

- [SQL Sources](#sql-sources)
- [API Sources](#api-sources)
- [NoSQL Sources](#nosql-sources)
- [User Questions](#user-questions)

## SQL Sources

| Category       | Question                        | Answer                              |
| -------------- | ------------------------------- | ----------------------------------- |
| **Connection** | SQLAlchemy dialect available?   | Yes/No/Partial                      |
| **Connection** | Official Python SDK/client?     | Yes/No                              |
| **Connection** | Docker image for testing?       | Yes/No                              |
| **Auth**       | Authentication methods?         | Basic/OAuth/Token/API Key           |
| **Hierarchy**  | Two-tier or three-tier?         | schema.table / catalog.schema.table |
| **Metadata**   | View definitions accessible?    | Yes/No                              |
| **Lineage**    | Query logs available?           | Yes/No                              |
| **Similar**    | Most similar DataHub connector? | (connector name)                    |

## API Sources

For API sources (BI, orchestration, streaming, ML, identity, analytics):

| Category        | Question                           | Answer                     |
| --------------- | ---------------------------------- | -------------------------- |
| **API Type**    | REST API or GraphQL?               | REST/GraphQL/Both          |
| **API Docs**    | Public API documentation URL?      | (link)                     |
| **Auth**        | Authentication method?             | OAuth2/API Key/Token/Basic |
| **Auth**        | OAuth2 scopes needed (if OAuth)?   | (list scopes)              |
| **Pagination**  | Pagination style?                  | Cursor/Offset/Page/None    |
| **Rate Limits** | Rate limit details?                | (requests/sec or similar)  |
| **SDK**         | Official Python SDK available?     | Yes/No                     |
| **Webhooks**    | Webhook support (for incremental)? | Yes/No                     |
| **Similar**     | Most similar DataHub connector?    | (connector name)           |

## NoSQL Sources

| Category       | Question                                      | Answer                            |
| -------------- | --------------------------------------------- | --------------------------------- |
| **Driver**     | Native Python driver available?               | Yes/No (name)                     |
| **Connection** | Docker image for testing?                     | Yes/No                            |
| **Auth**       | Authentication methods?                       | Username+Password/IAM/Certificate |
| **Schema**     | Schema registry or definition available?      | Yes/No                            |
| **Schema**     | If no schema: document structure predictable? | Yes/No                            |
| **Scale**      | Number of collections/tables expected?        | (estimate)                        |
| **Similar**    | Most similar DataHub connector?               | (connector name)                  |

## User Questions

Ask the user these questions (select variants matching the source category):

1. **Test environment**: Do you have a test instance, or should we plan for Docker-based testing?

2. **Permissions**: What access does your test account have? _(ask the relevant variant)_

   For SQL sources:
   - Basic metadata (tables, columns)?
   - View definitions?
   - Query logs (for lineage)?

   For API sources:
   - Admin or read-only API access?
   - Which API scopes/permissions are granted?

   For NoSQL sources:
   - Read access to all collections/tables?
   - Access to schema definitions (if any)?

3. **Feature scope**: Which features should we prioritize? _(ask the relevant variant)_

   For SQL sources (sql_databases, data_warehouses, query_engines, data_lakes):
   - A) Basic metadata only (tables, views, columns, containers)
   - B) Basic + lineage
   - C) Full features (lineage + usage statistics)

   For BI tools (bi_tools, product_analytics):
   - A) Dashboards and charts only
   - B) Dashboards + charts + lineage to upstream datasets
   - C) Full features (lineage + ownership + tags)

   For orchestration tools:
   - A) Pipelines/DAGs and tasks only
   - B) Pipelines + job lineage (input/output datasets)
   - C) Full features (lineage + ownership + tags)

   For streaming platforms:
   - A) Topics and schemas only
   - B) Topics + schemas + container hierarchy
   - C) Full features (consumer groups + producer/consumer lineage)

   For ML platforms:
   - A) Models and model groups only
   - B) Models + training dataset lineage
   - C) Full features (experiments + lineage + ownership)

   For identity platforms:
   - A) Users only
   - B) Users + groups
   - C) Full features (users + groups + group membership)

   For NoSQL databases:
   - A) Collections/tables with inferred schema only
   - B) Collections + container hierarchy
   - C) Full features (containers + schema inference tuning)
