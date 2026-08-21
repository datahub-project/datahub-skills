Conflict Scoring Reference
This reference backs the `datahub-semantic-consistency` skill. It defines how to group
concepts, score conflicts, and assign confidence and severity.
Concept grouping
Two definitions belong to the same concept group if their names match after normalization
or they are known synonyms.
Normalization steps:
Lowercase.
Collapse separators: `active_user`, `active user`, `active-user` → `active user`.
Expand common abbreviations: `MAU` → `monthly active user`, `DAU` → `daily active user`, `ARR` → `annual recurring revenue`.
Synonym pairs to treat as the same concept (extend as needed):
Concept A	Concept B
churn	attrition
revenue	net revenue
customer	account
active user	engaged user
signup	registration
Grouping only makes two definitions candidates for comparison. Whether they actually
conflict is decided by the severity rubric below.
Severity rubric
Severity	Meaning	Action
HIGH	Definitions clearly compute a different population or value	Report and prioritize
MEDIUM	Definitions likely diverge but wording is ambiguous	Report, flag for human review
LOW	Cosmetic wording difference only	Suppress by default
What raises severity to HIGH:
Different time window (7-day vs. 30-day).
Different population filter (authenticated-only vs. includes anonymous).
Different event basis (any view vs. completed key action).
Different unit or currency.
Different grain (per-user vs. per-account).
What keeps it at LOW (not a real conflict):
Same computation, reworded.
Abbreviation vs. spelled-out form of the identical definition.
Formatting or punctuation differences only.
Confidence
Confidence is how sure you are the definitions truly diverge, independent of severity.
0.90–1.00 — explicit contradicting parameters in both definitions (e.g., "7 days" vs. "30 days").
0.70–0.89 — strongly implied divergence, one side ambiguous.
0.50–0.69 — plausible divergence, both sides vague; needs human confirmation.
Below 0.50 — do not report as a conflict.
Blast-radius counting
Count distinct downstream assets that inherit the conflicting definition, one hop is
usually enough for prioritization:
Datasets, dashboards, charts, ML features, and metrics that reference the term or a
dataset carrying the term.
Report the total and a type breakdown (e.g., "12 assets: 7 dashboards, 3 datasets, 1 ML feature, 1 metric").
Illustrative cost estimates
If (and only if) the user asks for a cost estimate, label it clearly as illustrative and
state the assumption. Example: "Assuming roughly 1 analyst-hour to manually reconcile each
affected dashboard, 12 affected assets implies ~12 analyst-hours avoided." Never present
these numbers as measured facts.
