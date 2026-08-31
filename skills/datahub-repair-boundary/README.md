# datahub-repair-boundary

Decides whether an automated repair may be generated for a schema change, and names the condition when it may not.

Impact analysis answers "what does this change reach". This skill answers the next question: "given what the graph can and cannot prove, am I entitled to write code against it". A change can be low risk and still be unrepairable automatically, because the metadata does not identify what to edit.

## When it applies

An agent is about to generate or apply a repair on the strength of lineage: patching downstream models after a rename, rewriting references, or emitting a migration plus its consumer changes.

## The five blocking conditions

| Condition            | The naive result                        | The boundary                                      |
| -------------------- | --------------------------------------- | ------------------------------------------------- |
| Ambiguous mapping    | picks one implementation and patches it | stop, return every candidate, require a human pick |
| Reachable not used   | patches on asset-level reachability     | repair only on column evidence, route the rest     |
| Destination collision| renames onto a live column              | check the destination first, refuse on collision   |
| Empty execution      | reads exit zero as proof                | assert the expected node set, not the exit code    |
| Stale graph          | acts on a plan built from an older read | re-read before acting, disagreement is terminal    |

Plus a SQL scope preflight: refuse any file whose column ownership cannot be proven (joins, CTEs, set operations, subqueries, lateral relations, anything that is not a plain `SELECT`), and preserve strings, comments, dollar-quoted bodies and templating rather than rewriting them.

## Relationship to the other change skills

`datahub-lineage` traces dependencies. Impact and change-safety skills assess whether a revision is risky and return a verdict. This one is downstream of both: it assumes the change is going ahead and governs whether a **generated repair** may be emitted, and which named condition blocks it when not.

## Provenance

Distilled from [RippleProof](https://github.com/itxcrusher/ripple-proof), built for the Build with DataHub Agent Hackathon. The conditions are measured rather than asserted: a deterministic corpus of 14 cases, 8 existing only to check the agent still declines, with 0 false repairs.

One captured campaign, including three refusals in a single run, is readable with no install at <https://itxcrusher.github.io/ripple-proof/examples/>.
