#!/usr/bin/env python3
"""Choose approved original or pixel-snapped frames for runtime export."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from pipeline_common import file_records, read_json, selection_files, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sprite-root", required=True, type=Path)
    parser.add_argument("--direction", required=True, choices=("south", "north", "west", "east"))
    parser.add_argument("--source", required=True, choices=("original", "pixel-snapped"))
    parser.add_argument("--reviewer", default="user")
    args = parser.parse_args()

    root = args.sprite_root.resolve()
    work = root / "key-frames" / f"walking-{args.direction}"
    selection = work / "selection.json"
    names = selection_files(selection)
    accepted = read_json(root / "videos" / f"walking-{args.direction}" / "selected-attempt.json")
    if not isinstance(accepted, dict):
        raise SystemExit("No accepted source-video attempt")
    frames_dir = root / accepted["frame_directory"] if args.source == "original" else work / "pixel-snapped" / "frames"
    inputs = [selection, work / "phase-validation.json", work / "motion-validation.json"]
    for report in inputs[1:]:
        payload = read_json(report)
        if not isinstance(payload, dict) or payload.get("status") != "pass":
            raise SystemExit(f"Final validation does not pass: {report}")
    inputs.extend(frames_dir / name for name in names)
    payload = {
        "schemaVersion": 1,
        "status": f"approved-{args.source}",
        "reviewer": args.reviewer,
        "reviewedAt": datetime.now(timezone.utc).isoformat(),
        "framesRoot": frames_dir.relative_to(root).as_posix(),
        "inputs": file_records(root, inputs),
    }
    output = work / "frame-source.json"
    write_json(output, payload)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
