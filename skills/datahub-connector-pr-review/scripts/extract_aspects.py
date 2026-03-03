#!/usr/bin/env python3
"""
Extract and summarize aspects from DataHub golden files.

Supports both:
- MCP format (newer): aspectName + aspect.json at top level
- MCE format (older): proposedSnapshot with nested aspects array

Usage:
    python extract_aspects.py <golden_file.json> [--verbose]
    python extract_aspects.py <golden_file.json> --aspect schemaMetadata
    python extract_aspects.py <golden_file.json> --entity-type dataset
    python extract_aspects.py <golden_file.json> --aspect schemaMetadata --show-data --json

Examples:
    # Summary of all aspects
    python extract_aspects.py tests/integration/doris/doris_mces_golden.json

    # Check if schemaMetadata exists
    python extract_aspects.py golden.json --aspect schemaMetadata

    # Show schema fields for all datasets
    python extract_aspects.py golden.json --aspect schemaMetadata --show-data --json

    # Filter by entity type
    python extract_aspects.py golden.json --entity-type dataset
"""

import json
import sys
import argparse
from collections import defaultdict
from pathlib import Path


def extract_aspect_name_from_fqn(fqn: str) -> str:
    """
    Extract simple aspect name from fully qualified name.

    Example:
        "com.linkedin.pegasus2avro.schema.SchemaMetadata" -> "schemaMetadata"
        "com.linkedin.pegasus2avro.common.Status" -> "status"
    """
    simple_name = fqn.split(".")[-1]
    if simple_name:
        return simple_name[0].lower() + simple_name[1:]
    return simple_name


def extract_entity_type_from_snapshot_key(key: str) -> str:
    """
    Extract entity type from snapshot key.

    Example:
        "com.linkedin.pegasus2avro.metadata.snapshot.DatasetSnapshot" -> "dataset"
    """
    snapshot_types = {
        "DatasetSnapshot": "dataset",
        "ContainerSnapshot": "container",
        "ChartSnapshot": "chart",
        "DashboardSnapshot": "dashboard",
        "DataFlowSnapshot": "dataFlow",
        "DataJobSnapshot": "dataJob",
        "TagSnapshot": "tag",
        "GlossaryTermSnapshot": "glossaryTerm",
        "CorpUserSnapshot": "corpuser",
        "CorpGroupSnapshot": "corpGroup",
        "DataProcessSnapshot": "dataProcess",
        "MLModelSnapshot": "mlModel",
        "MLFeatureSnapshot": "mlFeature",
        "MLFeatureTableSnapshot": "mlFeatureTable",
        "MLPrimaryKeySnapshot": "mlPrimaryKey",
    }

    for snapshot_name, entity_type in snapshot_types.items():
        if snapshot_name in key:
            return entity_type

    # Fallback: extract from key name
    parts = key.split(".")
    if parts:
        snapshot_name = parts[-1]
        if snapshot_name.endswith("Snapshot"):
            entity = snapshot_name[:-8]
            return entity[0].lower() + entity[1:]
    return "unknown"


def parse_mcp(record: dict) -> list:
    """Parse MCP format record, return list of (entity_type, entity_urn, aspect_name, aspect_data)."""
    results = []
    entity_type = record.get("entityType", "unknown")
    entity_urn = record.get("entityUrn", "unknown")
    aspect_name = record.get("aspectName", "unknown")
    aspect_data = record.get("aspect", {}).get("json", {})

    results.append((entity_type, entity_urn, aspect_name, aspect_data))
    return results


def parse_mce(record: dict) -> list:
    """Parse MCE format record (proposedSnapshot), return list of (entity_type, entity_urn, aspect_name, aspect_data)."""
    results = []
    proposed_snapshot = record.get("proposedSnapshot", {})

    for snapshot_key, snapshot_value in proposed_snapshot.items():
        entity_type = extract_entity_type_from_snapshot_key(snapshot_key)
        entity_urn = snapshot_value.get("urn", "unknown")
        aspects = snapshot_value.get("aspects", [])

        for aspect_wrapper in aspects:
            for aspect_fqn, aspect_data in aspect_wrapper.items():
                aspect_name = extract_aspect_name_from_fqn(aspect_fqn)
                results.append((entity_type, entity_urn, aspect_name, aspect_data))

    return results


def parse_record(record: dict) -> list:
    """Parse a record, detecting format automatically."""
    if "proposedSnapshot" in record:
        return parse_mce(record)
    elif "aspectName" in record:
        return parse_mcp(record)
    else:
        return []


MAX_FILE_SIZE_MB = 100


def load_golden_file(filepath: str) -> list:
    """Load and parse golden file."""
    file_size = Path(filepath).stat().st_size
    if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise ValueError(
            f"File too large ({file_size / 1024 / 1024:.1f}MB). "
            f"Maximum allowed: {MAX_FILE_SIZE_MB}MB"
        )

    with open(filepath, "r") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data
    return [data]


def analyze_golden_file(filepath: str) -> dict:
    """
    Analyze a golden file and return structured summary.
    Used by gather-connector-context.sh for quick analysis.
    """
    records = load_golden_file(filepath)

    all_aspects = []
    for record in records:
        all_aspects.extend(parse_record(record))

    # Summarize
    entity_counts = defaultdict(int)
    aspect_counts = defaultdict(lambda: defaultdict(int))
    urns_by_type = defaultdict(set)

    for entity_type, entity_urn, aspect_name, aspect_data in all_aspects:
        entity_counts[entity_type] += 1
        aspect_counts[entity_type][aspect_name] += 1
        urns_by_type[entity_type].add(entity_urn)

    return {
        "total_records": len(all_aspects),
        "unique_entities": sum(len(urns) for urns in urns_by_type.values()),
        "entity_counts": dict(entity_counts),
        "aspect_counts": {k: dict(v) for k, v in aspect_counts.items()},
        "urns_by_type": {k: list(v) for k, v in urns_by_type.items()},
    }


