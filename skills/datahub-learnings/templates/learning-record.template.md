# Learning Record Template

One learning = one single-line JSON object (shown pretty-printed here for
readability; serialize with `separators=(",", ":")` before writing). Field
definitions: `protocol/SPEC.md` §4, condensed in `../references/protocol-reference.md`.

```jsonc
{
  "id": "<uuid4, generated fresh, never reused>",
  "kind": "semantic_gotcha", // semantic_gotcha | verified_query | join_path | caveat | metric_definition
  "subject_urn": "urn:li:dataset:(urn:li:dataPlatform:<platform>,<qualified_name>,<env>)",
  "subject_field": "amount", // OMIT this key entirely for table-level learnings
  "claim": "<1-2 sentences, <=280 chars, plain language>",
  "evidence": "<concrete, checkable support: a query + result, a count, a named comparison; <=500 chars>",
  "confidence": "high", // high | medium | low -- apply the SPEC.md §4 definitions exactly, do not inflate
  "learned_by": "<agent-name>/<session-id>",
  "learned_at": "2026-07-29", // YYYY-MM-DD
  "status": "active", // optional, default active -- active | disputed | conflict
  "conflicts_with": null, // only present when status: conflict -- the id of the disputed record
}
```

## Checklist before writing (SPEC.md §7, see SKILL.md Workflow 2 Step 2 for the full walkthrough)

- [ ] (a) No secrets, no row-level/PII data: evidence is aggregate only
- [ ] (b) Not something already obvious from the schema or existing docs
- [ ] (c) Recall re-run against this subject; not a duplicate of an existing active learning
- [ ] (d) `confidence` matches the SPEC.md §4 definition exactly; `evidence` is re-runnable
- [ ] (e) Does not contradict an existing active learning (if it does: Conflict Procedure, not this template)
- [ ] (f) About the data itself, not the requesting task/user/session
