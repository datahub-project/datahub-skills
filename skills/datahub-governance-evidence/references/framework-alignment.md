# Optional framework evidence alignment

Use this reference only when the user requests framework-oriented navigation.
These are narrow, project-authored mappings from catalog observations to
review objectives. Identifiers point to authoritative sources; the language
below does not reproduce framework requirements.

Never turn these mappings into grades, thresholds, pass/fail states, readiness
ratings, conformity decisions, legal advice, or claims that an objective is
satisfied. Preserve `Observed`, `Not observed`, and `Unable to determine`
populations for every relevant signal.

## Signal vocabulary

- `ownership`: assigned DataHub owners
- `documentation`: direct dataset descriptions
- `domain`: assigned DataHub domains
- `asset_classification`: asset tags or glossary terms
- `field_classification`: field tags or glossary terms
- `lineage`: catalog lineage in the recorded direction and depth
- `retention_intent`: a user-bound retention Structured Property
- `backup_decision`: a user-bound backup-decision Structured Property

Before using `retention_intent` or `backup_decision`, require the user or
catalog administrator to provide the exact Structured Property qualified name.
Do not guess it. Omit an objective when its required property is unbound.

## Project-authored profiles

Profiles are listed alphabetically. Titles are concise navigation labels, not
authoritative framework text.

