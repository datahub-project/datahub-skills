# MCP Tool Call Reference (empirically verified)

Every tool call and schema on this page was run against the live local DataHub OSS
v1.5.0.6 quickstart (`http://localhost:8080`) via `mcp-server-datahub@latest` (resolved
`0.6.0`), `TOOLS_IS_MUTATION_ENABLED=true`, not inferred from documentation. Parameter
names are copied from the server's own `tools/list` schema, not guessed.

---

## Reading learnings

### `get_entities`: the confirmed read path for dataset-level learnings

```python
get_entities(urns=["urn:li:dataset:(urn:li:dataPlatform:postgres,demo_warehouse.ecommerce.fct_orders,PROD)"])
```

`urns` accepts a single string or a list: batch multiple in-scope entities (target +
upstream hop) into one call. Response includes `structuredProperties.properties[].values[].stringValue`
for every structured property with a value on that entity, including
`io.datahub.agentMemory.learnings`. **Confirmed**: a value written via
`add_structured_properties` (below) appeared verbatim in the next `get_entities` call in
the same session.

### `list_schema_fields`: does NOT return structured property values

```python
list_schema_fields(urn="<dataset_urn>")   # note: param is `urn`, not `dataset_urn`
```

Returns `fieldPath`, `nativeDataType`, `description`, `nullable` per field: no
structured-property values, confirmed by direct test (wrote a schemaField-scoped
learning, called `list_schema_fields` on the parent dataset, the learning did not
appear in the response). Useful for resolving which columns exist / matching a column
name, not for reading learnings.

### Known gap: no MCP tool reads schemaField-scoped structured properties

Confirmed by direct test: after `add_structured_properties` succeeded writing a learning
to a schemaField urn (`urn:li:schemaField:(<dataset_urn>,amount)`, see below):

- `get_entities(urns=["<schemaField_urn>"])` → response is `{"urn": "<schemaField_urn>"}` only. No aspects, no structured properties.
- `list_schema_fields(urn="<dataset_urn>")` → returns the field's `fieldPath`/type/description, never its structured-property values.

The value **is** there: confirmed via raw GraphQL:

```graphql
query GetField($urn: String!) {
  entity(urn: $urn) {
    urn
    ... on SchemaFieldEntity {
      structuredProperties {
        properties {
          structuredProperty {
            urn
          }
          values {
            ... on StringValue {
              stringValue
            }
          }
        }
      }
    }
  }
}
```

```bash
datahub graphql --query 'query GetField($urn: String!) { entity(urn: $urn) { urn ... on SchemaFieldEntity { structuredProperties { properties { structuredProperty { urn } values { ... on StringValue { stringValue } } } } } } }' \
  --variables '{"urn": "urn:li:schemaField:(urn:li:dataset:(urn:li:dataPlatform:postgres,demo_warehouse.ecommerce.fct_orders,PROD),amount)"}'
```

Use this GraphQL form for column-scoped recall until the MCP server adds a schemaField
read path. This is the one place this skill cannot stay MCP-only.

---

## Lineage

```python
get_lineage(urn="<target_urn>", upstream=True, max_hops=1)
```

Schema: `urn` (required), `upstream` (bool, default `true`), `max_hops` (default `1`),
`max_results` (default `30`), plus optional `column`/`query`/`filter`/`offset`. An empty
`upstreams.total: 0` result is a valid, common response: it means no lineage edges are
ingested for that entity (true for this repo's demo warehouse, which ingests table
metadata only, no transformation lineage), not a tool failure.

---

## Writing learnings

### `add_structured_properties`

```python
add_structured_properties(
    property_values={
        "urn:li:structuredProperty:io.datahub.agentMemory.learnings": ["<json_blob_1>", "<json_blob_2>", ...]
    },
    entity_urns=["<dataset_or_schemaField_urn>"],
)
```

Schema: `property_values` (dict of property urn → list of values, required),
`entity_urns` (list, required). Confirmed working identically on both dataset urns and
schemaField urns (schemaField write succeeds via this tool with no low-level fallback
needed, unlike the high-level Python SDK, which cannot address `schemaField` as an
entity type at all).

**The full value list must be passed every time.** Confirmed by direct test: writing
`{"...learnings": [blob_2]}` to an entity that already had `[blob_1]` resulted in
`[blob_2]` only. `blob_1` was gone. The corrected sequence (read current values via
`get_entities`, append/replace client-side, write the complete list) was then verified
to leave both values present. `add_structured_properties` calls the GraphQL
`upsertStructuredProperties` mutation internally, which replaces, not appends: this is
DataHub's behavior, not a quirk of any one client.

CLI equivalent (needed for column-scoped writes only insofar as you want a single
non-MCP path; the MCP tool above already covers schemaField urns fine):

```bash
datahub graphql --query 'mutation upsert($input: UpsertStructuredPropertiesInput!) { upsertStructuredProperties(input: $input) { properties { structuredProperty { urn } values { ... on StringValue { stringValue } } } } }' \
  --variables '{"input": {"assetUrn": "<urn>", "structuredPropertyInputParams": [{"structuredPropertyUrn": "urn:li:structuredProperty:io.datahub.agentMemory.learnings", "values": [{"stringValue": "<json_blob>"}, ...]}]}}'
```

### `update_description`

```python
update_description(
    entity_urn="<dataset_urn>",
    operation="replace",       # NOT "append" -- see below
    description="<full spliced description text>",
    column_path=None,          # or "<column_name>" for a schemaField-level description
)
```

Schema: `entity_urn` (required), `operation` (`replace` | `append` | `remove`, default
`replace`), `description` (required for replace/append), `column_path` (optional,
targets a schema field by name on the same dataset urn, confirmed as the documented
mechanism for column-level descriptions; no need to address a schemaField urn
separately for this tool).

**Always use `operation="replace"` with the full spliced text for the agent-memory
block, never `operation="append"`.** `append` does raw string concatenation with no
marker awareness: it would duplicate the block on every write instead of replacing it
in place. Confirmed by direct test: two sequential `update_description(operation=
"replace", ...)` calls, each computing the full spliced description client-side (split
on `<!-- agent-memory:begin -->` / `<!-- agent-memory:end -->`, replace the middle,
reassemble), left **exactly one** marker pair after the second write, with the second
write's content, not two copies. If markers are absent (first-ever write), the same
splice function appends the whole block after a blank line rather than replacing
anything.

---

## Search (entity resolution)

```python
search(query="fct_orders", num_results=5)
```

Used only to resolve a name to a urn when the caller doesn't already have one, not
part of the learnings read/write path itself.
