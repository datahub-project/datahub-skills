#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/test-helpers.sh"

echo "=== load-standards skill tests ==="

# Test 1: loads all 22 files including source_types subdirectory
echo "Test 1: loads all 22 standards including source-type files"
output=$(run_claude "Load all DataHub connector standards." 60)
assert_contains "$output" "22\|twenty-two" \
    "should load and report all 22 standard files"
assert_contains "$output" "source.type\|source_type\|bi_tools\|nosql\|streaming" \
    "should load source-type standards from subdirectory"

# Test 2: all three categories covered
echo "Test 2: covers all three standard categories"
output=$(run_claude "Load the DataHub standards and summarize what was loaded." 60)
assert_contains "$output" "core\|Core" \
    "should mention core standards"
assert_contains "$output" "interface\|Interface\|sql\|api\|lineage" \
    "should mention interface standards"
assert_contains "$output" "source.type\|source_type\|bi_tools\|nosql\|streaming" \
    "should mention source-type standards"

# Test 3: "what are the standards" triggers the skill, not a memory answer
echo "Test 3: natural language question triggers skill, not a memory answer"
output=$(run_claude "What are the connector standards?" 60)
assert_contains "$output" "Read\|load\|reading\|loaded\|standards/" \
    "should load files rather than answer from training data"

# Test 4: asks what's next after loading
echo "Test 4: asks what the user needs help with after loading"
output=$(run_claude "Load golden standards before I start building a connector." 60)
assert_contains "$output" "help\|next\|work\|build\|develop" \
    "should ask what connector work is needed"

echo ""
echo "=== load-standards tests complete ==="
