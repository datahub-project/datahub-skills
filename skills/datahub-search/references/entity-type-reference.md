# Entity Type Quick Reference

## Entity Types for Search

| User Mentions | Entity Type Filter | DataHub Entity |
| --- | --- | --- |
| tables, views, topics, files, datasets | `dataset` | dataset |
| dashboards, reports | `dashboard` | dashboard |
| charts, visualizations, widgets | `chart` | chart |
| pipelines, DAGs, workflows, data flows | `dataFlow` | dataFlow |
| tasks, jobs, operators | `dataJob` | dataJob |
| databases, schemas, folders, projects | `container` | container |
| glossary terms, business terms | `glossaryTerm` | glossaryTerm |
| tags, labels | `tag` | tag |
| domains, business domains | `domain` | domain |
| users, people | `corpuser` | corpuser |
| groups, teams | `corpGroup` | corpGroup |
| data products | `dataProduct` | dataProduct |
| ML models, machine learning | `mlModel` | mlModel |
| structured properties, custom properties | `structuredProperty` | structuredProperty |

## URN Format Quick Reference

```
dataset:       urn:li:dataset:(urn:li:dataPlatform:PLATFORM,QUALIFIED_NAME,ENV)
dashboard:     urn:li:dashboard:(urn:li:dataPlatform:PLATFORM,ID)
chart:         urn:li:chart:(urn:li:dataPlatform:PLATFORM,ID)
dataFlow:      urn:li:dataFlow:(urn:li:dataPlatform:PLATFORM,FLOW_ID,CLUSTER)
dataJob:       urn:li:dataJob:(urn:li:dataFlow:(PLATFORM,FLOW_ID,CLUSTER),JOB_ID)
container:     urn:li:container:GUID
glossaryTerm:  urn:li:glossaryTerm:NAME
tag:           urn:li:tag:NAME
domain:        urn:li:domain:GUID
corpuser:      urn:li:corpuser:ID
corpGroup:     urn:li:corpGroup:ID
dataProduct:   urn:li:dataProduct:GUID
structuredProperty:  urn:li:structuredProperty:QUALIFIED_NAME
```

## Common Platforms

| Platform | DataHub ID |
| --- | --- |
| Snowflake | `snowflake` |
| BigQuery | `bigquery` |
| Redshift | `redshift` |
| PostgreSQL | `postgres` |
| MySQL | `mysql` |
| Databricks | `databricks` |
| dbt | `dbt` |
| Airflow | `airflow` |
| Looker | `looker` |
| Tableau | `tableau` |
| Kafka | `kafka` |
| Spark | `spark` |
| Hive | `hive` |
| S3 | `s3` |
| Power BI | `powerbi` |
