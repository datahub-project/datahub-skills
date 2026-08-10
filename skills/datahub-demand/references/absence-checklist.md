# Absence checklist

The eight checks that must return nothing before an asset may be called absent. Run them
in order and stop at the first hit.

Every command below uses the same CLI surface as `/datahub-search`. Use
`datahub search list-filters` to discover the filter keys available on your instance, and
`datahub search "X" --dry-run` to preview the generated GraphQL before running a broad
query.

## 1. Literal search

The user's phrase, unmodified. This is the check that fails most often and proves least.

```bash
datahub search "monthly recurring revenue by segment" --format json --limit 10
```

## 2. Tokenised search

Each significant term on its own. A four-word want is four searches. Assets are rarely
named the way a request is phrased.

```bash
datahub search "revenue" --where "entity_type = dataset" --format json --limit 20
datahub search "segment" --where "entity_type = dataset" --format json --limit 20
```

Compare the results against the **grain** the requester needs, not just the subject. An
asset about revenue that lacks the segment dimension is not a hit.

## 3. Glossary terms

The organisation's word for the concept is frequently not the requester's word. A glossary
hit usually points at the asset carrying the term.

```bash
datahub search "recurring revenue" --where "entity_type = glossaryTerm" --format json
datahub get --urn "<glossaryTerm urn from above>"
```

## 4. Column-level search

The single most common false absence. The want is a **column on an asset that already
exists**, not a missing asset.

```bash
datahub search "mrr" --where "entity_type = dataset" --format json --limit 20
datahub get --urn "<candidate dataset urn>" --aspect schemaMetadata
```

## 5. Other platforms

The requester searched where they work. The asset may live elsewhere, or in a dashboard,
or in a dbt model that has not been ingested yet.

```bash
datahub search "*" --where "entity_type = dataset" --projection "urn type" --limit 50
datahub search "revenue" --where "entity_type = chart OR entity_type = dashboard" --format json
```

`--limit` is capped at 50 per request; the CLI warns and silently truncates above that.
Page with `--offset` rather than raising the limit, or the sweep will look complete when it
is not.

If a platform the organisation uses is absent from the results entirely, the asset may
exist but be **uningested** — a different answer from absent, and one with a clear owner.

## 6. Deprecated and soft-deleted assets

An asset that was removed is not an asset that never existed. It has history and usually
an owner who can say why it went.

```bash
datahub get --urn "<candidate urn>" --aspect status
datahub get --urn "<candidate urn>" --aspect deprecation
```

## 7. Data products and domains

The thing may be wrapped in a product or domain whose name shares no tokens with the
request.

```bash
datahub search "revenue" --where "entity_type = dataProduct" --format json
datahub search "*" --where "entity_type = domain" --projection "urn type" --limit 50
```

## 8. Lineage neighbours

If a closely-related asset exists, walk one hop in each direction. The want is often a
trivial transform of something already catalogued, and the nearest neighbour is what the
builder will start from.

```bash
datahub get --urn "<nearest asset urn>" --aspect upstreamLineage
```

For a full traversal, hand off to `/datahub-lineage`.

---

## Recording the result

Only after all eight return nothing. Record at minimum:

| Field        | Why                                                           |
| ------------ | ------------------------------------------------------------- |
| want         | the phrase as the requester expressed it                      |
| requester    | from the caller's authenticated identity, never a typed field |
| requestedAt  | so repeat demand can be distinguished from a retry            |
| neededFields | what the requester was going to select                        |
| nearestAsset | the closest existing asset, or explicitly none                |
| ruledOut     | which of the eight checks ran and what each returned          |

`ruledOut` is what makes the record auditable later. A demand record without it is an
assertion; with it, it is an argument someone can check.
