## Community Test Feedback — {{CONNECTOR_NAME}}

**Tested by:** @{{TESTER_HANDLE}} &nbsp;·&nbsp; **Source:** {{SOURCE_NAME}} {{SOURCE_VERSION}} ({{SOURCE_DEPLOYMENT}}) &nbsp;·&nbsp; **DataHub:** {{DATAHUB_ENV}} &nbsp;·&nbsp; **Date:** {{DATE}}

{{#if INGESTION_RAN}}
**Ingestion:** {{ENTITY_COUNT}} entities ingested in {{INGESTION_DURATION}}
{{/if}}

---

### Feature Support

<!-- ✅ Working | ⚠️ Partial | ❌ Not working | N/A -->

| Schema | Lineage | Profiling | Usage | Tags | Owners |
|--------|---------|-----------|-------|------|--------|
| {{SCHEMA_STATUS}} | {{LINEAGE_STATUS}} | {{PROFILING_STATUS}} | {{USAGE_STATUS}} | {{TAGS_STATUS}} | {{OWNERS_STATUS}} |

**Setup difficulty:** {{SETUP_DIFFICULTY}} &nbsp;·&nbsp; **Config intuitiveness:** {{CONFIG_SCORE}}/5

---

### Top Issues

{{#if HAS_ISSUES}}
{{ISSUE_1}}
{{ISSUE_2}}
{{ISSUE_3}}
{{else}}
No issues found during this test run.
{{/if}}

---

### Verdict: {{VERDICT}}

<!-- ✅ Ready | ⚠️ Ready with minor issues | ❌ Needs work before production use -->

**Would use in production:** {{PRODUCTION_READINESS}}

{{#if TOP_IMPROVEMENT}}
**Top request:** {{TOP_IMPROVEMENT}}
{{/if}}

{{#if OUT_OF_SCOPE}}
> **Note:** Some scenarios were out of scope for this test:
> {{OUT_OF_SCOPE_BRIEF}}
{{/if}}

<details>
<summary>Full test notes</summary>

**Test scope:** {{TEST_SCOPE_ASSETS}} — {{TEST_SCOPE_FEATURES}}

**Environment:** {{SOURCE_NAME}} {{SOURCE_VERSION}} · {{SOURCE_DEPLOYMENT}} · DataHub {{DATAHUB_ENV}}

**Verification results:**
{{VERIFICATION_SUMMARY}}

**Configuration notes:**
{{CONFIG_NOTES}}

**Additional observations:**
{{ADDITIONAL_NOTES}}

{{#if LINEAGE_OUT_OF_SCOPE}}
**Lineage use cases not covered:**
{{LINEAGE_OUT_OF_SCOPE}}
{{/if}}

</details>

---

*Tested using the [DataHub Connector Community Feedback skill](https://github.com/datahub-project/datahub-skills). No credentials were shared in this session.*
