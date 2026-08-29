---
name: datahub-change-safety
description: |
  Use this skill when the user wants to assess whether a proposed data, pipeline, feature, or model change is safe before merge or deployment. Triggers on: "is this SQL change safe", "review this dbt model change", "what will this schema change break", "test downstream impact", "generate a change passport", "protect this model from upstream changes", or any request that combines an exact change with DataHub metadata/lineage and executable validation.
user-invocable: true
min-cli-version: 1.5.0.1rc1
allowed-tools: Bash(datahub *)
---

# DataHub Change Safety

Assess an exact proposed change with live DataHub context, execute the relevant downstream checks, and produce evidence that another reviewer or agent can verify. Treat metadata as test-selection context, not as proof that a change is safe.

## Compatibility and boundaries

Use MCP tools when available and the DataHub CLI otherwise. Keep the workflow sequential on agents without delegation.

| If the user wants to...                            | Use this instead   |
| -------------------------------------------------- | ------------------ |
| Explore lineage without a concrete proposed change | `/datahub-lineage` |
| Search for schemas, owners, or entities            | `/datahub-search`  |
| Update metadata without a safety assessment        | `/datahub-enrich`  |
| Create assertions or manage incidents              | `/datahub-quality` |

This skill coordinates change analysis and execution. It does not invent a generic SQL runtime, silently run production writes, or claim that lineage alone proves safety.

## Safety contract

Use exactly three verdicts:

- `UNSAFE`: an executed critical check regressed or an approved protection was violated.
- `SAFE_WITHIN_SCOPE`: every discovered critical check passed and context coverage is complete. Always state the evaluated scope and limitations.
- `UNVERIFIED`: required context or execution evidence is missing, ambiguous, stale, unsupported, or failed for infrastructure reasons.

Never convert `UNVERIFIED` into a pass. Never describe `SAFE_WITHIN_SCOPE` as universally safe.

Do not mutate production data. Use an isolated database, preview environment, temporary schema, test runner, or other reversible execution surface. Require explicit human approval before writing protection memory or assessment metadata to DataHub.

## 1. Bind the exact change

Record the repository, base revision, candidate revision, and changed paths. Read the exact file contents at both revisions rather than relying only on a prose PR description.

For SQL or dbt changes:

1. Resolve the changed model through the compiled manifest when available.
2. Parse semantic changes with an AST-aware tool. Treat comments and formatting as non-semantic.
3. Reject unsupported templating, missing revisions, ambiguous model matches, and multiple independently changed models as `UNVERIFIED` unless each model can be assessed separately.
4. Preserve normalized change facts such as `column_added`, `column_removed`, `expression_changed`, `join_changed`, or `filter_changed`.

For schema, pipeline, feature, or model changes, preserve an equivalent machine-readable diff: changed fields, contract, artifact hash, configuration, or deployment identity.

## 2. Resolve the DataHub asset

Prefer exact identifiers from build artifacts (for example dbt `unique_id`, platform instance, environment, or manifest metadata). Search by name only when no exact mapping exists.

1. Resolve one authoritative DataHub URN for each changed asset.
2. If multiple plausible entities remain, present them and stop for selection.
3. Confirm the entity type, platform, environment, and display name.
4. Record the resolution method and any ambiguity.

Reject shell metacharacters in user-supplied names and URNs before passing them to a CLI.

## 3. Build a live context snapshot

Use MCP first when it is available:

- `get_entities` for ownership, tags, domains, custom properties, status, and entity identity.
- `list_schema_fields` for the real field contract.
- `get_lineage` for downstream consumers and upstream dependencies.
- `get_lineage_paths_between` when a critical consumer path must be proven.
- `search` only for discovery or enrichment, not as a replacement for exact resolution.

With the CLI, use `datahub -C skill=datahub-change-safety ...` and follow `../shared-references/datahub-cli-reference.md`. If `-C` is unsupported, omit it.

Trace downstream far enough to reach executable consumers such as transformation models, assertions, dashboards, features, ML models, and deployed agents. Default to one hop; expand to at most three hops when the critical path requires it. Record whether results were capped or truncated.

Create a context-coverage ledger:

| Required evidence  | Complete when                                          |
| ------------------ | ------------------------------------------------------ |
| Entity identity    | exact URN and environment are resolved                 |
| Schema/contract    | current fields or artifact contract are captured       |
| Downstream lineage | relevant paths are captured and not silently truncated |
| Critical consumers | each critical consumer has an owner and planned check  |
| Protection memory  | prior approved protections were searched for           |

