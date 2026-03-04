# Connector Feature Reference

Pull actual capabilities from the PR/connector code — this is a starting-point reference only.

## Asset types by connector category

| Category | Typical assets |
|----------|---------------|
| SQL databases | Tables, views, schemas, databases |
| Data warehouses | Tables, views, schemas, databases, materialized views, external tables |
| Orchestration | DataFlow (pipeline), DataJob (task/resource) |
| BI tools | Dashboards, charts, data sources |
| Streaming | Topics, schemas |
| dlt | DataFlow (dlt pipeline), DataJob (dlt resource), outlet lineage to destination |

## Feature → DataHub UI location

| Feature | Where to check |
|---------|---------------|
| Schema metadata | Column names, types, descriptions on dataset page |
| Lineage | Lineage tab on dataset/datajob page |
| Data profiling | Stats tab — row counts, null %, distributions |
| Usage statistics | Usage tab — query frequency, top users |
| Tags | Tag chips on dataset / column |
| Owners | Owners section on dataset page |
| Run history | DataJob page — run instances |
| Custom properties | Custom Properties section on dataset page |

## DataHub URL patterns

| Entity type | URL pattern |
|-------------|-------------|
| DataFlow | `<base>/pipelines/<url-encoded-urn>` |
| DataJob | `<base>/tasks/<url-encoded-urn>` |
| Dataset | `<base>/dataset/<url-encoded-urn>` |
| Dashboard | `<base>/dashboard/<url-encoded-urn>` |
| Search | `<base>/search?query=<name>` |
| Browse by platform | `<base>/browse?type=<type>&path=/<platform>` |

**URL-encode URNs** before inserting into links — replace `,` → `%2C`, `:` → `%3A`.
Example: `urn:li:dataFlow:(dlt,my_pipeline,PROD)` →
`urn%3Ali%3AdataFlow%3A(dlt%2Cmy_pipeline%2CPROD)`
