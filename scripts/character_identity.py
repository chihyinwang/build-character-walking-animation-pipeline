#!/usr/bin/env python3
"""Resolve a stable generic character ID from a character root."""

from __future__ import annotations

import argparse
from pathlib import Path

from pipeline_common import ID_PATTERN, read_yaml


def resolve_character_id(sprite_root: Path) -> tuple[str, str]:
    spec = read_yaml(sprite_root / "spec" / "character-spec.yaml", {})
    if isinstance(spec, dict):
        for key in ("character_id", "sprite_id", "asset_id"):
            value = spec.get(key)
            if isinstance(value, str) and ID_PATTERN.fullmatch(value):
                return value, f"spec.{key}"
    fallback = sprite_root.name.lower().replace("_", "-")
    if ID_PATTERN.fullmatch(fallback):
        return fallback, "folder"
    raise ValueError("A valid character_id is required in spec/character-spec.yaml")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sprite_root", type=Path)
    args = parser.parse_args()
    character_id, source = resolve_character_id(args.sprite_root)
    print(f"{character_id}\t{source}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
