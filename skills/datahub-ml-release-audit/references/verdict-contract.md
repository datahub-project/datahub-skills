# ML leakage verdict contract

Use the least certain verdict supported by the evidence. Statistical importance is context only and never changes a verdict by itself.

| Verdict                 | Minimum evidence                                                                                                                                | Release action |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | -------------- |
| `insufficient_metadata` | Model scope, prediction cutoff, column lineage, transformation semantics, or authoritative availability time is missing                         | Hold           |
| `needs_review`          | Suspicious outcome ancestry exists, but direction or the availability-time violation is unresolved                                              | Hold           |
| `high_confidence`       | Exact directional outcome/post-outcome lineage and `available_at > prediction_time` are established                                             | Block          |
| `confirmed`             | `high_confidence` evidence plus either deterministic transformation/cutoff proof or a policy-qualified point-in-time collapse                   | Block          |
| `clear_for_release`     | Required metadata is complete, no availability violation is present, configured tests pass, and a predictive pre-cutoff control remains allowed | Allow          |

## Confirmation routes

### Deterministic route

Require all of:

1. An exact outcome or post-outcome field is an ancestor of a model feature.
2. The path direction reaches the feature or training snapshot.
3. Transformation semantics admit records whose authoritative availability time is after prediction.
4. The SQL, code, or equivalent cutoff proof is reproducible.

### Point-in-time reconstruction route

Require all of:

1. The `high_confidence` evidence above.
2. A reconstruction enforcing `available_at <= prediction_time`.
3. Identical metric, data split, seed, and evaluation protocol.
4. Advantage collapse under a threshold configured before the result was observed.
5. A predictive pre-cutoff control that does not falsely collapse.

Record the observed metric, point-in-time metric, baseline, advantage retained, threshold, and margin. Describe the threshold as policy—not a universal scientific constant.

## Machine-readable evidence keys

The bundled validator accepts a JSON object with:

- `verdict`: one of the five verdicts above;
- `model_urn`: non-empty string;
- `prediction_time`: non-empty timestamp string for `high_confidence`, `confirmed`, and `clear_for_release`;
- `directional_outcome_lineage`: boolean;
- `availability_violation`: boolean;
- `deterministic_cutoff_proof`: boolean;
- `point_in_time`: object with `performed`, `advantage_retained`, and `collapse_threshold`;
- `safe_control`: object with `performed` and `remained_safe`.

The validator checks logical consistency. It does not determine truth and cannot replace DataHub rereads or human review.