def print_summary(filepath: str, analysis: dict):
    """Print human-readable summary."""
    print(f"\n{'=' * 60}")
    print(f"Golden File: {Path(filepath).name}")
    print(f"{'=' * 60}")

    print(f"\nTotal records parsed: {analysis['total_records']}")
    print(f"Unique entities: {analysis['unique_entities']}")

    print(f"\n{'─' * 60}")
    print("ENTITY TYPES:")
    print(f"{'─' * 60}")
    for entity_type in sorted(analysis["entity_counts"].keys()):
        unique_urns = len(analysis["urns_by_type"].get(entity_type, []))
        total_aspects = analysis["entity_counts"][entity_type]
        print(f"  {entity_type}: {unique_urns} entities, {total_aspects} aspects")

    print(f"\n{'─' * 60}")
    print("ASPECTS BY ENTITY TYPE:")
    print(f"{'─' * 60}")
    for entity_type in sorted(analysis["aspect_counts"].keys()):
        print(f"\n  [{entity_type}]")
        for aspect_name in sorted(analysis["aspect_counts"][entity_type].keys()):
            count = analysis["aspect_counts"][entity_type][aspect_name]
            print(f"    - {aspect_name}: {count}")

    # Checklist for datasets
    print(f"\n{'─' * 60}")
    print("ASPECT CHECKLIST (datasets):")
    print(f"{'─' * 60}")
    dataset_aspects = analysis["aspect_counts"].get("dataset", {})
    checklist = [
        ("schemaMetadata", "Column definitions"),
        ("datasetProperties", "Name, description, custom props"),
        ("status", "Removed flag"),
        ("container", "Parent container"),
        ("subTypes", "Table/View subtype"),
        ("browsePathsV2", "Browse paths"),
        ("upstreamLineage", "Lineage information"),
        ("viewProperties", "View definition (for views)"),
    ]

    for aspect, description in checklist:
        status = "✓" if aspect in dataset_aspects else "✗"
        count = dataset_aspects.get(aspect, 0)
        print(f"  [{status}] {aspect}: {count} ({description})")


def main():
    parser = argparse.ArgumentParser(
        description="Extract aspects from DataHub golden files (supports both MCP and MCE formats)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s golden.json                          # Summary of all aspects
  %(prog)s golden.json --aspect schemaMetadata  # Check if schemaMetadata exists
  %(prog)s golden.json -a schemaMetadata -d -j  # Show schema data as JSON
  %(prog)s golden.json -e dataset               # Filter by entity type
  %(prog)s golden.json --summary-json           # Machine-readable summary
        """,
    )
    parser.add_argument("golden_file", help="Path to golden file (JSON)")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed output"
    )
    parser.add_argument("--aspect", "-a", help="Filter by aspect name")
    parser.add_argument("--entity-type", "-e", help="Filter by entity type")
    parser.add_argument(
        "--show-data", "-d", action="store_true", help="Show aspect data"
    )
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    parser.add_argument("--urn", "-u", help="Filter by entity URN (substring match)")
    parser.add_argument(
        "--summary-json",
        action="store_true",
        help="Output summary as JSON (for scripts)",
    )

    args = parser.parse_args()

    # Load golden file
    try:
        records = load_golden_file(args.golden_file)
    except FileNotFoundError:
        print(f"Error: File not found: {args.golden_file}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {args.golden_file}: {e}", file=sys.stderr)
        sys.exit(1)

    # Quick summary mode for scripts
    if args.summary_json:
        analysis = analyze_golden_file(args.golden_file)
        print(json.dumps(analysis, indent=2))
        return

    # Parse all records
    all_aspects = []
    for record in records:
        all_aspects.extend(parse_record(record))

    # Filter if requested
    if args.aspect:
        all_aspects = [
            (et, eu, an, ad)
            for et, eu, an, ad in all_aspects
            if an.lower() == args.aspect.lower()
        ]

    if args.entity_type:
        all_aspects = [
            (et, eu, an, ad)
            for et, eu, an, ad in all_aspects
            if et.lower() == args.entity_type.lower()
        ]

    if args.urn:
        all_aspects = [
            (et, eu, an, ad)
            for et, eu, an, ad in all_aspects
            if args.urn.lower() in eu.lower()
        ]

    if args.json:
        # Output as JSON
        output = []
        for entity_type, entity_urn, aspect_name, aspect_data in all_aspects:
            output.append(
                {
                    "entityType": entity_type,
                    "entityUrn": entity_urn,
                    "aspectName": aspect_name,
                    "aspectData": aspect_data if args.show_data else "<omitted>",
                }
            )
        print(json.dumps(output, indent=2))
        return

    # Standard summary output
    analysis = analyze_golden_file(args.golden_file)
    print_summary(args.golden_file, analysis)

    # Verbose/detailed output
    if args.verbose or args.show_data:
        print(f"\n{'─' * 60}")
        print("DETAILED ASPECTS:")
        print(f"{'─' * 60}")
        for entity_type, entity_urn, aspect_name, aspect_data in all_aspects:
            print(f"\n  Entity: {entity_urn}")
            print(f"  Type: {entity_type}")
            print(f"  Aspect: {aspect_name}")
            if args.show_data:
                print(f"  Data: {json.dumps(aspect_data, indent=4)}")


if __name__ == "__main__":
    main()
