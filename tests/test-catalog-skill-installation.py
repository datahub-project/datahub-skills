"""Verify catalog skills remain complete when installed independently."""

from __future__ import annotations

import re
import shutil
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CATALOG_SKILLS = (
    "datahub-search",
    "datahub-enrich",
    "datahub-lineage",
    "datahub-quality",
    "datahub-setup",
)
LOCAL_REFERENCE = re.compile(
    r"`((?:\.\./|references/|templates/)[^`]+\.(?:md|json|ya?ml))`"
)


class CatalogSkillInstallationTest(unittest.TestCase):
    def test_local_references_survive_standalone_installation(self) -> None:
        """Removing a skill from the repository must not break its references."""

        with tempfile.TemporaryDirectory() as temporary_directory:
            install_root = Path(temporary_directory)

            for skill_name in CATALOG_SKILLS:
                with self.subTest(skill=skill_name):
                    source = REPOSITORY_ROOT / "skills" / skill_name
                    installed = install_root / skill_name
                    shutil.copytree(source, installed, symlinks=False)

                    skill_markdown = (installed / "SKILL.md").read_text()
                    referenced_paths = set(LOCAL_REFERENCE.findall(skill_markdown))
                    self.assertTrue(
                        referenced_paths,
                        f"{skill_name} should declare at least one local artifact",
                    )

                    for relative_path in referenced_paths:
                        resolved = (installed / relative_path).resolve()
                        self.assertTrue(
                            resolved.is_relative_to(installed.resolve()),
                            f"{skill_name} reference escapes installed skill: {relative_path}",
                        )
                        self.assertTrue(
                            resolved.is_file(),
                            f"{skill_name} reference is missing after install: {relative_path}",
                        )


if __name__ == "__main__":
    unittest.main()
