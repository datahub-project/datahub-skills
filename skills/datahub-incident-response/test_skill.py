"""Validate datahub-incident-response skill assets."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = Path(__file__).resolve().parent
SKILL_MD = SKILL_DIR / "SKILL.md"


def test_skill_frontmatter() -> None:
    text = SKILL_MD.read_text(encoding="utf-8")
    assert text.lstrip().startswith("---")
    for key in ("name", "description"):
        assert re.search(rf"(?m)^{key}\s*:", text), f"missing frontmatter key: {key}"
    assert "triggers on:" in text.lower() or "trigger" in text.lower()


def test_skill_references_datahub_capabilities() -> None:
    low = SKILL_MD.read_text(encoding="utf-8").lower()
    for cap in ("lineage", "incident", "context document"):
        assert cap in low, f"skill missing capability reference: {cap}"


def test_example_paths_exist() -> None:
    examples_dir = SKILL_DIR / "examples"
    assert examples_dir.is_dir()
    md_files = list(examples_dir.glob("*.md"))
    assert len(md_files) >= 2

    for md in md_files:
        content = md.read_text(encoding="utf-8")
        for match in re.findall(r"\[`[^`]+`\]\(([^)]+)\)", content):
            if match.startswith("http"):
                continue
            rel = (md.parent / match).resolve()
            if "../../examples/" in match:
                target = (REPO_ROOT / match.split("../../", 1)[1]).resolve()
                assert target.exists(), f"missing referenced path: {match}"
