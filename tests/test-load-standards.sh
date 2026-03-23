#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/test-helpers.sh"

echo "=== load-standards skill tests ==="

# Test 1: loads files, doesn't answer from memory
echo "Test 1: loads actual files rather than answering from memory"
output=$(run_claude "What are the connector standards?" 60)
assert_contains "$output" "Read\|load\|reading\|loaded" \
    "should read files, not answer from training data"
assert_contains "$output" "22\|twenty-two" \
    "should mention all 22 standards"

# Test 2: all three categories covered
echo "Test 2: covers all three standard categories"
output=$(run_claude "Load the DataHub standards and summarize what was loaded." 60)
assert_contains "$output" "core\|Core" \
    "should mention core standards"
assert_contains "$output" "interface\|Interface\|sql\|api\|lineage" \
    "should mention interface standards"
assert_contains "$output" "source.type\|source_type\|bi_tools\|nosql\|streaming" \
    "should mention source-type standards"

# Test 3: asks what's next after loading
echo "Test 3: asks what the user needs help with after loading"
output=$(run_claude "Load golden standards before I start building a connector." 60)
assert_contains "$output" "help\|next\|work\|build\|develop" \
    "should ask what connector work is needed"

echo ""
echo "=== load-standards tests complete ==="
