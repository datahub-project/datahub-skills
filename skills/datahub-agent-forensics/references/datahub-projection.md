# DataHub decision projection

Use DataHub Documents and relationships as governed summaries of agent decisions.
Search can discover a candidate Document; a direct entity read establishes which
aspects and managed properties DataHub currently stores.

## Retrieval discipline

1. Search for candidate decision, agent, incident, and data-asset URNs.
2. Directly fetch the selected entities and required aspects.
3. Preserve unknown, missing, or permission-hidden aspects.
4. Record the exact Document URN, referenced asset URNs, timestamps, and managed
   properties used in the finding.
5. For integrity questions, fetch the authoritative receipt and use its configured
   deterministic verifier.
6. For a requested write, use a deterministic identifier and directly read back the
   exact aspects written before claiming success.

## Claim boundary

A projection may record receipt identifiers, digests, counts, policy versions,
impact states, and referenced URNs. These fields are useful governed context, but
they do not independently prove the authoritative receipt or its signatures.

Generic DataHub lineage explains potential data flow. Require run-specific receipt
evidence before claiming that a particular decision consumed an asset or field.
