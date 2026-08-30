#!/usr/bin/env python3
"""Audit a plugin tree for privacy leaks, external code references, and release debris."""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path


TEXT_SUFFIXES = {".md", ".txt", ".py", ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg"}
IGNORED_WORKTREE_NAMES = {".git", ".venv", "venv"}
FORBIDDEN_NAMES = {".DS_Store", "__pycache__", ".pytest_cache", ".mypy_cache"}
EXTERNAL_IMPORTS = {"PIL", "numpy", "yaml", "imageio_ffmpeg"}


def is_probably_text(path: Path) -> bool:
    return path.suffix.lower() in TEXT_SUFFIXES or path.name in {"LICENSE"}


def audit(root: Path, deny_tokens: list[str]) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    local_modules = {path.stem for folder in (root / "scripts", root / "tests") for path in folder.glob("*.py")}
    private_home_patterns = (
        re.compile(re.escape("/" + "Users" + "/") + r"[^/\s]+/"),
        re.compile(re.escape("/" + "home" + "/") + r"[^/\s]+/"),
        re.compile(r"[A-Za-z]:[\\/](?:Users|Documents and Settings)[\\/][^\\/\s]+[\\/]", re.IGNORECASE),
    )
    email_pattern = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)

    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if any(part in IGNORED_WORKTREE_NAMES for part in path.parts):
            continue
        if any(part in FORBIDDEN_NAMES for part in path.parts):
            errors.append(f"release debris: {relative}")
            continue
        if path.is_symlink():
            try:
                target = path.resolve(strict=True)
            except FileNotFoundError:
                errors.append(f"broken symlink: {relative}")
                continue
            if target != root and root not in target.parents:
                errors.append(f"symlink leaves package: {relative}")
        lowered_name = relative.casefold()
        for token in deny_tokens:
            if token and token.casefold() in lowered_name:
                errors.append(f"denied token in filename: {relative}")
        if not path.is_file() or not is_probably_text(path):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"non-UTF-8 text file: {relative}")
            continue
        lowered = text.casefold()
        for token in deny_tokens:
            if token and token.casefold() in lowered:
                errors.append(f"denied token in content: {relative}")
        if any(pattern.search(text) for pattern in private_home_patterns):
            errors.append(f"absolute user-home path: {relative}")
        if email_pattern.search(text):
            errors.append(f"email address: {relative}")
        installed_skill_fragment = ".codex" + "/" + "skills"
        installed_skill_fragment_windows = ".codex" + "\\" + "skills"
        if installed_skill_fragment in text or installed_skill_fragment_windows in text:
            errors.append(f"external installed-skill reference: {relative}")
        private_key_markers = ("BEGIN" + " PRIVATE KEY", "BEGIN" + " OPENSSH PRIVATE KEY")
        if any(marker in text for marker in private_key_markers):
            errors.append(f"private-key material: {relative}")
        if path.suffix == ".py":
            try:
                tree = ast.parse(text, filename=relative)
            except SyntaxError as error:
                errors.append(f"Python syntax error in {relative}: {error.msg}")
                continue
            for node in ast.walk(tree):
                module = None
                if isinstance(node, ast.Import):
                    modules = [alias.name.split(".")[0] for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    modules = [node.module.split(".")[0]] if node.module else []
                else:
                    modules = []
                for module in modules:
                    if module in local_modules or module in EXTERNAL_IMPORTS or module in sys.stdlib_module_names or module == "__future__":
                        continue
                    errors.append(f"undeclared Python import in {relative}: {module}")

    for skill in (root / "skills").glob("*/SKILL.md"):
        text = skill.read_text(encoding="utf-8")
        for script_name in re.findall(r"\.\./\.\./scripts/([A-Za-z0-9_.-]+)", text):
            if not (root / "scripts" / script_name).is_file():
                errors.append(f"missing bundled script referenced by {skill.relative_to(root)}: {script_name}")
    return sorted(set(errors))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".", type=Path)
    parser.add_argument("--deny-token", action="append", default=[])
    args = parser.parse_args()
    errors = audit(args.root, args.deny_token)
    if errors:
        print("PUBLIC RELEASE AUDIT: FAIL")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)
    print("PUBLIC RELEASE AUDIT: PASS")


if __name__ == "__main__":
    main()
