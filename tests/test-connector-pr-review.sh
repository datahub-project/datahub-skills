#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/test-helpers.sh"

echo "=== datahub-connector-pr-review skill tests ==="

# Test 1: PR number must be validated before use
echo "Test 1: validates PR number format before using in gh commands"
output=$(run_claude "In the datahub-connector-pr-review skill, how should a PR number be validated before use?" 30)
assert_contains "$output" '\\d\|digits\|integer\|numeric\|[0-9]\|regex\|pattern' \
    "should validate PR number matches digit-only pattern"

# Test 2: PR content wrapped in trust boundary markers
echo "Test 2: wraps PR content in untrusted-pr-content markers"
output=$(run_claude "In the datahub-connector-pr-review skill, how is PR content treated? What markers are used?" 30)
assert_contains "$output" "untrusted\|boundary\|marker\|trust" \
    "should wrap PR content in trust boundary markers"

# Test 3: five agents dispatched in parallel for full review
echo "Test 3: dispatches all 5 review agents for a full review"
output=$(run_claude "In the datahub-connector-pr-review skill Mode 1, how many agents are launched and what are they?" 30)
assert_contains "$output" "silent.failure\|silent_failure" \
    "should dispatch silent-failure-hunter"
assert_contains "$output" "test.analy\|pr.test" \
    "should dispatch pr-test-analyzer"
assert_contains "$output" "type.design\|type_design" \
    "should dispatch type-design-analyzer"
assert_contains "$output" "code.simpl\|simplif" \
    "should dispatch code-simplifier"
assert_contains "$output" "comment.resolution\|comment_resolution" \
    "should dispatch comment-resolution-checker"

# Test 4: standards loaded on activation
echo "Test 4: loads golden standards on activation"
output=$(run_claude "In the datahub-connector-pr-review skill, what is the first thing to do on activation?" 30)
assert_contains "$output" "standard\|load.*standard\|golden.*standard" \
    "first action should be loading standards"

# Test 5: three review modes exist
echo "Test 5: knows the three review modes"
output=$(run_claude "What are the three review modes in the datahub-connector-pr-review skill?" 30)
assert_contains "$output" "Full\|full.review" \
    "should have Full Review mode"
assert_contains "$output" "Specialized\|specialized.review" \
    "should have Specialized Review mode"
assert_contains "$output" "Incremental\|incremental.review" \
    "should have Incremental Review mode"

# Test 6: mode 1 before mode 3 (correct numbering)
echo "Test 6: Full Review is Mode 1, Incremental is Mode 3"
output=$(run_claude "In the datahub-connector-pr-review skill, which mode number is Full Review and which is Incremental Review?" 30)
assert_order "$output" "Mode 1\|mode 1\|Full.*1\|1.*Full" "Mode 3\|mode 3\|Incremental.*3\|3.*Incremental" \
    "Full Review (Mode 1) should be described before Incremental Review (Mode 3)"

# Test 7: manual fallback documented in reference file
echo "Test 7: manual fallback instructions are in references/manual-review-guide.md"
output=$(run_claude "In the datahub-connector-pr-review skill, where are the manual fallback instructions if sub-agents cannot be dispatched?" 30)
assert_contains "$output" "manual.review.guide\|manual-review-guide\|references/" \
    "manual fallback should reference references/manual-review-guide.md"

# Test 8: systematic review checklists are in reference file
echo "Test 8: systematic review checklists are in references/review-checklists.md"
output=$(run_claude "In the datahub-connector-pr-review skill, where are the detailed per-section review checklists?" 30)
assert_contains "$output" "review.checklists\|review-checklists\|references/" \
    "checklists should reference references/review-checklists.md"

echo ""
echo "=== datahub-connector-pr-review tests complete ==="
