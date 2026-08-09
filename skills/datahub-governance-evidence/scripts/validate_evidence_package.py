#!/usr/bin/env python3
"""Validate scoreless governance-evidence JSON and Markdown reconciliation."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

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
    assets = package.get("assets") or []
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
        for item in asset.get("observations") or []:
            signal = item.get("signal")
            state = item.get("state")
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

    summaries = package.get("summary") or []
    summary_by_signal = {item.get("signal"): item for item in summaries}
    require(
        len(summary_by_signal) == len(summaries),
        "summary signals must be unique",
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

    for alignment in package.get("framework_alignment") or []:
        missing = FRAMEWORK_FIELDS - set(alignment)
        require(not missing, f"framework fields missing: {sorted(missing)}", errors)
        require(
            str(alignment.get("authoritative_source", "")).startswith("https://"),
            "framework source must be HTTPS",
            errors,
        )
        relevant = alignment.get("relevant_signals") or []
        parts = alignment.get("signal_breakdown") or []
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
    errors = validate(package, markdown)
    print(
        json.dumps(
            {"status": "failed" if errors else "passed", "errors": errors}, indent=2
        )
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
