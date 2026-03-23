#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/test-helpers.sh"

echo "=== datahub-connector-planning skill tests ==="

# Test 1: classifies SQL sources correctly
echo "Test 1: classifies ClickHouse as SQL/data warehouse"
output=$(run_claude "In the datahub-connector-planning skill, what category would ClickHouse be classified as?" 30)
assert_contains "$output" "SQL\|sql\|data.warehouse\|warehouse" \
    "ClickHouse should be classified as SQL/data warehouse"

# Test 2: classifies API sources correctly
echo "Test 2: classifies Tableau as API/BI tool"
output=$(run_claude "In the datahub-connector-planning skill, what category would Tableau be classified as?" 30)
assert_contains "$output" "API\|api\|BI\|bi.tool\|business.intell" \
    "Tableau should be classified as API/BI tool"

# Test 3: classifies NoSQL sources correctly
echo "Test 3: classifies MongoDB as NoSQL"
output=$(run_claude "In the datahub-connector-planning skill, what category would MongoDB be classified as?" 30)
assert_contains "$output" "NoSQL\|nosql\|document\|non.relational" \
    "MongoDB should be classified as NoSQL"

# Test 4: confirms classification with user before proceeding
echo "Test 4: confirms classification with user before researching"
output=$(run_claude "In the datahub-connector-planning skill, what does it do after classifying the source type?" 30)
assert_contains "$output" "confirm\|confirm.*user\|user.*confirm\|approval\|approve\|validate.*user" \
    "should confirm classification with user before proceeding"

# Test 5: uses connector-researcher agent
echo "Test 5: dispatches connector-researcher agent for research"
output=$(run_claude "In the datahub-connector-planning skill, how does Step 2 research work? What agent is used?" 30)
assert_contains "$output" "connector-researcher\|researcher.*agent\|research.*agent" \
    "should dispatch connector-researcher agent"

# Test 6: produces a _PLANNING.md file
echo "Test 6: output is a _PLANNING.md document"
output=$(run_claude "What does the datahub-connector-planning skill produce as its final output?" 30)
assert_contains "$output" "_PLANNING\|PLANNING.md\|planning.*document\|planning.*file" \
    "final output should be a _PLANNING.md document"

# Test 7: user approval before completion
echo "Test 7: requests user approval before finishing"
output=$(run_claude "Does the datahub-connector-planning skill require user approval before completing? When?" 30)
assert_contains "$output" "approval\|approve\|confirm\|Step 4\|step 4" \
    "should require user approval at Step 4"

echo ""
echo "=== datahub-connector-planning tests complete ==="
