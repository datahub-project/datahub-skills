# Verdict Reference

Six verdicts, their entry conditions, the evidence each one requires, and the counter-evidence that must travel with it.

Verdicts are **deterministic**: the same graph plus the same rate card produces the same verdict every time. Evaluate the conditions in the order below and take the first that matches. A model may narrate a verdict; it may never decide one.

---

## Evaluation Order

1. `UNPRICEABLE` — signal check comes first, so a missing aspect can never be mistaken for a zero.
2. `ORPHANED`
3. `DEAD_WEIGHT`
4. `OVERSERVED`
5. `LOAD_BEARING`
6. `HEALTHY` — the default when nothing above matches.

---

## `UNPRICEABLE`

**Entry:** Any signal required for the verdict under consideration is missing, or the lineage traversal was capped.

**Required evidence:** The name of each missing aspect.

**Action:** Refuse to judge. State what would make the asset judgeable — for example, "no `datasetUsageStatistics` aspect: enable usage ingestion on this platform".

This is a first-class outcome, not a failure. Recommending deletion of an asset with no usage data is how a tool gets banned from an organization. An estate that returns mostly `UNPRICEABLE` is telling the user something true about their ingestion coverage, and reporting that honestly is more useful than a confident guess.

---

## `ORPHANED`

**Entry:** No owner on the `ownership` aspect **and** no reachable terminals.

**Required evidence:** Empty ownership, empty terminal set, annual cost.

**Counter-evidence to state:** Nobody is accountable for this asset, so nobody can approve its removal either.

**Action:** Route to a human. Do not propose deletion of an asset with no owner to ask — find the owner first, usually via the container, domain, or upstream producer.

---

## `DEAD_WEIGHT`

**Entry:** `totalSqlQueries == 0` over the window **and** the reachable terminal set is empty **and** both signals are present.

**Required evidence:** Query count of zero over a stated window, empty terminal set, `recoverable_usd_year`.

**Counter-evidence to state:** The window length, and anything the window would miss — quarterly reporting jobs, annual audits, disaster-recovery copies.

**Action:** Deprecation candidate. Quote `recoverable_usd_year` (storage plus rebuild), never `annual_cost_usd`.

---

## `OVERSERVED`

**Entry:** `cadence_per_day > reads_per_day` by a material margin **and** the asset has live consumers (nonzero reads or a nonempty terminal set).

**Required evidence:** Rebuild cadence, read rate, rebuild cost, computed saving at the target cadence.

**Counter-evidence to state:** **The asset is in use. Reduce cadence, do not delete.**

**Action:** Right-size the schedule to `max(reads_per_day, 1/7)`.

`OVERSERVED` assets must never appear in a deprecation list. They carry recoverable spend and an in-use flag simultaneously, which is precisely the combination that gets a live table dropped. Any ranking of "what can we remove" must filter this verdict out explicitly rather than relying on the saving figure alone.

---

## `LOAD_BEARING`

**Entry:** High `value_at_risk_usd_day` relative to the estate, with observed active use.

**Required evidence:** Distinct reachable terminals with their seeded values, read volume.

**Counter-evidence to state:** Value at risk is a hard-dependency upper bound — some downstream consumers may have alternative sources.

**Action:** Protect and monitor. Good candidates for freshness and volume assertions via `/datahub-quality`, and for ownership backfill via `/datahub-enrich`.

---

## `HEALTHY`

**Entry:** Everything else. Cost is proportionate to observed consumption.

**Required evidence:** Cost components and read volume.

**Action:** None. Say so plainly — an estate where every asset has a finding is an estate nobody will trust.

---

## Presenting a Verdict

Every verdict carries at least one line of counter-evidence, marked distinctly from supporting evidence:

```text
DEAD_WEIGHT   recover $38k/yr   acme.staging.legacy_sessions_2019
  + 0 queries in 30 days
  + 0 reachable dashboards, charts, models, or data products
  + storage $2k/yr + rebuild $36k/yr recoverable
  − 30-day window would not see a quarterly reporting job
  confidence 0.75 — no owner on record; ask the container owner before dropping
```

A verdict without counter-evidence reads as advocacy. The counter-evidence is what makes it reviewable.
