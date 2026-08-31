# Decision receipt evidence

A decision receipt is an immutable evidence record for one consequential agent
output. Prefer the authoritative artifact over its DataHub summary projection.

## Integrity gates

Use the receipt format's declared verifier. Common gates include:

- schema and version validation;
- canonical payload digest;
- content-addressed receipt identity;
- ordered evidence and action commitments;
- required signatures from configured trusted keys.

A failed gate makes the receipt invalid. An unavailable verifier means the receipt
is not currently verified. Signature verification establishes byte integrity and
key possession only; it does not establish that the recorded inputs were true.

## Investigation fields

Look for:

- run, agent, workflow, and environment identity;
- exact model, skill, tool, and policy version pins;
- DataHub entity and schema-field URNs with evidence state, role, digest, and time;
- ordered actions with side-effect class, outcome, input and output digests, and
  approval bindings;
- output digest and redaction status;
- replay eligibility and supersession relationships.

Preserve causal ordering when the receipt format declares order significant.

## Safe wording

Say "the verified receipt records an observed dependency" rather than "the data was
true." Say "the DataHub projection identifies receipt X" rather than "the receipt
verified" unless the authoritative artifact was actually checked.
