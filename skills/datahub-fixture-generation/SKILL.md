---
name: datahub-fixture-generation
description: |
  Generate source-row-free test fixtures and developer artifacts from governed DataHub metadata, then validate and deliver them as a reviewable Git change. Use when a user asks to create fixtures, seeds, factories, dbt tests, mock datasets, or merge-ready development code that must adapt to real DataHub schemas, lineage, ownership, tags, glossary terms, domains, or schema changes. Also trigger for adversarial schema-change testing, deterministic fixture generation, or evidence writeback after a fixture-generation run.
user-invocable: true
min-cli-version: 1.4.0
allowed-tools: Bash(datahub *), Bash(git *)
---

# DataHub Fixture Generation

Generate reviewable developer assets from DataHub's metadata graph without reading production
source rows. Treat DataHub as the contract, Git as the delivery boundary, and independent
validation as the success gate.

## Boundaries

- Read schema, keys, lineage, ownership, tags, glossary terms, domains, and relevant quality
  signals. Do not query source tables or copy source rows.
- Treat source-row-free as an access claim, not an anonymization, privacy, compliance, or
  production-readiness claim.
- Keep DataHub mutation disabled during discovery. Require explicit approval before metadata
  writeback.
- Require explicit approval before pushing a branch or opening a remote pull request unless the
  user's request already authorizes publication.
- Refuse to generate when the metadata contract is internally inconsistent, incomplete for a
  required relationship, or truncated without a verified pagination path.

## Step 1: Define the delivery contract

Capture:

1. The business goal and bounded catalog scope
2. Required outputs, such as CSV, Parquet, dbt tests, typed factories, migration code, or seeds
3. The destination repository and path
4. Required row counts and deterministic seed
5. Validation and writeback expectations

Do not accept a hand-curated dataset list as a substitute when the user asks for graph-aware
discovery. Derive the working set from search and lineage evidence.

## Step 2: Discover and inspect the graph

Prefer MCP tools when available. Use the DataHub CLI as a fallback; see
`../shared-references/datahub-cli-reference.md` for exact syntax.

1. Search for the goal's scope.
2. Expand bounded upstream and downstream lineage.
3. Fetch the selected entities together.
4. Fetch complete schema fields for every selected dataset.
5. Record primary and foreign keys, nullability, native types, descriptions, ownership, tags,
   glossary terms, domains, deprecation, and relevant quality state.
6. Record every tool call and selected URN. Detect truncated schema or lineage responses and
   paginate before generation.

Keep a strict read allowlist during this phase. Record that source-row tools were unavailable or
unused; do not infer zero-row access merely because no rows appear in the final output.

## Step 3: Normalize a reproducible contract

Create a machine-readable contract containing:

- Exact dataset and field URNs
- Field order, type, nullability, key constraints, and relationships
- Governance metadata that changes generation behavior
- Lineage edges used to select or order artifacts
- Ownership and domain context for review routing
- DataHub server and tool identity
- A canonical metadata fingerprint and deterministic seed

Separate explicit user policy from DataHub-derived facts. Hash both inputs so reviewers can tell
which decisions came from the catalog and which came from the requested generation policy.

## Step 4: Generate developer assets

Generate parent datasets before children. Preserve foreign-key relationships and primary-key
uniqueness. Use governance signals to select synthetic generators, for example:

- PII or email terms → clearly fictional `example.test` values
- Accepted-value rules → values from the allowed set
- Numeric bounds → include boundary values
- Dates and timestamps → deterministic synthetic sequences

Emit developer-facing tests and typed accessors alongside the fixtures. Include provenance in the
generated artifacts so reviewers can trace each rule to metadata or explicit policy.

## Step 5: Prove the output

Run all checks on the first generated bundle:

- Parse and type compatibility
- Row counts and nullability
- Primary-key uniqueness
- Foreign-key integrity
- Accepted values and numeric ranges
- Tool-specific checks for generated dbt, Python, SQL, or configuration artifacts

Then run three stronger gates:

1. **Negative control:** Deliberately break one relationship or constraint and prove the same
   independent validator rejects it.
2. **Deterministic rebuild:** Rebuild from the same fingerprint, policy, version, and seed; compare
   byte-level hashes.
3. **Adversarial schema changes:** Exercise representative additions, removals, renames, type or
   enum changes, and broken relationships. Report first-pass success for compatible changes and
   refusal rate for incompatible contracts.

Do not silently retry and call the final attempt "first pass." Count one attempt per scenario and
include generation, emission, and validation in latency.

## Step 6: Deliver through Git

Verify the destination repository is clean enough to isolate the generated change. Create a
dedicated branch, stage only intended artifacts and evidence, and commit with a concise goal-based
message. The pull request should include:

- Generated code and sample artifacts
- The normalized metadata contract
- Validation, negative-control, and determinism receipts
- Adversarial schema-change metrics
- Exact reproduction commands
- Honest claim boundaries

Do not merge automatically. Leave the change reviewable by the responsible owners discovered in
DataHub.

## Step 7: Write evidence back

After the user approves DataHub mutation, save a concise context document or approved metadata
update related to a selected asset. Include the metadata fingerprint, validation result, Git branch
and commit, and claim boundary. Read the written content back through DataHub and require the full
fingerprint before reporting success.

Do not write generated rows, secrets, local paths, or private repository details into DataHub.

## Final report

Use `templates/evidence-summary.md`. Report:

- Discovered and rejected assets
- Metadata aspects actually read
- Source rows read
- Generated artifacts and Git receipt
- First-pass success rate and latency sample size
- Negative-control and adversarial results
- DataHub writeback and read-after-write receipt
- Reproduction steps and limitations

Distinguish local evidence, CI evidence, and production adoption. A green local run or pull request
does not prove production use or business impact.
