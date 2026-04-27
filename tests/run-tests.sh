#!/usr/bin/env bash
# Run all datahub-skills tests.
# Usage: ./tests/run-tests.sh [--test test-name] [--model model-id] [--verbose]
#
# Options:
#   --test NAME    Run only the test file matching NAME (e.g. --test load-standards)
#   --model ID     Claude model to use (default: claude-haiku-4-5-20251001)
#                  Examples: claude-haiku-4-5-20251001, claude-sonnet-4-6, claude-opus-4-6
#   --verbose      Show full Claude output on failures

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

VERBOSE=false
FILTER=""
export TEST_MODEL="${TEST_MODEL:-claude-haiku-4-5-20251001}"

while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose) VERBOSE=true; shift ;;
        --test)    FILTER="$2"; shift 2 ;;
        --model)   export TEST_MODEL="$2"; shift 2 ;;
        *) echo "Unknown argument: $1"; exit 1 ;;
    esac
done

# Check claude is available
if ! command -v claude &>/dev/null; then
    echo "Error: 'claude' CLI not found. Install Claude Code first."
    exit 1
fi

echo "Claude Code: $(claude --version 2>/dev/null || echo 'unknown version')"
echo "Model:       $TEST_MODEL"
echo ""

TESTS=(
    "$SCRIPT_DIR/test-load-standards.sh"
    "$SCRIPT_DIR/test-connector-planning.sh"
    "$SCRIPT_DIR/test-connector-pr-review.sh"
    "$SCRIPT_DIR/test-datahub-audit.sh"
)

passed=0
failed=0
skipped=0

for test_file in "${TESTS[@]}"; do
    test_name="$(basename "$test_file" .sh | sed 's/^test-//')"

    if [ -n "$FILTER" ] && [[ "$test_name" != *"$FILTER"* ]]; then
        echo "SKIP $test_name"
        ((skipped++))
        continue
    fi

    chmod +x "$test_file"
    echo "Running: $test_name"

    if $VERBOSE; then
        if bash "$test_file"; then
            ((passed++))
        else
            ((failed++))
        fi
    else
        output=$(bash "$test_file" 2>&1) && exit_code=0 || exit_code=$?
        if [ "$exit_code" -ne 0 ] || echo "$output" | grep -q "\[FAIL\]"; then
            echo "$output"
            ((failed++))
        else
            echo "$output" | grep -E "PASS|complete"
            ((passed++))
        fi
    fi
    echo ""
done

echo "Results: $passed passed, $failed failed, $skipped skipped"
[ "$failed" -eq 0 ]
