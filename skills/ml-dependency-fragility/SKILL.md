---
name: ml-dependency-fragility
description: Certify how many upstream feeds a model depends on jointly, before anything breaks. Computes the interaction order and minimal failure set of a model's dependence on its DataHub lineage, tracks that order over time to flag rising fragility while per-feature drift monitors stay green, and writes the certificate back onto the asset so later incident-response agents know whether one-at-a-time debugging can work at all.
user-invocable: true
effort: high
allowed-tools: Bash
---

# ML Dependency Fragility Certification

You determine whether a model's upstream feeds can fail _independently_ or only _jointly_, and you
record the answer in DataHub.

This is the proactive counterpart to incident root-cause. Nothing has broken. The question is what
would happen if it did, and whether the tools that would investigate it are capable of finding the
answer.

---

## Why this exists

Every upstream health signal in a catalog is per-asset: freshness, volume, schema, per-column
profiles. None of them can express "this model degrades only if these three feeds go stale
together." That statement is a common-cause failure, and it is the case redundancy does not protect
against.

It has a direct operational consequence. An agent that root-causes by reverting one upstream at a
time — or even every pair — **cannot** identify a failure set larger than the coalitions it
examined. Not "finds it slowly". The information is absent from what it measured. So it matters to
know the interaction order _before_ the incident, not during it.

---

## When to Use

- A model's dependence structure may have drifted even though no single feature has.
- You are about to rely on one-at-a-time ablation for root cause and want to know if that can work.
- You want a standing record on the asset of how many upstreams must be repaired together.
- Upstream feeds are correlated (same refresh job, same source system, same region).

Do **not** use this to explain a failure that has already happened — use `ml-incident-root-cause`.

---

## Prerequisites

- A running DataHub instance with the model or feature view and its upstream lineage.
- **A replayable scoring function.** You must be able to score the model on counterfactual upstream
  states. A feature store gives you this directly: a point-in-time join returns a feed's value as of
  an earlier moment, which _is_ a stale feed. Without any offline replay path, stop — the interaction
  order is not computable and you should say so rather than approximate it.
- A metric that responds to upstream degradation (holdout accuracy, AUC, a business metric).

---

## Workflow

### Step 1: Discover the feeds from the catalog

Read the asset's upstream feeds from DataHub rather than accepting a list. The player set must be
catalog truth, or the certificate describes something other than the deployed lineage.

For a feature view: `mlFeatureTable.properties.mlFeatures`, and each feature's `sources`.
For a model: `mlModel.properties.mlFeatures`, then each feature's `sources`.

### Step 2: Define ONE fixed probe

Choose a single standardized perturbation and keep it identical across periods. Staleness works well
because it is what actually happens: serve each degraded feed its value from 24 hours earlier.

Two properties make the probe correct:

- It must not move any feed's **marginal** distribution at probe time. Then a per-feature drift
  monitor sees nothing by construction, and anything the interaction order does is pure structure.
- It must be **fixed**. If the probe changes between periods, a change in interaction order tells
  you about your probe, not your model.

### Step 3: Evaluate every coalition

For each subset `S` of feeds, measure the metric with the feeds in `S` degraded and the rest fresh.
With a feature store this is two retrievals per period — one fresh, one lagged — because a coalition
is then just a choice of which columns come from which retrieval.

Guard the row alignment: a lagged retrieval legitimately returns **fewer** rows than a fresh one, as
nothing exists before the start of history. Pairing them positionally silently attaches one row's
degraded values to another row's fresh values. Align on a carried row key.

### Step 4: Take the Mobius transform

```
m(S) = sum over T subset of S of (-1)^(|S|-|T|) v(T)
```

- **interaction order** = largest `|S|` with a non-zero dividend
- **minimal failure set** = support of the largest-magnitude dividend at that order

**Apply a resolution floor.** This is the step implementations get wrong. On a finite holdout,
accuracy moves in steps of `1/n_eval`, so a _single flipped prediction_ creates a non-zero top-order
dividend and inflates the order to the maximum the feed set allows. Treat dividends below a few
metric quanta as unresolvable. Without this you will confidently report the highest possible order
every time.

### Step 5: Interpret

| Order | Meaning                | What can root-cause it                                    |
| ----- | ---------------------- | --------------------------------------------------------- |
| 1     | Additive dependence    | Single-feed ablation is sufficient                        |
| 2     | Redundant pair         | Single-feed ablation is blind; pairwise works             |
| >= 3  | Common-cause structure | Single **and** pairwise are blind; only coalition methods |

### Step 6: Track it over time, then write it back

Recompute each period with the same probe. A rising order means the model is accumulating redundant
dependence on correlated upstreams — the latent condition a common-cause failure exploits — while
every drift dashboard stays green.

Write the certificate onto the asset so it outlives the run: the order and minimal failure set as
structured properties, plus a human-legible banner. Make the write **idempotent** — re-running a
monitor must update one record, not stack another. The point is that the next agent inherits the
finding rather than recomputing it.

---

## Reporting honestly

- The order is a property of **model-under-this-probe**, not of the model. Always report the probe
  and the metric alongside the number.
- This is counterfactual attribution under an assumed, catalog-given DAG plus mechanism
  independence. It is not identified causal effect. Do not claim causality.
- If the floor removed a high-order dividend, say so. "Order 2, with an order-3 term below the
  resolution floor" is the honest reading, not "order 3".
- A rising order is a fragility signal, not a prediction that a failure is imminent.

---

## Notes for implementers

- The transform is exponential in the number of feeds. Enumerate exactly for small sets (up to
  roughly eight) and prefilter the upstreams first; sample above that, with a fixed seed so the
  result is reproducible.
- Prefilter by each feed's solo impact, not by how much it drifted. A loud feed with no effect on
  the metric will otherwise crowd out a quiet feed that the failure depends on.
- Two retrievals per period are enough for every coalition: one fresh, one degraded. A coalition is
  then a choice of which columns come from which retrieval.
- Prior art worth reading: Harsanyi dividends and interaction indices (Grabisch and Roubens 1999;
  Shapley-Taylor, Sundararajan et al. 2020; n-Shapley, Bordt and von Luxburg, AISTATS 2023);
  Shapley-based root-cause analysis over causal graphs (Budhathoki et al., ICML 2022); interventional
  rather than conditional attribution (Janzing et al. 2020), which matters here because correlated
  upstreams are exactly the regime this skill exists for.
