#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/test-helpers.sh"

echo "=== datahub-import-docs skill tests ==="

# Test 1: local-first — "this repo" reads the working tree, no clone
echo "Test 1: 'this repo' reads the local working tree without cloning"
output=$(run_claude "In the datahub-import-docs skill, if I'm inside a git checkout and say 'import docs from this repo', does it clone the repo or call a forge API? How does it read the files?" 40)
assert_contains "$output" "working tree\|on disk\|not clone\|no clone\|don't clone\|do not clone\|local" \
    "should read the local working tree directly, not clone"
assert_not_contains "$output" "always clone\|must clone the repo" \
    "should not require cloning for the local case"

# Test 2: writes via the stable datahub.sdk Document SDK, not server-side resolvers
echo "Test 2: writes through the datahub.sdk Document SDK (no server-side import resolvers)"
output=$(run_claude "In the datahub-import-docs skill, what API does it use to create the documents in DataHub? Does it depend on server-side GraphQL import resolvers?" 40)
assert_contains "$output" "datahub.sdk\|Document\|SDK\|upsert" \
    "should use the datahub.sdk Document SDK"
assert_contains "$output" "no\|not\|never\|does not\|doesn't\|stable\|without" \
    "should NOT depend on server-side import resolvers"

# Test 3: host-based namespace — forge-agnostic (GitLab/Bitbucket/self-hosted)
echo "Test 3: host-based namespace works across forges, not GitHub-only"
output=$(run_claude "In the datahub-import-docs skill, how are document IDs namespaced? Does it work for GitLab, Bitbucket, or self-hosted git, not just GitHub?" 40)
assert_contains "$output" "host\|github-com\|gitlab\|bitbucket\|self-hosted\|forge" \
    "namespace should be host-based and forge-agnostic"

# Test 4: repo becomes a folder; default mount groups by host; repos don't collide
echo "Test 4: repo is a folder, repos grouped by host, no collisions across repos"
output=$(run_claude "In the datahub-import-docs skill, how do imports from two different repos avoid colliding in DataHub? Is the repo itself represented as a folder, and where do repos land by default?" 40)
assert_contains "$output" "folder\|parent\|nest\|subtree" \
    "repo should be represented as a folder/parent document"
assert_contains "$output" "host\|namespace\|prefix\|unique\|collide\|collision" \
    "should explain how collisions are avoided (host namespace)"

# Test 5: deterministic IDs make re-import idempotent (upsert, not duplicate)
echo "Test 5: deterministic IDs make re-import idempotent"
output=$(run_claude "In the datahub-import-docs skill, what happens if I import the same repo twice? Does it create duplicates?" 40)
assert_contains "$output" "idempotent\|upsert\|update\|in place\|no duplicate\|deterministic" \
    "re-import should upsert, not duplicate"

# Test 6: requires explicit approval before writing
echo "Test 6: requires preview/plan and explicit approval before any write"
output=$(run_claude "In the datahub-import-docs skill, does it write documents to DataHub before showing me anything? What are the steps before execution?" 40)
assert_contains "$output" "approval\|approve\|confirm\|preview\|plan" \
    "should require preview/plan + approval before writing"

# Test 7: parents are created before children
echo "Test 7: imports parents before children so hierarchy resolves"
output=$(run_claude "In the datahub-import-docs skill, in what order are documents created relative to their parent folders, and why?" 40)
assert_contains "$output" "parent\|first\|before\|order\|host folder\|top" \
    "should create parents before children"

# Test 8: runs the script with the interpreter that has the SDK (not plain python3)
echo "Test 8: uses the interpreter that has the datahub SDK, not necessarily plain python3"
output=$(run_claude "In the datahub-import-docs skill, how does it pick the Python interpreter to run the generated import script? What if 'import datahub.sdk' fails from python3?" 40)
assert_contains "$output" "interpreter\|datahub\|command -v\|readlink\|CLI\|co-located\|bundled\|which" \
    "should resolve the interpreter that ships with the datahub CLI"

# Test 9: container nodes get the Folder subtype; content subtypes are opt-in + survey-first
echo "Test 9: folder nodes get the Folder subtype; content subtypes opt-in + survey-first"
output=$(run_claude "In the datahub-import-docs skill, what subtype do the folder/container nodes get? And how does it handle content-document subtypes like Runbook or FAQ — does it ask up front or check the catalog?" 40)
assert_contains "$output" "Folder" \
    "container nodes should get the Folder subtype"
assert_contains "$output" "survey\|existing\|catalog\|reuse\|opt-in\|opt in\|not.*up front\|don't.*interrogat" \
    "content subtypes should be opt-in and survey the catalog's existing vocabulary"

echo ""
echo "=== datahub-import-docs tests complete ==="
