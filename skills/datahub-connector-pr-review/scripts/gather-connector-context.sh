#!/bin/bash
# Gather Connector Context Script
# Consolidates multiple grep/find commands to gather connector information
# Used by PR review skill to quickly understand a connector's structure

set -e

usage() {
    cat << EOF
Usage: $0 <connector_name> [datahub_repo_path]

Gathers comprehensive context about a DataHub connector for review.

Arguments:
  connector_name    Name of the connector (e.g., snowflake, postgres, snowplow)
  datahub_repo_path Path to DataHub repo (default: current directory)

Output:
  - File structure
  - Base class identification
  - Import dependencies
  - Test locations
  - Config structure

Examples:
  $0 snowflake
  $0 snowplow /path/to/datahub

EOF
    exit 1
}

CONNECTOR="${1:-}"
REPO_PATH="${2:-.}"

if [[ -z "$CONNECTOR" ]]; then
    echo "Error: Connector name is required" >&2
    usage
fi

# Input validation: reject path traversal and shell metacharacters
if [[ "$CONNECTOR" =~ [/\\.\$\`\;\|\&\>\<\!\(\)\{\}\[\]\'\"] ]] || [[ "$CONNECTOR" == *..* ]]; then
    echo "Error: Invalid connector name. Use only alphanumeric characters, hyphens, and underscores." >&2
    exit 1
fi

# Validate connector name is a simple identifier
if ! [[ "$CONNECTOR" =~ ^[a-zA-Z0-9_-]+$ ]]; then
    echo "Error: Connector name must contain only alphanumeric characters, hyphens, and underscores." >&2
    exit 1
fi

# Validate repo path exists
if [[ ! -d "$REPO_PATH" ]]; then
    echo "Error: Repository path does not exist: $REPO_PATH" >&2
    exit 1
fi

SOURCE_BASE="$REPO_PATH/metadata-ingestion/src/datahub/ingestion/source"
SOURCE_DIR="$SOURCE_BASE/$CONNECTOR"
SOURCE_FILE="$SOURCE_BASE/${CONNECTOR}.py"
TESTS_UNIT="$REPO_PATH/metadata-ingestion/tests/unit"
TESTS_INTEGRATION="$REPO_PATH/metadata-ingestion/tests/integration/$CONNECTOR"
DOCS_DIR="$REPO_PATH/docs/sources/$CONNECTOR"

# Determine source type: directory or single file
IS_SINGLE_FILE=false
SOURCE_FILES=()

echo "═══════════════════════════════════════════════════════════════"
echo "  Connector Context: $CONNECTOR"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Check if connector exists (directory or single file)
if [[ -d "$SOURCE_DIR" ]]; then
    echo "📍 Source type: Directory-based connector"
    mapfile -t SOURCE_FILES < <(find "$SOURCE_DIR" -name "*.py" -type f 2>/dev/null)
elif [[ -f "$SOURCE_FILE" ]]; then
    echo "📍 Source type: Single-file connector"
    IS_SINGLE_FILE=true
    SOURCE_DIR="$SOURCE_BASE"
    SOURCE_FILES=("$SOURCE_FILE")
else
    echo "⚠️  Connector not found at default locations, searching..."

    # Try to find directory with connector name
    FOUND=$(find "$SOURCE_BASE" -type d -name "$CONNECTOR" 2>/dev/null | head -1)
    if [[ -n "$FOUND" ]]; then
        echo "📍 Found directory: $FOUND"
        SOURCE_DIR="$FOUND"
        mapfile -t SOURCE_FILES < <(find "$SOURCE_DIR" -name "*.py" -type f 2>/dev/null)
    else
        # Try to find single file anywhere in source tree (e.g., sql/duckdb.py)
        FOUND=$(find "$SOURCE_BASE" -type f -name "${CONNECTOR}.py" 2>/dev/null | head -1)
        if [[ -n "$FOUND" ]]; then
            echo "📍 Found file: $FOUND"
            IS_SINGLE_FILE=true
            SOURCE_FILE="$FOUND"
            SOURCE_DIR="$(dirname "$FOUND")"
            SOURCE_FILES=("$SOURCE_FILE")
        else
            # Try partial match
            FOUND=$(find "$SOURCE_BASE" -type f -name "*${CONNECTOR}*.py" 2>/dev/null | head -1)
            if [[ -n "$FOUND" ]]; then
                echo "📍 Found file (partial match): $FOUND"
                IS_SINGLE_FILE=true
                SOURCE_FILE="$FOUND"
                SOURCE_DIR="$(dirname "$FOUND")"
                SOURCE_FILES=("$SOURCE_FILE")
            else
                echo "   Connector not found in source directory"
                exit 1
            fi
        fi
    fi
fi
echo ""

echo "📁 FILE STRUCTURE"
echo "─────────────────────────────────────────────────────────────────"
if [[ ${#SOURCE_FILES[@]} -gt 0 ]]; then
    for file in "${SOURCE_FILES[@]}"; do
        if [[ -f "$file" ]]; then
            lines=$(wc -l < "$file" | tr -d ' ')
            echo "  $(basename "$file") ($lines lines)"
        fi
    done | sort
else
    echo "  (no source files found)"
fi
echo ""

echo "🏗️  BASE CLASS & INHERITANCE"
echo "─────────────────────────────────────────────────────────────────"
if [[ ${#SOURCE_FILES[@]} -gt 0 ]]; then
    grep -h "class.*Source.*:" "${SOURCE_FILES[@]}" 2>/dev/null | head -5 || echo "  (no source classes found)"
    echo ""
    echo "  Inheritance chain:"
    grep -h "from datahub.ingestion.source" "${SOURCE_FILES[@]}" 2>/dev/null | sort -u | sed 's/^/    /' || echo "    (none found)"
else
    echo "  (no source files found)"
fi
echo ""

echo "📦 KEY IMPORTS"
echo "─────────────────────────────────────────────────────────────────"
if [[ ${#SOURCE_FILES[@]} -gt 0 ]]; then
    # DataHub imports
    echo "  DataHub SDK:"
    grep -h "^from datahub\|^import datahub" "${SOURCE_FILES[@]}" 2>/dev/null | sort -u | head -10 | sed 's/^/    /' || echo "    (none)"

    echo ""
    echo "  External libraries:"
    grep -h "^from \|^import " "${SOURCE_FILES[@]}" 2>/dev/null | grep -v "^from datahub\|^import datahub\|^from \.\|^from typing" | sort -u | head -10 | sed 's/^/    /' || echo "    (none)"
else
    echo "  (no source files found)"
fi
echo ""

echo "⚙️  CONFIG STRUCTURE"
echo "─────────────────────────────────────────────────────────────────"
if [[ ${#SOURCE_FILES[@]} -gt 0 ]]; then
    # Find config classes
    grep -h "class.*Config.*:" "${SOURCE_FILES[@]}" 2>/dev/null | head -5 || echo "  (no config classes found)"

    # Find config fields
    echo ""
    echo "  Config fields (sample):"
    grep -h ":\s*\(str\|int\|bool\|Optional\|List\|Dict\)" "${SOURCE_FILES[@]}" 2>/dev/null | grep -v "def \|#" | head -10 | sed 's/^/    /' || echo "    (none found)"
else
    echo "  (no source files found)"
fi
echo ""

echo "🧪 TEST LOCATIONS"
echo "─────────────────────────────────────────────────────────────────"
echo "  Unit tests:"
UNIT_TESTS=$(find "$TESTS_UNIT" -path "*$CONNECTOR*" -name "*.py" 2>/dev/null | wc -l | tr -d ' ')
if [[ "$UNIT_TESTS" -gt 0 ]]; then
    find "$TESTS_UNIT" -path "*$CONNECTOR*" -name "*.py" 2>/dev/null | head -5 | sed 's/^/    /'
    [[ "$UNIT_TESTS" -gt 5 ]] && echo "    ... and $((UNIT_TESTS - 5)) more"
else
    echo "    (none found)"
fi

echo ""
echo "  Integration tests:"
if [[ -d "$TESTS_INTEGRATION" ]]; then
    find "$TESTS_INTEGRATION" -name "*.py" -o -name "*.yml" -o -name "*.json" 2>/dev/null | head -10 | sed 's/^/    /'
else
    echo "    (directory not found: $TESTS_INTEGRATION)"
fi

echo ""
echo "  Golden files:"
GOLDEN_FILES=$(find "$TESTS_INTEGRATION" -name "*golden*.json" 2>/dev/null)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXTRACT_SCRIPT="$SCRIPT_DIR/extract_aspects.py"

if [[ -n "$GOLDEN_FILES" ]]; then
    echo "$GOLDEN_FILES" | while read -r gf; do
        if [[ -f "$gf" ]]; then
            size=$(ls -lh "$gf" | awk '{print $5}')
            lines=$(wc -l < "$gf" | tr -d ' ')
            echo "    $(basename "$gf") - $size, $lines lines"
        fi
    done
else
    echo "    (none found)"
fi
echo ""

# Detailed golden file analysis using extract_aspects.py
if [[ -n "$GOLDEN_FILES" && -f "$EXTRACT_SCRIPT" ]]; then
    echo "📊 GOLDEN FILE ANALYSIS"
    echo "─────────────────────────────────────────────────────────────────"
    echo "$GOLDEN_FILES" | while read -r gf; do
        if [[ -f "$gf" ]]; then
            echo ""
            echo "  File: $(basename "$gf")"
            # Get summary as JSON and format key info
            SUMMARY=$(python3 "$EXTRACT_SCRIPT" "$gf" --summary-json 2>/dev/null)
            if [[ -n "$SUMMARY" ]]; then
                TOTAL=$(echo "$SUMMARY" | python3 -c "import sys,json; print(json.load(sys.stdin).get('total_records', 0))" 2>/dev/null)
                ENTITIES=$(echo "$SUMMARY" | python3 -c "import sys,json; print(json.load(sys.stdin).get('unique_entities', 0))" 2>/dev/null)
                echo "    Total aspects: $TOTAL, Unique entities: $ENTITIES"

                # Show entity breakdown
                echo "    Entities:"
                echo "$SUMMARY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for etype, count in sorted(data.get('entity_counts', {}).items()):
    urns = len(data.get('urns_by_type', {}).get(etype, []))
    print(f'      {etype}: {urns} entities')
" 2>/dev/null

                # Show dataset aspects checklist
                echo "    Dataset aspects:"
                echo "$SUMMARY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
aspects = data.get('aspect_counts', {}).get('dataset', {})
checklist = ['schemaMetadata', 'datasetProperties', 'container', 'subTypes', 'upstreamLineage', 'viewProperties']
for aspect in checklist:
    status = '✓' if aspect in aspects else '✗'
    count = aspects.get(aspect, 0)
    print(f'      [{status}] {aspect}: {count}')
" 2>/dev/null
            else
                echo "    (analysis failed)"
            fi
        fi
    done
    echo ""
fi

echo "📚 DOCUMENTATION"
echo "─────────────────────────────────────────────────────────────────"
if [[ -d "$DOCS_DIR" ]]; then
    find "$DOCS_DIR" -name "*.md" 2>/dev/null | sed 's/^/    /' || echo "    (no docs found)"
else
    echo "    (directory not found: $DOCS_DIR)"
fi
echo ""

echo "🔗 LINEAGE IMPLEMENTATION"
echo "─────────────────────────────────────────────────────────────────"
if [[ ${#SOURCE_FILES[@]} -gt 0 ]]; then
    if grep -q "SqlParsingAggregator\|upstreamLineage\|UpstreamLineage" "${SOURCE_FILES[@]}" 2>/dev/null; then
        echo "  ✅ Lineage implementation detected"
        grep -h "SqlParsingAggregator\|upstreamLineage" "${SOURCE_FILES[@]}" 2>/dev/null | head -3 | sed 's/^/    /'
    else
        echo "  ⚠️  No lineage implementation found"
    fi
else
    echo "  (no source files found)"
fi
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo "  Context gathering complete"
echo "═══════════════════════════════════════════════════════════════"
