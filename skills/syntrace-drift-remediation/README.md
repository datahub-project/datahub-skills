# Syntrace Drift Remediation

Detect breaking schema changes in a DataHub-cataloged pipeline and drive the full
detect → trace → fix → PR → write-back loop using
[Syntrace](https://github.com/mrnetwork0001/Syntrace), an open-source (Apache-2.0)
autonomous remediation agent built on live DataHub metadata.

## What it does

1. Diffs the dataset's versioned `schemaMetadata` aspects to detect renames, drops, adds, and type changes
2. Traces the column-level downstream blast radius via the DataHub MCP Server (GraphQL fallback)
3. Rewrites the affected dbt SQL and Airflow DAG code deterministically
4. Prepares a GitHub remediation PR (dry-run by default)
5. Writes the healed metadata back to DataHub: fine-grained lineage, renamed schema fields, a `syntrace-remediated` tag, and documentation notes

## Capabilities

- **Drift detection** — versioned-schema diffing with rename matching
- **Impact analysis** — exactly which downstream columns of which assets break, and how many hops away
- **Code remediation** — first-try-valid dbt SQL and Airflow DAG fixes
- **Catalog write-back** — the catalog reflects the healed pipeline immediately

## Usage

```
> a column was renamed upstream - what breaks and how do we fix it?
> run Syntrace on raw.orders and show me the blast radius
> remediate the drifted dataset and open the PR for real
```

## Requirements

A checkout of [Syntrace](https://github.com/mrnetwork0001/Syntrace) plus a reachable
DataHub Core instance (see the Syntrace README quickstart; hosted demo at
<https://syntraceapp.xyz>).
