#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/test-helpers.sh"

echo "=== datahub-audit skill tests ==="

echo "Test 1: systematic coverage requests produce an audit report"
output=$(run_claude "Audit the metadata coverage of production Snowflake datasets and report percentages and gaps." 60)
assert_contains "$output" "coverage\|percentage\|denominator" \
    "should produce coverage metrics with a denominator"
assert_contains "$output" "owner\|description\|schema" \
    "should report metadata coverage categories"

echo "Test 2: audit remains read-only"
output=$(run_claude "Run a DataHub metadata audit for Finance datasets. Do not change anything." 60)
assert_contains "$output" "read.only\|no mutation\|without changing\|report" \
    "should explain the read-only boundary"
assert_not_contains "$output" "executed.*mutation\|updated.*owner\|added.*tag" \
    "should not claim metadata was changed"

echo "Test 3: unavailable fields are not counted as missing"
output=$(run_claude "In a DataHub audit, how should a field omitted by the server be counted?" 60)
assert_contains "$output" "unavailable\|not available" \
    "should distinguish unavailable from missing"
assert_contains "$output" "denominator\|percentage" \
    "should explain the denominator impact"

echo ""
echo "=== datahub-audit skill tests complete ==="
