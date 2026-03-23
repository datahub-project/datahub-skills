#!/usr/bin/env bash
# Shared test helpers for datahub-skills tests.
# Modelled after https://github.com/obra/superpowers/tree/main/tests/claude-code

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Model to use — defaults to Claude Code's configured model (respects skill effort: frontmatter).
# Override with TEST_MODEL env var or --model flag in run-tests.sh.
TEST_MODEL="${TEST_MODEL:-}"

# macOS ships without GNU timeout; use gtimeout (brew install coreutils) if available
_timeout_cmd() {
    if command -v gtimeout &>/dev/null; then
        gtimeout "$@"
    elif command -v timeout &>/dev/null; then
        timeout "$@"
    else
        # No timeout available — run without it
        local _t="$1"; shift
        "$@"
    fi
}

run_claude() {
    local prompt="$1"
    local timeout="${2:-60}"
    local output_file
    output_file=$(mktemp)

    local model_flag=()
    [ -n "$TEST_MODEL" ] && model_flag=(--model "$TEST_MODEL")

    if _timeout_cmd "$timeout" claude --add-dir "$REPO_ROOT" "${model_flag[@]}" -p "$prompt" >"$output_file" 2>&1; then
        cat "$output_file"
        rm -f "$output_file"
        return 0
    else
        local exit_code=$?
        cat "$output_file" >&2
        rm -f "$output_file"
        return $exit_code
    fi
}

assert_contains() {
    local output="$1"
    local pattern="$2"
    local test_name="${3:-test}"

    if echo "$output" | grep -qi "$pattern"; then
        echo "  [PASS] $test_name"
        return 0
    else
        echo "  [FAIL] $test_name"
        echo "         Expected to find: $pattern"
        echo "         In output: $(echo "$output" | head -5 | sed 's/^/           /')"
        return 1
    fi
}

assert_not_contains() {
    local output="$1"
    local pattern="$2"
    local test_name="${3:-test}"

    if echo "$output" | grep -qi "$pattern"; then
        echo "  [FAIL] $test_name"
        echo "         Did not expect to find: $pattern"
        echo "         In output: $(echo "$output" | head -5 | sed 's/^/           /')"
        return 1
    else
        echo "  [PASS] $test_name"
        return 0
    fi
}

assert_order() {
    local output="$1"
    local pattern_a="$2"
    local pattern_b="$3"
    local test_name="${4:-test}"

    local line_a line_b
    line_a=$(echo "$output" | grep -ni "$pattern_a" | head -1 | cut -d: -f1)
    line_b=$(echo "$output" | grep -ni "$pattern_b" | head -1 | cut -d: -f1)

    if [ -z "$line_a" ]; then
        echo "  [FAIL] $test_name: pattern A not found: $pattern_a"
        return 1
    fi
    if [ -z "$line_b" ]; then
        echo "  [FAIL] $test_name: pattern B not found: $pattern_b"
        return 1
    fi

    if [ "$line_a" -lt "$line_b" ]; then
        echo "  [PASS] $test_name (A at line $line_a, B at line $line_b)"
        return 0
    else
        echo "  [FAIL] $test_name"
        echo "         Expected '$pattern_a' (line $line_a) before '$pattern_b' (line $line_b)"
        return 1
    fi
}

export -f run_claude assert_contains assert_not_contains assert_order
