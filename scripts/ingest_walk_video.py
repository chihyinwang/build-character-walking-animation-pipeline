#!/usr/bin/env python3
"""Copy a user-returned video into the character root without leaking its source path."""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

from pipeline_common import DIRECTIONS, VIDEO_SUFFIXES, relative_record_path, sha256_file, write_json


def next_attempt(folder: Path) -> int:
    numbers = []
    for path in folder.glob("attempt-*.*"):
        match = re.fullmatch(r"attempt-(\d+)", path.stem)
        if match:
            numbers.append(int(match.group(1)))
    return max(numbers, default=0) + 1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--sprite-root", type=Path, required=True)
    parser.add_argument("--direction", choices=DIRECTIONS, required=True)
    parser.add_argument("--attempt", type=int)
    args = parser.parse_args()

    source = args.source.resolve()
    if not source.is_file() or source.suffix.lower() not in VIDEO_SUFFIXES:
        raise SystemExit("Return file must be an existing MP4, MOV, or WEBM video")
    root = args.sprite_root.resolve()
    output_dir = root / "videos" / f"walking-{args.direction}"
    output_dir.mkdir(parents=True, exist_ok=True)
    attempt = args.attempt or next_attempt(output_dir)
    destination = output_dir / f"attempt-{attempt:02d}{source.suffix.lower()}"
    record = output_dir / f"attempt-{attempt:02d}.json"
    if destination.exists() or record.exists():
        raise SystemExit(f"Attempt {attempt:02d} already exists")
    shutil.copyfile(source, destination)
    write_json(
        record,
        {
            "schema_version": 1,
            "direction": args.direction,
            "attempt": attempt,
            "video": {"path": relative_record_path(root, destination), "sha256": sha256_file(destination)},
            "source_location_retained": False,
        },
    )
    print(record)


if __name__ == "__main__":
    main()
