#!/usr/bin/env python3
"""Validate the internal consistency of an ML release-audit evidence bundle."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

VERDICTS = {
    "insufficient_metadata",
    "needs_review",
    "high_confidence",
    "confirmed",
    "clear_for_release",
}


def validate(bundle: dict[str, Any]) -> list[str]:
    """Return human-readable consistency errors; an empty list means valid."""
    errors: list[str] = []
    verdict = bundle.get("verdict")
    if verdict not in VERDICTS:
        errors.append(f"verdict must be one of: {', '.join(sorted(VERDICTS))}")
    if not isinstance(bundle.get("model_urn"), str) or not bundle["model_urn"].strip():
        errors.append("model_urn must be a non-empty string")

    directional = bundle.get("directional_outcome_lineage") is True
    violation = bundle.get("availability_violation") is True
    deterministic = bundle.get("deterministic_cutoff_proof") is True
    point_in_time = bundle.get("point_in_time", {})
    safe_control = bundle.get("safe_control", {})

    if verdict in {"high_confidence", "confirmed", "clear_for_release"}:
        prediction_time = bundle.get("prediction_time")
        if not isinstance(prediction_time, str) or not prediction_time.strip():
            errors.append(f"{verdict} requires prediction_time")
    if verdict in {"high_confidence", "confirmed"} and not (directional and violation):
        errors.append(
            f"{verdict} requires directional lineage and an availability violation"
        )
    if deterministic and not (directional and violation):
        errors.append(
            "deterministic proof requires directional lineage and an availability violation"
        )

    pit_confirmed = False
    if isinstance(point_in_time, dict) and point_in_time.get("performed") is True:
        retained = point_in_time.get("advantage_retained")
        threshold = point_in_time.get("collapse_threshold")
        if not _unit_number(retained) or not _unit_number(threshold):
            errors.append(
                "point-in-time retained advantage and threshold must be numbers from 0 to 1"
            )
        else:
            pit_confirmed = retained <= threshold

    if verdict == "confirmed" and not (deterministic or pit_confirmed):
        errors.append(
            "confirmed requires deterministic proof or policy-qualified PIT collapse"
        )
    if pit_confirmed and not (directional and violation):
        errors.append(
            "PIT collapse cannot confirm without directional lineage and a time violation"
        )
    if verdict == "clear_for_release":
        if violation:
            errors.append("clear_for_release cannot contain an availability violation")
        safe = (
            isinstance(safe_control, dict)
            and safe_control.get("performed") is True
            and safe_control.get("remained_safe") is True
        )
        if not safe:
            errors.append(
                "clear_for_release requires a predictive safe control that remained safe"
            )
    return errors


def _unit_number(value: Any) -> bool:
    return (
        isinstance(value, int | float)
        and not isinstance(value, bool)
        and 0 <= value <= 1
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path, help="JSON evidence bundle")
    args = parser.parse_args()
    try:
        data = json.loads(args.evidence.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"INVALID: {exc}")
        return 2
    if not isinstance(data, dict):
        print("INVALID: top-level JSON value must be an object")
        return 2
    errors = validate(data)
    if errors:
        for error in errors:
            print(f"INVALID: {error}")
        return 1
    print("VALID: evidence bundle is internally consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
