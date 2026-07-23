---
name: datahub-semantic-consistency
description: |
Use this skill when the user wants to check whether two teams mean the same thing by the same metric, find semantic conflicts or "meaning drift" across the DataHub catalog, reconcile disagreeing glossary term or metric definitions, or write a single canonical definition back into DataHub. Triggers on: "do Finance and Marketing define active users the same way", "find conflicting metric definitions", "why don't these dashboards agree", "reconcile our revenue definition", "which teams disagree on churn", or any request to detect, quantify, or resolve definitional inconsistency across DataHub metadata. For plain metadata gaps ("what's undocumented"), use `/datahub-search`. For lineage traversal without a definitional angle, use `/datahub-lineage`.
user-invocable: true
min-cli-version: 1.4.0
allowed-tools: Bash(datahub *)
DataHub Semantic Consistency
You are an expert at finding where two teams silently mean different things by the same
metric. A data-quality check asks "is this value correct?" You ask a different question:
"do these two definitions actually describe the same thing?" Two dashboards can both be
100% correct and still disagree, because the humans behind them never agreed on what the
word meant. That is a meaning bug, and it is invisible to freshness, volume, and null
checks. Your job is to surface it, price it, and help a human resolve it.
This skill operates in three modes:
Detect mode: Find glossary terms and metric definitions that conflict across teams, domains, or platforms ("do Finance and Marketing define `active_user` the same way?")
Impact mode: Quantify the blast radius of a conflict — how many downstream assets inherit the ambiguous definition ("what does the `active_user` disagreement actually touch?")
Reconcile mode: Draft a single canonical definition with a before/after diff, get human approval, and write it back into DataHub ("propose one definition and update the glossary")
---
Multi-Agent Compatibility
This skill is designed to work across multiple coding agents (Claude Code, Cursor, Codex,
Copilot, Gemini CLI, Windsurf, and others).
What works everywhere:
The full detect → impact → reconcile workflow
All three modes
Reading glossary terms, descriptions, and lineage via MCP tools or the DataHub CLI
Conflict scoring, blast-radius counting, and diff generation
Writing the reconciled definition back via `datahub` CLI upsert
Claude Code-specific features (other agents can safely ignore these):
`allowed-tools` in the YAML frontmatter above
Reference file paths: Skill-specific references are in `references/`. Shared CLI docs
are in `../shared-references/datahub-cli-reference.md`.
---
Not This Skill
If the user wants to...	Use this instead
Find, browse, or list entities	`/datahub-search`
Explore lineage without a definitional question	`/datahub-lineage`
Add or update a single description/tag/owner directly	`/datahub-enrich`
Create assertions or manage incidents	`/datahub-quality`
Install the CLI or configure authentication	`/datahub-setup`
Key boundary: Enrich edits one entity's metadata on request. This skill compares
definitions across many entities, finds where they conflict, and only then proposes a
single reconciled write. If the user already knows the right definition and just wants it
applied, that's `/datahub-enrich`.
---
Step 1: Harvest Candidate Definitions
Collect the definitional metadata that could conflict. The richest sources are:
Glossary terms — the explicit definitions teams write down.
Dataset and column descriptions — where the same concept is redefined informally.
Domains and ownership — who authored each definition, so you can attribute the disagreement to real teams.
```bash
# Glossary terms and their definitions
datahub search "*" --where "entity_type = glossaryTerm" --projection "urn type
... on GlossaryTerm { properties { name description definition } domain { domain { urn } } ownership { owners { owner type } } }"

# Datasets/columns whose descriptions mention the concept under review
datahub search "active user" --projection "urn type
... on Dataset { properties { name description } editableProperties { description } domain { domain { urn } } ownership { owners { owner type } } }"
```
Group by concept, not by string. `active_user`, `active users`, `Active User` and
`MAU` may all name the same concept. Normalize casing and separators, and treat known
synonyms (`churn` ~ `attrition`, `revenue` ~ `net revenue`) as candidates for the same
group. Do not assume they are the same yet — that's Step 2.
---
Step 2: Detect Conflicts
For each concept group with two or more definitions, decide whether the definitions
actually disagree. A conflict is not "the wording differs" — it is "the wording
implies a different computation or population."
Signal	Example	Conflict?
Different time window	"active in last 7 days" vs. "active in last 30 days"	Yes
Different population filter	"logged-in users" vs. "any session incl. anonymous"	Yes
Different event basis	"any page view" vs. "completed a key action"	Yes
Same computation, reworded	"monthly active users" vs. "distinct users active this month"	No
Different unit or currency	"revenue in USD" vs. "revenue in local currency"	Yes
Assign each detected conflict a confidence (how sure you are the definitions truly
diverge) and classify severity:
HIGH — the definitions clearly compute different populations or values.
MEDIUM — the definitions likely diverge but wording is ambiguous; flag for human review.
LOW — cosmetic wording difference only; usually not a real conflict.
Report only MEDIUM and above by default. Never assert a conflict you cannot point to
specific conflicting text for — cite the exact two definitions and the two owning teams.
---
Step 3: Quantify Blast Radius
A conflict on an unused term is trivia. A conflict on a term wired into 12 dashboards is a
board-meeting problem. Count what each conflict actually touches.
```bash
# Downstream assets that consume a conflicting term/dataset
datahub search "*" --where "entity_type = dataset" --projection "urn type
... on Dataset { properties { name } downstream { total } }"
# For a specific entity, trace consumers (one hop is usually enough for pricing)
datahub get --urn "<urn>" --aspect glossaryTerms
```
For each conflict, produce:
Assets at risk — count of downstream datasets, dashboards, charts, and ML features that inherit the ambiguous definition.
Asset breakdown — e.g., "12 assets: 7 dashboards, 3 datasets, 1 ML feature, 1 metric".
A dollar/hours estimate is optional and must be labeled as illustrative, never presented as measured. If you provide one, state the assumption (e.g., "assuming ~1 analyst-hour per affected dashboard to reconcile manually").
Rank conflicts by blast radius, highest first. This is the priority order a human should
work in.
---
Step 4: Reconcile — Human Stays in Control
Draft one canonical definition per conflict. Present it as a before/after diff against
the current glossary term, and require explicit human approval before writing anything.
```markdown
## Proposed canonical definition: `active_user`

**Before (two conflicting definitions):**

- Finance / Revenue team: "a user who logged in during the last 7 days"
- Marketing / Growth team: "any user with a session in the last 30 days, incl. anonymous"

**After (proposed canonical):**

> `active_user`: a user with at least one authenticated session in the trailing 30 days.
> Anonymous sessions are excluded. Window is fixed at 30 days across all domains.

**Rationale:** aligns to the wider (30-day) window already used by 7 of 12 downstream
assets; excludes anonymous sessions per the authenticated-user standard.
```
Then ask: "Approve writing this definition to the glossary term, or edit first?" Nothing
is overwritten without a yes.
---
Step 5: Write Back to DataHub
On approval, upsert the canonical definition to the glossary term. Write the description
/ definition aspect; do not delete the conflicting terms — link or deprecate them so the
history stays visible.
```bash
# Upsert the reconciled definition (via a metadata file or MCP upsert)
datahub put --urn "urn:li:glossaryTerm:active_user" --aspect glossaryTermInfo --file canonical_active_user.json

# Optionally deprecate the losing definition rather than deleting it
datahub put --urn "<conflicting-urn>" --aspect deprecation --file deprecate_note.json
```
Confirm the write succeeded by reading the term back, and report exactly what changed.
Never claim a write happened without verifying it.
---
Reference Documents
Document	Path	Purpose
Conflict scoring reference	`references/conflict-scoring-reference.md`	Severity rubric, confidence, synonyms
CLI reference (shared)	`../shared-references/datahub-cli-reference.md`	CLI command syntax
---
Common Mistakes
Flagging wording differences as conflicts. "MAU" vs. "monthly active users" is not a conflict. Only flag when the definitions imply a different computation or population.
Asserting a conflict without evidence. Always quote the two exact definitions and name the two owning teams. No quote, no conflict.
Ignoring blast radius. A conflict on an unused term is noise. Rank by downstream impact so humans fix what matters first.
Presenting dollar figures as measured. Any cost/hours number is illustrative and must be labeled as such, with its assumption stated.
Writing without approval. Never upsert a canonical definition until a human explicitly approves the diff.
Deleting the losing definition. Deprecate or link it instead, so the reconciliation history is auditable.
Claiming a write you didn't verify. Always read the term back after writing and report what actually changed.
---
Red Flags
Only one definition exists for a concept → there is nothing to reconcile; hand off to `/datahub-enrich` if the user just wants to document it.
No downstream assets → note the conflict is low priority before spending effort on it.
User asks to write before seeing the diff → stop and show the before/after first.
Conflicting terms owned by the same person/team → likely a duplicate, not a cross-team disagreement; confirm before treating it as a conflict.
---
Remember
A meaning bug is not a data-quality bug. Both dashboards can be correct and still disagree.
Group by concept, not by string. Casing, synonyms, and abbreviations hide the same concept.
Quote the evidence. Name the two definitions and the two teams for every conflict.
Rank by blast radius. Fix the widely-inherited conflicts first.
Human approves every write. Draft, diff, approve, then upsert — and verify the result.
