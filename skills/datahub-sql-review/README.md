# DataHub SQL Review

Check SQL against the catalog before it ships. Resolves every table and column
the statement references, so a hallucinated column is caught in review rather
than in production.

## What it does

1. Extracts the tables and columns the statement reads and writes
2. Resolves each one against DataHub
3. Grades findings by how strong the evidence is
4. Reports what the catalog proves, disproves, and cannot speak to

## Checks

| Check             | What it catches                                     |
| ----------------- | --------------------------------------------------- |
| Phantom table     | A table the catalog has never heard of              |
| Phantom column    | A column absent from a table whose schema is known  |
| Deprecated source | Reading from an asset marked deprecated             |
| PII propagation   | A PII-tagged column flowing into an untagged output |
| Unvetted join     | A join key pair seen in no observed query           |
| Blast radius      | Who consumes the asset the statement overwrites     |

## Usage

```
/datahub-sql-review models/customer_revenue.sql
/datahub-sql-review check this query before I merge it
/datahub-sql-review does this model reference real columns?
```

Or paste a statement and ask "review this against the catalog".

## The rule it follows

Severity reflects the strength of the evidence, not how alarming the problem
would be if it were real.

A column missing from a table whose schema the catalog holds is an **error**,
because the catalog can prove it. A table absent from the catalog entirely is
an **unknown**, because the catalog cannot tell a hallucinated name from a
table nobody ingested. Treating the second as the first is how a review like
this loses its readers.
