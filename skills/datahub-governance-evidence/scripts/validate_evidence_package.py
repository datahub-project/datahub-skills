#!/usr/bin/env python3
"""Validate scoreless governance-evidence JSON and Markdown reconciliation."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

STATES = {"Observed", "Not observed", "Unable to determine"}
FORBIDDEN_KEYS = {
    "compliant",
    "control_status",
    "fail",
    "grade",
    "pass",
    "readiness",
    "score",
}
FRAMEWORK_FIELDS = {
    "authoritative_source",
    "evidence_relevance",
    "framework",
    "limitations",
    "objective_id",
    "relevant_signals",
    "review_focus",
    "signal_breakdown",
    "source_surfaces",
}
REQUIRED_TOP_LEVEL_FIELDS = {
    "assets",
    "collection",
    "collection_errors",
    "disclaimer",
    "follow_up_candidates",
    "framework_alignment",
    "limitations",
    "schema_version",
    "summary",
}


def keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        return set(value) | set().union(*(keys(item) for item in value.values()))
    if isinstance(value, list):
        return set().union(*(keys(item) for item in value), set())
    return set()


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def validate(package: dict[str, Any], markdown: str) -> list[str]:
    errors: list[str] = []
    missing_top_level = REQUIRED_TOP_LEVEL_FIELDS - set(package)
    require(
        not missing_top_level,
        f"required top-level fields missing: {sorted(missing_top_level)}",
        errors,
    )
    require(
        package.get("schema_version") == "1.0",
        "unsupported schema version",
        errors,
    )
    require(
        isinstance(package.get("collection"), dict),
        "collection must be an object",
        errors,
    )
    for field in (
        "assets",
        "collection_errors",
        "follow_up_candidates",
        "framework_alignment",
        "limitations",
        "summary",
    ):
        require(
            isinstance(package.get(field), list), f"{field} must be an array", errors
        )

    assets = package.get("assets") if isinstance(package.get("assets"), list) else []
    require(
        all(isinstance(asset, dict) for asset in assets),
        "every asset must be an object",
        errors,
    )
    assets = [asset for asset in assets if isinstance(asset, dict)]
    asset_urns = [asset.get("urn") for asset in assets]
    boundary = set(asset_urns)
    require(None not in boundary, "every asset must have a URN", errors)
    require(len(boundary) == len(asset_urns), "asset URNs must be unique", errors)
    require(
        not (keys(package) & FORBIDDEN_KEYS), "forbidden result field present", errors
    )

    observations: dict[tuple[str, str], dict[str, Any]] = {}
    for asset in assets:
        urn = asset.get("urn")
        asset_observations = asset.get("observations")
        require(
            isinstance(asset_observations, list),
            f"observations must be an array: {urn}",
            errors,
        )
        for item in asset_observations if isinstance(asset_observations, list) else []:
            if not isinstance(item, dict):
                errors.append(f"observation must be an object: {urn}")
                continue
            signal = item.get("signal")
            state = item.get("state")
            require(
                isinstance(signal, str) and bool(signal.strip()),
                f"observation signal must be a non-empty string: {urn}",
                errors,
            )
            require(
                state in STATES, f"invalid state for {urn}/{signal}: {state}", errors
            )
            key = (urn, signal)
            require(
                key not in observations,
                f"duplicate observation: {urn}/{signal}",
                errors,
            )
            observations[key] = item

    summaries = (
        package.get("summary") if isinstance(package.get("summary"), list) else []
    )
    require(
        all(isinstance(item, dict) for item in summaries),
        "every summary must be an object",
        errors,
    )
    summaries = [item for item in summaries if isinstance(item, dict)]
    summary_by_signal = {item.get("signal"): item for item in summaries}
    require(
        len(summary_by_signal) == len(summaries),
        "summary signals must be unique",
        errors,
    )
    require(
        all(isinstance(signal, str) and signal.strip() for signal in summary_by_signal),
        "summary signals must be non-empty strings",
        errors,
    )
    for signal, item in summary_by_signal.items():
        sets = {
            "observed": set(item.get("observed_urns") or []),
            "not_observed": set(item.get("not_observed_urns") or []),
            "unable": set(item.get("unable_urns") or []),
        }
        counts = item.get("counts") or {}
        require(
            item.get("selected_assets") == len(boundary),
            f"wrong denominator: {signal}",
            errors,
        )
        require(
            all(counts.get(name) == len(values) for name, values in sets.items()),
            f"count/set mismatch: {signal}",
            errors,
        )
        require(
            sum(counts.get(name, -1) for name in sets) == len(boundary),
            f"counts do not reconcile: {signal}",
            errors,
        )
        require(
            not (
                sets["observed"] & sets["not_observed"]
                or sets["observed"] & sets["unable"]
                or sets["not_observed"] & sets["unable"]
            ),
            f"state sets overlap: {signal}",
            errors,
        )
        require(
            set().union(*sets.values()) == boundary,
            f"state sets do not cover boundary: {signal}",
            errors,
        )
        for name, state in (
            ("observed", "Observed"),
            ("not_observed", "Not observed"),
            ("unable", "Unable to determine"),
        ):
            actual = {
                urn
                for urn in boundary
                if observations.get((urn, signal), {}).get("state") == state
            }
            require(
                actual == sets[name],
                f"asset/summary mismatch: {signal}/{state}",
                errors,
            )
            expected_percentage = (
                round(len(actual) / len(boundary) * 100, 1) if boundary else 0.0
            )
            actual_percentage = (item.get("percentages") or {}).get(name)
            require(
                isinstance(actual_percentage, (int, float))
                and math.isclose(actual_percentage, expected_percentage, abs_tol=0.05),
                f"percentage mismatch: {signal}/{state}",
                errors,
            )

    observation_signals = {
        signal for _, signal in observations if isinstance(signal, str)
    }
    require(
        not boundary or observation_signals == set(summary_by_signal),
        "asset observation signals and summary signals must match",
        errors,
    )

    alignments = (
        package.get("framework_alignment")
        if isinstance(package.get("framework_alignment"), list)
        else []
    )
    for alignment in alignments:
        if not isinstance(alignment, dict):
            errors.append("framework alignment must be an object")
            continue
        missing = FRAMEWORK_FIELDS - set(alignment)
        require(not missing, f"framework fields missing: {sorted(missing)}", errors)
        source = alignment.get("authoritative_source", "")
        parsed_source = urlparse(source) if isinstance(source, str) else None
        require(
            bool(
                parsed_source
                and parsed_source.scheme == "https"
                and parsed_source.netloc
            ),
            "framework source must be an absolute HTTPS URL",
            errors,
        )
        relevant = alignment.get("relevant_signals") or []
        parts = alignment.get("signal_breakdown") or []
        require(
            all(signal in summary_by_signal for signal in relevant),
            "framework references an uncollected signal",
            errors,
        )
        require(
            [part.get("signal") for part in parts] == relevant,
            "framework signal order mismatch",
            errors,
        )
        for part in parts:
            signal = part.get("signal")
            summary = summary_by_signal.get(signal) or {}
            for name in ("observed", "not_observed", "unable"):
                require(
                    (part.get("counts") or {}).get(name)
                    == (summary.get("counts") or {}).get(name),
                    f"framework count mismatch: {signal}/{name}",
                    errors,
                )
                require(
                    set(part.get(f"{name}_urns") or [])
                    == set(summary.get(f"{name}_urns") or []),
                    f"framework URN mismatch: {signal}/{name}",
                    errors,
                )

        objective_id = alignment.get("objective_id")
        require(
            isinstance(objective_id, str) and objective_id in markdown,
            "Markdown omits a framework objective identifier",
            errors,
        )
        require(
            isinstance(source, str) and source in markdown,
            "Markdown omits a framework authoritative source",
            errors,
        )

    disclaimer = package.get("disclaimer")
    require(
        isinstance(disclaimer, str) and disclaimer in markdown,
        "Markdown disclaimer mismatch",
        errors,
    )
    require(
        all(urn in markdown for urn in boundary),
        "Markdown omits one or more exact URNs",
        errors,
    )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("json_package", type=Path)
    parser.add_argument("markdown_package", type=Path)
    args = parser.parse_args()
    package = json.loads(args.json_package.read_text(encoding="utf-8"))
    markdown = args.markdown_package.read_text(encoding="utf-8")
    errors = (
        validate(package, markdown)
        if isinstance(package, dict)
        else ["JSON package root must be an object"]
    )
    print(
        json.dumps(
            {"status": "failed" if errors else "passed", "errors": errors}, indent=2
        )
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
