# Model Investigation

## Subject

**Model group:** <!-- name and URN -->
**Version investigated:** <!-- version tag and mlModel URN -->
**Comparison version:** <!-- version tag and URN, or "none" -->
**Reported symptom:** <!-- in the user's words -->

## Conclusion

<!-- One sentence. What changed, where, and when. -->

**Confidence:** <!-- High / Medium / Low --> — <!-- why that level -->

## Evidence Chain

```text
<!-- hop-by-hop trace, e.g.

<model> v7 (mlModel)
  └─ TrainedBy → <run name> (ML Training Run, <date>)
       ├─ metrics: <metric> <value> (v6: <value>)
       └─ Consumes → <input dataset>
            └─ upstream → <real source dataset>
                 └─ column <column> ← <source column>
                      └─ nullProportion <before> → <after> on <date>
-->
```

## Version Diff

| Field            | <!-- good version -->    | <!-- bad version -->     | Same? |
| ---------------- | ------------------------ | ------------------------ | ----- |
| Created          | <!-- timestamp -->       | <!-- timestamp -->       |       |
| Training run     | <!-- run name -->        | <!-- run name -->        |       |
| Hyperparameters  | <!-- summary or diff --> | <!-- summary or diff --> |       |
| Training metrics | <!-- key metrics -->     | <!-- key metrics -->     |       |
| Input datasets   | <!-- count and list -->  | <!-- count and list -->  |       |
| Features         | <!-- count -->           | <!-- count -->           |       |

## Observations

| #   | Observation                | Source                                   | Timestamp     |
| --- | -------------------------- | ---------------------------------------- | ------------- |
| 1   | <!-- what was measured --> | <!-- aspect / query that returned it --> | <!-- when --> |

<!-- Observations are facts returned by DataHub. Keep inferences out of this table. -->

## Hypotheses Considered

| Hypothesis               | Verdict                        | Basis                      |
| ------------------------ | ------------------------------ | -------------------------- |
| <!-- candidate cause --> | <!-- supported / ruled out --> | <!-- which observation --> |

## Gaps

| Missing                               | Effect on the conclusion            |
| ------------------------------------- | ----------------------------------- |
| <!-- e.g. no column-level lineage --> | <!-- what could not be verified --> |

## Suggested Next Steps

1. <!-- e.g. assertion on the source column via /datahub-quality -->
2. <!-- e.g. notify the owners of the affected model versions -->
3. <!-- e.g. record this finding on the model version via /datahub-enrich -->
