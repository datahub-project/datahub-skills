# Grounding Reference — the "no ungrounded diagnosis" rule

A candidate root cause is only acceptable if its causal claim can be
**reconstructed from real lineage evidence**. This is the core discipline that
separates this skill from a plausible-sounding guess.

## The rule

For a candidate `C` and symptom `S`:

1. Call `get_lineage_paths_between(source=S, target=C, direction=upstream)`.
2. If **no path** is returned → **reject `C`**. Try the next candidate.
3. If a path is returned → collect its ordered nodes and edges.
4. For the edge leaving `C` (and along the path), fetch `get_dataset_queries`
   to identify the **transform SQL** that carried the fault downstream.
5. The (nodes + edges + transform SQL) constitute the **proof**. Only now is the
   diagnosis "grounded" and eligible to be written back.

## Why this matters

- Rankings are hypotheses; without a path, a high score can still be wrong
  (correlated but not causal).
- Writing an ungrounded cause into a shared catalog pollutes it for every
  future reader and agent.
- A proof path is auditable: a human can follow the exact edges and the SQL,
  and either trust or challenge the diagnosis.

## When nothing can be grounded

If no candidate yields a verifiable path, do **not** write anything. Report:

> "No grounded root cause could be established. Strongest anomaly was on `<node>`
> but a lineage path to the symptom could not be reconstructed. Escalating to a
> human."

This honesty is a feature, not a failure mode.
