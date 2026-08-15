#!/usr/bin/env python3
"""Offline regression tests for the governance-evidence package validator."""

from __future__ import annotations

import copy
import unittest

from validate_evidence_package import validate

DISCLAIMER = (
    "This package summarizes catalog-visible metadata only. It is supporting "
    "evidence, not an audit, attestation, certification, legal opinion, or "
    "compliance determination."
)
URN = "urn:li:dataset:(urn:li:dataPlatform:snowflake,db.schema.table,PROD)"


def valid_package() -> dict:
    return {
        "schema_version": "1.0",
        "disclaimer": DISCLAIMER,
        "collection": {"complete": True},
        "assets": [
            {
                "urn": URN,
                "name": "table",
                "observations": [
                    {
                        "signal": "ownership",
                        "state": "Observed",
                        "source_surfaces": ["ownership"],
                        "supporting_metadata": ["urn:li:corpuser:owner"],
                        "error": None,
                    }
                ],
            }
        ],
        "summary": [
            {
                "signal": "ownership",
                "selected_assets": 1,
                "counts": {"observed": 1, "not_observed": 0, "unable": 0},
                "percentages": {
                    "observed": 100.0,
                    "not_observed": 0.0,
                    "unable": 0.0,
                },
                "observed_urns": [URN],
                "not_observed_urns": [],
                "unable_urns": [],
            }
        ],
        "framework_alignment": [],
        "collection_errors": [],
        "limitations": [],
        "follow_up_candidates": [],
    }


def valid_markdown() -> str:
    return f"# Evidence\n\n{DISCLAIMER}\n\n{URN}\n"


class ValidateEvidencePackageTests(unittest.TestCase):
    def test_valid_package_passes(self) -> None:
        self.assertEqual(validate(valid_package(), valid_markdown()), [])

    def test_required_top_level_fields_cannot_be_omitted(self) -> None:
        for field in (
            "assets",
            "collection",
            "collection_errors",
            "disclaimer",
            "follow_up_candidates",
            "framework_alignment",
            "limitations",
            "schema_version",
            "summary",
        ):
            with self.subTest(field=field):
                package = valid_package()
                package.pop(field)
                self.assertTrue(validate(package, valid_markdown()))

    def test_summary_and_asset_signal_sets_must_match(self) -> None:
        package = valid_package()
        package["summary"] = []
        errors = validate(package, valid_markdown())
        self.assertIn(
            "asset observation signals and summary signals must match",
            errors,
        )

    def test_empty_boundary_can_retain_requested_signal_summary(self) -> None:
        package = valid_package()
        package["assets"] = []
        summary = package["summary"][0]
        summary["selected_assets"] = 0
        summary["counts"] = {"observed": 0, "not_observed": 0, "unable": 0}
        summary["percentages"] = {
            "observed": 0.0,
            "not_observed": 0.0,
            "unable": 0.0,
        }
        summary["observed_urns"] = []
        markdown = f"# Evidence\n\n{DISCLAIMER}\n"
        self.assertEqual(validate(package, markdown), [])

    def test_framework_cannot_reference_an_uncollected_signal(self) -> None:
        package = valid_package()
        package["framework_alignment"] = [
            {
                "framework": "SOC 2",
                "objective_id": "CC2.1",
                "review_focus": "Catalog information supporting review",
                "relevant_signals": ["lineage"],
                "source_surfaces": ["upstreamLineage"],
                "signal_breakdown": [
                    {
                        "signal": "lineage",
                        "counts": {
                            "observed": 0,
                            "not_observed": 0,
                            "unable": 0,
                        },
                        "observed_urns": [],
                        "not_observed_urns": [],
                        "unable_urns": [],
                    }
                ],
                "evidence_relevance": "Registered relationships support review.",
                "limitations": "Does not establish completeness.",
                "authoritative_source": "https://example.com/soc2",
            }
        ]
        markdown = f"{valid_markdown()}\nCC2.1\nhttps://example.com/soc2\n"
        errors = validate(package, markdown)
        self.assertIn("framework references an uncollected signal", errors)

    def test_framework_source_requires_an_absolute_https_url(self) -> None:
        package = valid_package()
        alignment = {
            "framework": "SOC 2",
            "objective_id": "CC2.1",
            "review_focus": "Catalog information supporting review",
            "relevant_signals": ["ownership"],
            "source_surfaces": ["ownership"],
            "signal_breakdown": [copy.deepcopy(package["summary"][0])],
            "evidence_relevance": "Assigned owners support review.",
            "limitations": "Does not establish accountability.",
            "authoritative_source": "https://",
        }
        alignment["signal_breakdown"][0].pop("selected_assets")
        alignment["signal_breakdown"][0].pop("percentages")
        package["framework_alignment"] = [alignment]
        markdown = f"{valid_markdown()}\nCC2.1\nhttps://\n"
        errors = validate(package, markdown)
        self.assertIn("framework source must be an absolute HTTPS URL", errors)

    def test_forbidden_result_fields_fail_at_any_depth(self) -> None:
        package = valid_package()
        package["assets"][0]["score"] = 100
        self.assertIn(
            "forbidden result field present",
            validate(package, valid_markdown()),
        )


if __name__ == "__main__":
    unittest.main()
