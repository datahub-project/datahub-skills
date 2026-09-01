# Version-Bound Change Proof Gaps

Use this reference when a quality question concerns a proposed change. Current asset health and a
passing assertion are useful context, but neither proves that the affected behavior is safe for an
exact revision and schema snapshot.

## Boundary

This workflow composes existing DataHub capabilities:

- `datahub-search` resolves the subject and governance context;
- `datahub-lineage` discovers affected consumers and reports traversal completeness;
- `datahub-quality` reads assertion outcomes and, after approval, can publish supported quality
  context.

It does not infer a release decision from lineage size, owner count, tags, or model confidence. It
builds explicit proof obligations and evaluates version-bound evidence against deterministic rules.

## Safety invariants

- Start read-only. Never trigger CI, run tests, change code, create incidents, send notifications,
  or mutate DataHub while assessing gaps.
- Treat model output as a proposal, never as evidence.
- Reject ambiguous entity matches. Bind the target to its canonical URN and environment.
- Treat incomplete, capped, cached, unavailable, or permission-filtered lineage as unknown
  coverage. An empty response is not proof that no dependencies exist.
- Keep prior evidence and review decisions append-only. A new decision does not rewrite history.
- Require a separate approval for the exact action target and payload. Approval of a report does
  not authorize execution.

## 1. Bind the exact change

Create a subject binding with these values:

```text
(asset_urn, environment, schema_snapshot, changed_field,
 exact_type_signature, source_revision, change_digest, observed_at)
```

The schema snapshot should be a native immutable version when available. Otherwise, compute a
digest over canonical field paths, logical and native types, parameters, nullability, and relevant
constraints. Preserve precision, scale, width, and timezone semantics; a broad type such as
`number` cannot prove a binding to `decimal(18,2)`.

If the source revision, environment, schema snapshot, or changed field cannot be resolved, set the
binding to `unresolved`. Continue only to report known impacts and gaps; the readiness decision must
be `indeterminate`.

## 2. Record impact completeness

Run field-level downstream lineage for every changed field and asset-level lineage as a
cross-check. Record:

- direction and hop depth;
- query and deployment tier;
- requested and returned pagination;
- result count and truncation or cap signals;
- observation time;
- field-lineage blind spots and asset-level fallback use.

An offline export is provisional unless a trusted manifest binds it to the exact query, snapshot,
filters, pagination, record count, truncation state, and SHA-256 checksum.

## 3. Create proof obligations

Create one independently decidable obligation for each affected behavior or control. Split items
whose owner or acceptance rule differs.

```yaml
id: PO-001
subject_binding: <binding digest>
impact: <downstream asset, field, or control>
risk: <falsifiable failure statement>
required_evidence: <contract, test, assertion, or reviewed control>
acceptance_rule: <deterministic predicate>
version_rule: <required revision, schema, field, and environment match>
owner: <DataHub owner URN or unresolved>
criticality: required | advisory
```

Derive obligations from observed lineage and declared change semantics. Do not invent a test merely
because an edge exists. When field lineage is unavailable, asset-level lineage may produce a
conservative candidate obligation, clearly labeled as such.

A missing owner is residual risk by default. Make ownership a required obligation only when the
accepted assurance policy says so.

## 4. Validate evidence

An evidence record needs enough immutable metadata to reproduce its scope:

```yaml
evidence_id: EV-001
kind: contract_test
subject_binding: <binding digest>
source_revision: <immutable revision>
schema_snapshot: <version or digest>
environment: TEST
producer: <named verifier>
run_id: <immutable run identifier>
executed_at: <RFC 3339 timestamp>
result: pass | fail | error | skipped
artifact_uri: <stable locator>
artifact_digest: sha256:<hex>
valid_until: <optional RFC 3339 timestamp>
```

Do not treat an assertion description, proposed test, issue, model explanation, or unbound PASS as
executed evidence.

## 5. Preserve evidence states

Assign exactly one status per obligation:

| Condition                                                                      | Status      | Meaning                                   |
| ------------------------------------------------------------------------------ | ----------- | ----------------------------------------- |
| Complete successful query, no relevant artifact                                | `missing`   | Evidence was not found                    |
| Artifact exists, but revision, schema, field, environment, or validity differs | `stale`     | It does not cover this change             |
| Matching evidence ran and failed its acceptance rule                           | `negative`  | The behavior was tested and failed        |
| Matching evidence ran and passed its acceptance rule                           | `satisfied` | The obligation is proven for this binding |
| Query incomplete, artifact unverifiable, execution errored, or test skipped    | `unknown`   | No defensible conclusion is available     |

Never turn `missing`, `stale`, or `unknown` into `negative`. Preserve individual artifact states
even when the report summarizes an obligation.

## 6. Decide deterministically

For required obligations:

```text
any negative                         -> not_ready
else any missing, stale, or unknown -> indeterminate
else all satisfied                  -> ready
```

An unresolved subject binding or incomplete required lineage always overrides the table with
`indeterminate`. Advisory obligations appear as residual risk and never compensate for a required
gap.

## 7. Propose, review, and re-evaluate

For each gap, propose the smallest action that could produce the required evidence. Show the exact
target, tool, operation, payload summary, side effects, expected artifact, compensation, and
idempotency behavior. When no approved safe execution tool exists, mark it `not_available`; do not
substitute an arbitrary shell command.

Pause for explicit human approval. After an external system returns fresh evidence, validate its
binding and recompute every obligation. Review approval alone cannot change evidence status or
readiness.

If the user separately approves DataHub write-back, use the supported quality mutation described
in `assertion-mutations-reference.md`, re-read the entity after writing, and record the exact
server-returned assertion URN. Publish digests and stable locators instead of raw evidence whenever
possible.

## Canonical digests

Use lowercase hexadecimal SHA-256 over UTF-8 stable JSON with sorted object keys, semantically
ordered arrays, and no insignificant whitespace. Include a digest-contract version. Recommended
scopes are:

- `binding_digest`: exact subject binding;
- `lineage_query_digest`: binding, query scope, normalized edges, completeness, and observation;
- `obligations_digest`: binding plus obligations sorted by stable ID;
- `evidence_set_digest`: obligations plus evidence sorted by evidence ID;
- `report_digest`: binding, lineage, obligation states, decision, residual risks, proposed actions,
  and review status, excluding the digest field and audit section to avoid self-reference.

Do not compare digests produced under different contract versions.
