# Replay and approval safety reference

## Modes

- `PINNED`: original receipt context only.
- `CORRECTED`: at least one named context replacement with verification authority.
- `COUNTERFACTUAL`: exactly one named replacement.
- `DRY`: reconstruct and inspect; never authorize execution.

Missing input, model parameters, feature flags, tool/model versions, source digests,
or context verification never triggers current-version substitution.

## Policy outcomes

- Complete exact read-only recipe: `ALLOW`.
- Reversible action with rollback and idempotency: fresh approval required.
- Unknown/incomplete material: `DRY_RUN_ONLY` or `BLOCK`.
- Irreversible action: never automatic execution.

Approval must bind the exact bundle ID, action-set digest, environment, policy,
scope, issuer, reason digest, issue/expiry, revocation state, and a configured trusted
signer. A valid self-contained signature alone does not establish authority.

## History and comparison

Execution must produce a new signed decision receipt linked by the prior payload
digest. Failed replay also gets a receipt. Never overwrite the source.

Structural diff may expose paths, types, change kinds, and value digests, not raw
values. Built-in semantic equality means exact output equality only. A separate
supersession record links source receipt, replay receipt, bundle, plan, execution,
and diff.

The reference executor is capability-scoped but in-process. Do not describe it as an
OS/network sandbox.
