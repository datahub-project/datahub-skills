#!/usr/bin/env python3
"""Validate DataHub skill names and cross-skill references.

This dependency-free repository integrity check verifies that:
- every skills/*/SKILL.md frontmatter name matches its directory;
- slash references such as /datahub-search resolve to an existing skill;
- Skill-tool references such as datahub-skills:datahub-search resolve;
- known unresolved references are explicitly tracked in a baseline; and
- baseline entries are removed once they become resolved.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"
BASELINE_PATH = ROOT / ".skill-reference-baseline.txt"

FRONTMATTER_NAME_RE = re.compile(r"(?m)^name:\s*([a-z0-9-]+)\s*$")
SLASH_REF_RE = re.compile(r"(?<![\w/])/(datahub-[a-z0-9-]+)\b")
SKILL_TOOL_REF_RE = re.compile(r"datahub-skills:(datahub-[a-z0-9-]+)\b")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_skills() -> tuple[set[str], list[str]]:
    skills: set[str] = set()
    errors: list[str] = []

    for skill_file in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        text = read_text(skill_file)
        match = FRONTMATTER_NAME_RE.search(text)
        rel = skill_file.relative_to(ROOT)
        if not match:
            errors.append(f"{rel}: missing lowercase frontmatter name")
            continue

        name = match.group(1)
        directory_name = skill_file.parent.name
        if name != directory_name:
            errors.append(
                f"{rel}: frontmatter name {name!r} does not match "
                f"directory {directory_name!r}"
            )
        if name in skills:
            errors.append(f"{rel}: duplicate skill name {name!r}")
        skills.add(name)

    return skills, errors


def load_baseline() -> set[str]:
    if not BASELINE_PATH.exists():
        return set()

    entries: set[str] = set()
    for raw_line in read_text(BASELINE_PATH).splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if line:
            entries.add(line)
    return entries


def markdown_files() -> list[Path]:
    paths = [ROOT / "README.md"]
    paths.extend(SKILLS_DIR.rglob("*.md"))
    paths.extend((ROOT / "commands").glob("*.md"))
    return sorted(path for path in paths if path.is_file())


def collect_references() -> dict[str, set[str]]:
    refs: dict[str, set[str]] = {}
    for path in markdown_files():
        text = read_text(path)
        names = set(SLASH_REF_RE.findall(text))
        names.update(SKILL_TOOL_REF_RE.findall(text))
        if names:
            refs[str(path.relative_to(ROOT))] = names
    return refs


def main() -> int:
    skills, errors = load_skills()
    baseline = load_baseline()
    refs_by_file = collect_references()

    unresolved: dict[str, list[str]] = {}
    for path, refs in refs_by_file.items():
        missing = sorted(refs - skills)
        if missing:
            unresolved[path] = missing

    unresolved_names = {name for names in unresolved.values() for name in names}
    new_unresolved = unresolved_names - baseline
    stale_baseline = baseline - unresolved_names

    if new_unresolved:
        errors.append(
            "unresolved skill references not present in baseline: "
            + ", ".join(sorted(new_unresolved))
        )
        for path, names in unresolved.items():
            unexpected = sorted(set(names) & new_unresolved)
            if unexpected:
                errors.append(
                    f"{path}: unresolved references: " + ", ".join(unexpected)
                )

    if stale_baseline:
        errors.append(
            "stale baseline entries now resolve and must be removed: "
            + ", ".join(sorted(stale_baseline))
        )

    if errors:
        print("Skill reference validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    tracked = ", ".join(sorted(baseline)) or "none"
    print(
        f"Skill reference validation passed: {len(skills)} skills; "
        f"known unresolved baseline: {tracked}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
