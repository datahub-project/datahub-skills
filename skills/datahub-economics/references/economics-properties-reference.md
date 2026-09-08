# Economics Properties Reference

How to persist an economic judgement into DataHub so other agents inherit it.

All write operations use `datahub graphql --query '...' --format json` or MCP tools. Get user approval before any write — see Step 6 of `SKILL.md`.

---

## Namespace

Use a namespace the user owns, in reverse-domain form: `<org>.<tool>.<field>`, for example `io.acme.economics.verdict`. Do not write into another vendor's namespace, and do not invent one silently — confirm the namespace with the user on the first run and reuse it thereafter so values stay comparable across runs.

`<ns>` below stands for that namespace.

---

## Property Definitions

| Property                  | Value type | Cardinality | Notes                           |
| ------------------------- | ---------- | ----------- | ------------------------------- |
| `<ns>.verdict`            | STRING     | SINGLE      | Constrained to the six verdicts |
| `<ns>.annualCostUsd`      | NUMBER     | SINGLE      | Storage + read + rebuild        |
| `<ns>.valueAtRiskUsdDay`  | NUMBER     | SINGLE      | Per **day**, not per year       |
| `<ns>.recoverableUsdYear` | NUMBER     | SINGLE      | Storage + rebuild only          |
| `<ns>.confidence`         | NUMBER     | SINGLE      | 0–1                             |

Keep the period in the property name (`UsdDay`, `UsdYear`). A consuming agent has no other way to know, and the two differ by 365×.

---

## Registration Order Matters

**Register every definition with a search configuration before writing any value.**

A structured property value is indexed for search only if its definition already carried a `searchConfiguration` at the moment the value was written. Adding the search config later does not retroactively index existing values, and no part of the API response reveals this — the write succeeds, `datahub get` returns the value, and only the search filter comes back empty.

```yaml
# structured_property.yaml — apply with: datahub properties upsert -f structured_property.yaml
- id: <ns>.verdict
  qualified_name: <ns>.verdict
  type: string
  cardinality: SINGLE
  display_name: Economic verdict
  entity_types:
    - dataset
    - dashboard
    - chart
  allowed_values:
    - value: LOAD_BEARING
    - value: HEALTHY
    - value: OVERSERVED
    - value: DEAD_WEIGHT
    - value: ORPHANED
    - value: UNPRICEABLE
```

Set `showInSearchFilters: true` on the property settings at registration time so verdicts are filterable in DataHub's own search UI. If a user reports an empty filter while the value is clearly present on the entity, the fix is to correct the definition and then **rewrite the values** — correcting the definition alone does nothing to values already written.

---

## Writing Values

```bash
datahub -C skill=datahub-economics graphql --query 'mutation {
  upsertStructuredProperties(input: {
    assetUrn: "<ENTITY_URN>",
    structuredPropertyInputs: [
      { structuredPropertyUrn: "urn:li:structuredProperty:<ns>.verdict", values: ["OVERSERVED"] },
      { structuredPropertyUrn: "urn:li:structuredProperty:<ns>.annualCostUsd", values: [105000] },
      { structuredPropertyUrn: "urn:li:structuredProperty:<ns>.recoverableUsdYear", values: [104000] },
      { structuredPropertyUrn: "urn:li:structuredProperty:<ns>.confidence", values: [0.82] }
    ]
  })
}' --format json
```

`upsertStructuredProperties` has no batch form — execute sequentially, and report progress every 10 entities on bulk runs.

### Complex URNs

Dataset URNs contain `(`, `)`, and `,`, which break shell escaping. Write the variables to a temp JSON file:

```bash
cat > /tmp/vars.json <<'JSON'
{ "urn": "urn:li:dataset:(urn:li:dataPlatform:snowflake,acme.public.orders,PROD)" }
JSON

datahub -C skill=datahub-economics graphql \
  --query /tmp/economics.graphql --variables /tmp/vars.json --format json

rm /tmp/vars.json /tmp/economics.graphql
```

Long inline `--query` strings also hit OS filename length limits — write the query to a file and pass its path; the CLI auto-detects it.

---

## Provenance

Whatever you write, the numbers are only defensible if their basis is recoverable later. Record alongside the run:

- the rate card and whether it was `contract` or `list` price
- the observation window
- the propagation assumptions (hard dependency, no distance decay, terminals deduplicated)
- the skill version or commit that produced the values

An agent quoting these properties can then quote the caveats too, instead of laundering an upper-bound estimate into a fact.

---

## Verify With a Separate Read

```bash
datahub -C skill=datahub-economics get --urn "<URN>" --aspect structuredProperties
```

Compare field by field against what you intended to write and report `checked / verified / missing / mismatched`. A mutation that reports its own success proves nothing. On any mismatch, stop the run and report — do not keep writing.

---

## Removing Values

```bash
datahub -C skill=datahub-economics graphql --query 'mutation {
  removeStructuredProperties(input: {
    assetUrn: "<ENTITY_URN>",
    structuredPropertyUrns: ["urn:li:structuredProperty:<ns>.verdict"]
  })
}' --format json
```

Stale economics are worse than none — a verdict from an old rate card will be read as current. If a rerun cannot re-price an asset it previously priced, remove the old values rather than leaving them in place.