Any material gap makes the verdict `UNVERIFIED` unless the user explicitly narrows the scope and the Passport records that boundary.

## 4. Turn context into an executable test plan

Map every critical consumer to a check that can observe the proposed change:

| Consumer          | Preferred evidence                                                     |
| ----------------- | ---------------------------------------------------------------------- |
| dbt/SQL model     | compile/build plus row-, column-, and invariant-level comparison       |
| DataHub assertion | assertion execution or current run result tied to the candidate        |
| Dashboard/metric  | query or semantic-layer test for affected measures and dimensions      |
| Feature           | feature contract and value-distribution comparison                     |
| ML model          | baseline/candidate prediction replay using the same model artifact     |
| Deployed agent    | baseline/candidate action replay with the same policy and model output |

Do not count a discovered consumer as covered until its check actually executes. If no safe executable surface exists, mark that consumer unverified and route review to its DataHub owner.

## 5. Execute baseline and candidate

Use the same fixture, environment, dependency versions, model artifact, and policy for both revisions.

Capture for every check:

- consumer URN and owner;
- evaluator name and version;
- start/end timestamps and exit status;
- input or fixture hash;
- baseline and candidate output hashes;
- observations, pass/fail status, and a concise explanation.

Separate behavior regressions from infrastructure failures. Infrastructure failures produce `UNVERIFIED`, not `UNSAFE` and not a pass.

For a behavioral regression, reduce the failing input only while replaying the entire changed path. Keep a minimization only when the smaller witness reproduces the same failure. Re-run the minimized witness in a separate process when practical.

## 6. Decide and remediate

Apply the three-state safety contract after all planned checks finish.

For `UNSAFE`:

1. Show the smallest causal path from changed asset to failed consumer.
2. Show the minimized counterexample and exact baseline/candidate difference.
3. Route review to the owners returned by DataHub.
4. Generate a remediation only when the change intent is clear.
5. Execute the remediation through the same plan. Label it `verified` only if every previously failing critical check passes; otherwise label it `proposed`.

For `SAFE_WITHIN_SCOPE`, list every executed critical check and every explicit limitation. For `UNVERIFIED`, list missing evidence and the smallest next action that would make the assessment decidable.

## 7. Produce a Change Passport

Read `references/change-passport.md` and emit both:

- a machine-readable JSON Passport committed or attached to the change; and
- a compact reviewer summary suitable for a pull-request Check.

Bind the Passport to source revisions, normalized change facts, DataHub fact hashes, evaluator versions, artifact hashes, and outputs. Never hand-author a verdict that is not derivable from recorded checks.

Publish CI status using the verdict's native exit semantics when the surrounding system supports them: `SAFE_WITHIN_SCOPE` succeeds, `UNSAFE` fails, and `UNVERIFIED` requests action or fails closed. For changes outside the configured scope, report an explicit not-applicable result and make no safety claim.

## 8. Learn with human approval

After an unsafe assessment, propose a reusable protection containing:

- stable protection ID and version;
- source Passport ID;
- affected entity URNs;
- portable regression fixture or invariant;
- approval identity and timestamp;
- link to the immutable Passport artifact.

Show the exact write plan and require explicit approval. Then use `/datahub-enrich` or supported MCP mutations to store an organization-approved representation such as a related DataHub Document, structured properties, or a custom aspect, and attach it to all affected entities. Do not disguise a Passport as a dataset schema or overwrite existing metadata blindly.

Verify the write by reading it back. A future assessment must retrieve matching active protections during context collection and execute them alongside newly selected checks. Repeating the same approval must update idempotently rather than create duplicates.

## Stop conditions

Return `UNVERIFIED` and stop the safety claim when:

- the changed asset cannot be mapped to one DataHub entity;
- lineage or schema results are missing, stale, capped without review, or contradictory;
- a critical consumer has no executable check;
- baseline and candidate did not run under equivalent conditions;
- the model or policy artifact identity changed unintentionally;
- a command, query, or fixture contains unreviewed production writes;
- evidence cannot be bound to the exact source revision.

## Reviewer summary

Lead with the verdict, then show:

1. exact change and DataHub entity;
2. context coverage and critical consumers;
3. executed checks and counterexample, if any;
4. verified remediation or next action;
5. owner routing;
6. Passport link and protection-memory status;
7. bounded limitations.

Keep raw MCP payloads in the Passport; keep the reviewer summary compact.
