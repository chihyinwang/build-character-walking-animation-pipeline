#!/usr/bin/env python3
"""Create non-destructive pixel-snapped candidates for an approved walk selection."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image

from animation_media import contact_sheet, save_gif
from pipeline_common import DIRECTIONS, file_records, read_json, selection_files, write_json
from pixel_snap import recover


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sprite-root", type=Path, required=True)
    parser.add_argument("--direction", choices=DIRECTIONS, required=True)
    parser.add_argument("--k-colors", type=int, default=256)
    parser.add_argument("--fps", type=float, default=10.0)
    args = parser.parse_args()

    root = args.sprite_root.resolve()
    key_root = root / "key-frames" / f"walking-{args.direction}"
    selection = key_root / "selection.json"
    names = selection_files(selection)
    accepted = read_json(root / "videos" / f"walking-{args.direction}" / "selected-attempt.json")
    if not isinstance(accepted, dict):
        raise SystemExit("No accepted source video")
    source_dir = root / accepted["frame_directory"]
    output = key_root / "pixel-snapped"
    frames_dir = output / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    reports: list[dict] = []
    outputs: list[Path] = []
    for name in names:
        source_path = source_dir / name
        with Image.open(source_path) as source:
            rgba = source.convert("RGBA")
            native, report = recover(rgba, args.k_colors)
            candidate = native.resize(rgba.size, Image.Resampling.NEAREST)
        destination = frames_dir / name
        candidate.save(destination)
        reports.append({"file": name, **report})
        outputs.append(destination)
    contact_sheet(outputs, output / "snapped-contact-sheet.png", columns=5)
    save_gif(outputs, output / "snapped-loop.gif", args.fps)
    save_gif(outputs, output / "snapped-loop-repeated-4x.gif", args.fps, 4)
    write_json(
        output / "snap-report.json",
        {
            "schema_version": 1,
            "method": "deterministic-grid-majority",
            "semantic_review": "pending",
            "source_inputs": file_records(root, [selection, *[source_dir / name for name in names]]),
            "candidate_outputs": file_records(root, outputs),
            "frames": reports,
        },
    )
    print(output)


if __name__ == "__main__":
    main()
