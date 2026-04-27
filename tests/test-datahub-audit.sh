#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/test-helpers.sh"

echo "=== datahub-audit skill tests ==="

# Test 1: routes coverage audit intent correctly
echo "Test 1: recognises coverage audit intent"
output=$(run_claude "In the datahub-audit skill, what does it do when a user asks 'how complete is our metadata?'" 30)
assert_contains "$output" "coverage\|audit\|completeness\|systematic" \
    "should recognise coverage audit intent"

# Test 2: confirms scope before executing
echo "Test 2: confirms audit scope with user before running queries"
output=$(run_claude "In the datahub-audit skill, what does it do before running any queries?" 30)
assert_contains "$output" "scope\|confirm\|platform\|entity.type\|proceed" \
    "should confirm scope with user before executing"

# Test 3: checks siblings for description coverage
echo "Test 3: checks siblings when measuring description coverage"
output=$(run_claude "In the datahub-audit skill, how does it handle dbt and Snowflake sibling entities when checking description coverage?" 30)
assert_contains "$output" "sibling\|dbt\|primary\|isPrimary\|deduplic" \
    "should check siblings to avoid false undocumented counts"

# Test 4: calculates percentages
echo "Test 4: calculates coverage percentages"
output=$(run_claude "In the datahub-audit skill, how does it calculate coverage metrics?" 30)
assert_contains "$output" "percent\|%\|total\|numerator\|denominator\|coverage" \
    "should calculate coverage percentages"

# Test 5: applies score thresholds
echo "Test 5: applies score thresholds to coverage results"
output=$(run_claude "In the datahub-audit skill, what are the score thresholds for coverage percentages?" 30)
assert_contains "$output" "80\|50\|green\|yellow\|red\|good\|critical\|attention" \
    "should apply score thresholds (>=80 good, 50-79 attention, <50 critical)"

# Test 6: distinguishes audit from search
echo "Test 6: redirects single-entity questions to datahub-search"
output=$(run_claude "In the datahub-audit skill, what should it do if a user asks 'who owns the orders table?'" 30)
assert_contains "$output" "search\|datahub-search\|redirect\|single.entity\|ad.hoc" \
    "should redirect single-entity questions to /datahub-search"

# Test 7: suggests enrich for fixing gaps
echo "Test 7: suggests /datahub-enrich to fix identified gaps"
output=$(run_claude "In the datahub-audit skill, what does it suggest after generating a coverage report?" 30)
assert_contains "$output" "enrich\|datahub-enrich\|fix\|update\|next.step" \
    "should suggest /datahub-enrich to fix identified gaps"

# Test 8: governance audit covers deprecation hygiene
echo "Test 8: governance audit checks deprecation hygiene"
output=$(run_claude "In the datahub-audit skill, what does a governance audit check for regarding deprecated entities?" 30)
assert_contains "$output" "deprecat\|downstream\|consumer\|lineage\|risk" \
    "should check deprecated entities for active downstream consumers"

echo ""
echo "=== datahub-audit tests complete ==="
