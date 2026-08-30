#!/usr/bin/env python3

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PLUGIN = Path(__file__).resolve().parents[1]
AUDIT = PLUGIN / "scripts" / "audit_public_release.py"


class PublicReleaseAuditTest(unittest.TestCase):
    def run_audit(self, root: Path, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(AUDIT), str(root), *extra], text=True, capture_output=True, check=False)

    def test_clean_tree_passes_and_private_home_fails(self) -> None:
        with tempfile.TemporaryDirectory(prefix="release-audit-test-") as temporary:
            root = Path(temporary)
            (root / "scripts").mkdir()
            (root / "skills").mkdir()
            (root / "README.md").write_text("Generic public package\n", encoding="utf-8")
            self.assertEqual(0, self.run_audit(root).returncode)
            private_path = "/" + "Users" + "/example-person/private.png"
            (root / "README.md").write_text(private_path, encoding="utf-8")
            result = self.run_audit(root)
            self.assertEqual(1, result.returncode)
            self.assertIn("absolute user-home path", result.stdout)

    def test_deny_token_is_case_insensitive(self) -> None:
        with tempfile.TemporaryDirectory(prefix="release-audit-token-") as temporary:
            root = Path(temporary)
            (root / "scripts").mkdir()
            (root / "skills").mkdir()
            (root / "notes.md").write_text("Example Sensitive Marker", encoding="utf-8")
            result = self.run_audit(root, "--deny-token", "sensitive marker")
            self.assertEqual(1, result.returncode)

    def test_worktree_metadata_and_virtualenv_are_ignored(self) -> None:
        with tempfile.TemporaryDirectory(prefix="release-audit-worktree-") as temporary:
            root = Path(temporary)
            (root / "scripts").mkdir()
            (root / "skills").mkdir()
            (root / ".git" / "objects").mkdir(parents=True)
            (root / ".git" / "config").write_text("private working metadata\n", encoding="utf-8")
            (root / ".venv" / "lib").mkdir(parents=True)
            (root / ".venv" / "lib" / "dependency.py").write_text("import undeclared_package\n", encoding="utf-8")
            self.assertEqual(0, self.run_audit(root).returncode)

            (root / "__pycache__").mkdir()
            result = self.run_audit(root)
            self.assertEqual(1, result.returncode)
            self.assertIn("release debris", result.stdout)

    def test_anchor_generation_is_never_delegated_to_the_user(self) -> None:
        readme = (PLUGIN / "README.md").read_text(encoding="utf-8")
        anchor_skill = (PLUGIN / "skills" / "build-character-anchor-set" / "SKILL.md").read_text(encoding="utf-8")
        pipeline_skill = (
            PLUGIN / "skills" / "build-character-walking-animation-pipeline" / "SKILL.md"
        ).read_text(encoding="utf-8")
        combined = "\n".join((readme, anchor_skill, pipeline_skill)).casefold()

        self.assertNotIn("user-returned png", combined)
        self.assertIn("never ask the user to generate, upload, or return a still image", combined)
        self.assertIn("the walking video", combined)


if __name__ == "__main__":
    unittest.main()