| Profile       | Objective                      | Review focus                              | Relevant signals                                                                              | Evidence relevance                                                                                                         | Limitations                                                                                                              |
| ------------- | ------------------------------ | ----------------------------------------- | --------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| CSA AICM      | DSP-03                         | Data inventory context                    | `domain`, `documentation`                                                                     | Domains and descriptions make selected datasets easier to organize and review.                                             | Does not establish that all data is cataloged, accurate, or current.                                                     |
| CSA AICM      | DSP-04                         | Recorded data classification              | `field_classification`                                                                        | Explicit field tags or terms show where selected classification decisions are catalog-visible.                             | Does not establish classification coverage, correctness, criteria, or handling.                                          |
| CSA AICM      | DSP-05                         | Data-flow records                         | `lineage`                                                                                     | Registered lineage supplies catalog-visible relationship evidence.                                                         | Does not establish complete flows, transformations, boundaries, or recipients.                                           |
| CSA AICM      | DSP-06                         | Ownership context                         | `ownership`                                                                                   | Assigned owners identify catalog-visible accountable parties.                                                              | Does not establish acceptance, authority, procedures, or effectiveness.                                                  |
| CSA AICM      | DSP-16                         | Recorded retention intent                 | `retention_intent`                                                                            | A bound Structured Property shows where retention intent is recorded.                                                      | Does not validate the period or prove deletion, disposition, or enforcement.                                             |
| CSA AICM      | DSP-17                         | Sensitive-field identification            | `field_classification`                                                                        | Explicit field labels provide a population for sensitivity review.                                                         | Does not validate labels or prove protective safeguards.                                                                 |
| CSA AICM      | DSP-20                         | Stated context and provenance             | `documentation`, `lineage`                                                                    | Descriptions and lineage provide complementary purpose and relationship context.                                           | Does not establish provenance completeness, authenticity, or transformation accuracy.                                    |
| GDPR          | Article 30                     | Processing-record inputs                  | `ownership`, `domain`, `documentation`, `field_classification`, `lineage`, `retention_intent` | Catalog context can support assembly or reconciliation of selected processing-record inputs.                               | A dataset is not a processing activity; this is not legal advice and omits many required determinations.                 |
| GDPR          | Article 5(1)(e)                | Recorded retention intent                 | `retention_intent`                                                                            | A bound Structured Property makes stated retention intent reviewable.                                                      | Does not identify personal data, validate necessity or periods, or prove deletion.                                       |
| HIPAA         | 45 CFR 164.308(a)(1)(ii)(A)    | ePHI risk-analysis scoping inputs         | `ownership`, `domain`, `documentation`, `field_classification`, `lineage`                     | Catalog context can help assemble systems, data, and relationships for accountable risk-analysis scoping.                  | Does not determine applicability, identify all ePHI, assess risk, or evaluate safeguards.                                |
| HIPAA         | 45 CFR 164.502(b) / 164.514(d) | Minimum-necessary review inputs           | `field_classification`, `documentation`                                                       | Field labels and descriptions can help identify recorded information categories and stated context.                        | Does not determine PHI, purpose, access, exceptions, or policy effectiveness.                                            |
| ISO/IEC 27001 | A.5.9                          | Information-asset inventory context       | `ownership`, `domain`, `documentation`                                                        | Ownership, domains, and descriptions provide catalog-visible inventory context.                                            | Does not establish complete, maintained, accurate, or appropriate inventory records.                                     |
| ISO/IEC 27001 | A.5.12                         | Recorded classification decisions         | `field_classification`                                                                        | Explicit field labels show where selected classification decisions are catalog-visible.                                    | Does not establish the classification scheme, coverage, accuracy, or handling.                                           |
| ISO/IEC 27001 | A.5.13                         | Recorded field labels                     | `field_classification`                                                                        | Explicit tags or terms show where field-level labels are present.                                                          | Does not establish organization-wide procedures, alignment, accuracy, or resulting handling.                             |
| ISO/IEC 42001 | A.4.3                          | AI data-resource documentation inputs     | `documentation`, `lineage`, `field_classification`, `retention_intent`                        | Descriptions, relationships, labels, and retention intent provide reusable catalog context for selected AI data resources. | Does not identify the complete AI boundary or establish quality, bias, preparation, disposal, or documentation accuracy. |
| ISO/IEC 42001 | A.7.5                          | Data provenance inputs                    | `lineage`                                                                                     | Registered relationships provide machine-readable provenance inputs.                                                       | Does not prove completeness, source authenticity, transformation accuracy, or AI use.                                    |
| SOC 2         | CC2.1                          | Catalog information supporting review     | `documentation`, `lineage`, `field_classification`                                            | Descriptions, relationships, and labels provide catalog-visible information for reviewer use.                              | Does not establish information quality, communication, operating effectiveness, or criterion satisfaction.               |
| SOC 2         | A1.2                           | Recorded backup decision                  | `backup_decision`                                                                             | A bound Structured Property shows where an accountable backup decision is recorded.                                        | Does not validate the decision or prove backup, protection, restoration, or recovery capability.                         |
| SOC 2         | C1.1                           | Confidential-information retention inputs | `documentation`, `field_classification`, `retention_intent`                                   | Labels, context, and retention intent provide a population for accountable review.                                         | Does not establish complete identification, necessity, valid periods, exceptions, or deletion.                           |
| SOC 2         | C1.2                           | Disposition-review inputs                 | `field_classification`, `retention_intent`                                                    | Labels and retention intent identify catalog records that may need disposition review.                                     | Does not establish expiration, holds, authorization, destruction, or lifecycle operation.                                |
| SOC 2         | PI1.2                          | Declared input relationships              | `lineage`                                                                                     | Registered lineage records declared upstream or downstream relationships.                                                  | Does not establish complete, accurate, timely, or validated input activity.                                              |
| SOC 2         | P4.2                           | Personal-information retention inputs     | `field_classification`, `retention_intent`                                                    | Reviewed personal-information labels plus recorded retention intent identify a catalog-visible review population.          | Does not establish complete identification, appropriate periods, exceptions, deletion, or lifecycle enforcement.         |

## Output rules

For each selected objective:

1. Copy only its identifier and project-authored mapping language.
2. Include its review focus and the DataHub source surfaces used.
3. List per-signal counts plus the exact relevant state URNs; do not collapse
   multiple signals into one result.
4. Name missing property definitions/bindings or collection failures as `Unable to
determine` inputs.
5. Include the objective-specific limitation.
6. Link users to the authoritative source instead of quoting it:
   - CSA AICM: <https://cloudsecurityalliance.org/artifacts/ai-controls-matrix>
   - GDPR: <https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng>
   - HIPAA: <https://www.hhs.gov/hipaa/for-professionals/index.html>
   - ISO/IEC 27001: <https://www.iso.org/standard/27001>
   - ISO/IEC 42001: <https://www.iso.org/standard/81230.html>
   - SOC 2: <https://www.aicpa-cima.com/resources/landing/system-and-organization-controls-soc-suite-of-services>
