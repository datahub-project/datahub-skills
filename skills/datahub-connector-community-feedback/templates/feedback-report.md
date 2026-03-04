# Community Feedback: {{CONNECTOR_NAME}}

**PR / Version:** {{PR_OR_VERSION}}
**Tested by:** {{TESTER_HANDLE}}
**Date:** {{DATE}}

---

**Source system:** {{SOURCE_NAME}} {{SOURCE_VERSION}} · {{SOURCE_DEPLOYMENT}}
**DataHub environment:** {{DATAHUB_ENV}}
**Testing mode:** {{TESTING_MODE}}
**Ingestion run:** {{INGESTION_TIMESTAMP}} · {{ENTITY_COUNT}} entities · {{INGESTION_DURATION}}

<!-- INGESTION_TIMESTAMP, ENTITY_COUNT, INGESTION_DURATION: fill from ingestion output.
     If ingestion was not run in this session, write "not run in this session". -->

---

## Test Scope

**What was tested:**
{{TEST_SCOPE_ASSETS}} — {{TEST_SCOPE_FEATURES}}

**Explicitly out of scope:**
{{OUT_OF_SCOPE_ITEMS}}

<!-- Examples of out-of-scope entries:
  - Cross-platform lineage (Snowflake → dbt): prerequisite dbt ingestion not configured
  - Data profiling: not selected for this test run
  - Usage statistics: feature not implemented in this PR
-->

---

## Verification Results

<!-- Results from Phase 5 checklist. Status: ✅ Pass | ❌ Fail | ⚠️ Partial | N/A -->

| Scenario | Status | Notes |
|----------|--------|-------|
| Browse & discovery | {{STATUS}} | {{NOTES}} |
| Schema quality | {{STATUS}} | {{NOTES}} |
| {{FEATURE_1}} | {{STATUS}} | {{NOTES}} |
| {{FEATURE_2}} | {{STATUS}} | {{NOTES}} |
| {{FEATURE_3}} | {{STATUS}} | {{NOTES}} |

---

## Setup Experience

**Installation:** {{INSTALL_RESULT}}
<!-- e.g., "Smooth — no issues" or "Required: pip install psycopg2-binary separately" -->

**Time from zero to first successful ingest:** {{SETUP_TIME}}

**Configuration intuitiveness:** {{CONFIG_SCORE}}/5
{{CONFIG_NOTES}}

**Authentication & permissions setup:**
{{AUTH_NOTES}}
<!-- Production path only. Skip for quickstart. -->

**Documentation accuracy:**
{{DOCS_NOTES}}

---

## Asset Coverage

<!-- Production path only. Fill from ingestion output + tester input. -->
<!-- Skip this section if testing via Quickstart or no live instance. -->

| Asset type | Expected (approx.) | Found | Gap |
|------------|---------------------|-------|-----|
| {{ASSET_TYPE_1}} | ~{{EXPECTED}} | {{FOUND}} | {{GAP_DESCRIPTION}} |
| {{ASSET_TYPE_2}} | ~{{EXPECTED}} | {{FOUND}} | {{GAP_DESCRIPTION}} |

**Missing or unexpected assets:**
{{MISSING_ASSETS}}

---

## Feature Support Matrix

<!-- Status: ✅ Working | ⚠️ Partial | ❌ Not working | N/A (not tested / not applicable) -->

| Feature | Status | Notes |
|---------|--------|-------|
| Schema metadata (columns, types) | {{STATUS}} | {{NOTES}} |
| Data lineage | {{STATUS}} | {{NOTES}} |
| Data profiling | {{STATUS}} | {{NOTES}} |
| Usage statistics | {{STATUS}} | {{NOTES}} |
| Tags / classifications | {{STATUS}} | {{NOTES}} |
| Owner mapping | {{STATUS}} | {{NOTES}} |
| Descriptions | {{STATUS}} | {{NOTES}} |
| Custom properties | {{STATUS}} | {{NOTES}} |
| {{CONNECTOR_SPECIFIC_FEATURE}} | {{STATUS}} | {{NOTES}} |

---

## Issues Found

<!-- List issues discovered during testing. Severity: Critical / High / Medium / Low / Enhancement -->
<!-- Do NOT include credentials, hostnames, or config values in reproduction steps. -->

### 1. {{ISSUE_TITLE}}

**Severity:** {{SEVERITY}}
**Feature area:** {{FEATURE_AREA}}

**What happened:**
{{ISSUE_DESCRIPTION}}

**Expected behavior:**
{{EXPECTED_BEHAVIOR}}

**Steps to reproduce:**
1. {{STEP_1}}
2. {{STEP_2}}

**Environment context:**
{{SOURCE_NAME}} {{SOURCE_VERSION}} on {{SOURCE_DEPLOYMENT}}

---

<!-- Add additional issues as needed. Delete this section if no issues were found. -->

---

## Overall Assessment

**Would use in production:** {{PRODUCTION_READINESS}}
<!-- Options: Yes / No / Yes, once [X] is fixed / Already using it -->

**Verdict:** {{VERDICT}}
<!-- Options: ✅ Ready | ⚠️ Ready with caveats | ❌ Needs work -->

**Top improvement needed:**
{{TOP_IMPROVEMENT}}

**What worked better than expected:**
{{POSITIVE_SURPRISES}}

**Security / compliance concerns:**
{{SECURITY_NOTES}}
<!-- Write "None" if no concerns. -->

---

## Cross-Platform Lineage Coverage

<!-- Only include this section if lineage was discussed in Phase 2. -->

| Scenario | In scope for this PR | Tested | Result |
|----------|---------------------|--------|--------|
| {{SOURCE}} → {{TOOL}} lineage | {{IN_SCOPE}} | {{TESTED}} | {{RESULT}} |

**Out-of-scope lineage use cases (not covered in this test):**
{{LINEAGE_OUT_OF_SCOPE}}
<!-- This is valuable to document even if not tested — it informs the connector roadmap. -->

---

*Community feedback generated with the DataHub Connector Community Feedback skill.*
*Credentials were not shared in this session.*
