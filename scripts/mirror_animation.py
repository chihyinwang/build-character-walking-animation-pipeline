#!/usr/bin/env python3
"""Derive a runtime direction by exact horizontal reflection."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image, ImageOps

from animation_media import save_gif
from pipeline_common import DIRECTIONS, file_records, read_json, write_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sprite-root", type=Path, required=True)
    parser.add_argument("--source-direction", choices=DIRECTIONS, default="west")
    parser.add_argument("--target-direction", choices=DIRECTIONS, default="east")
    args = parser.parse_args()
    if args.source_direction == args.target_direction:
        raise SystemExit("Source and target directions must differ")
    root = args.sprite_root.resolve()
    source = root / "runtime" / f"walking-{args.source_direction}"
    source_manifest = read_json(source / "manifest.json")
    if not isinstance(source_manifest, dict):
        raise SystemExit("Source runtime manifest is missing")
    source_frames = [root / record["path"] for record in source_manifest["frames"]]
    target = root / "runtime" / f"walking-{args.target_direction}"
    target_frames_dir = target / "frames"
    target_frames_dir.mkdir(parents=True, exist_ok=True)
    target_frames: list[Path] = []
    for path in source_frames:
        with Image.open(path) as image:
            reflected = ImageOps.mirror(image.convert("RGBA"))
        destination = target_frames_dir / path.name
        reflected.save(destination)
        target_frames.append(destination)
    cell_w, cell_h = source_manifest["cell_size"]
    columns = source_manifest["sheet_columns"]
    rows = math.ceil(len(target_frames) / columns)
    sheet = Image.new("RGBA", (columns * cell_w, rows * cell_h), (0, 0, 0, 0))
    for index, path in enumerate(target_frames):
        with Image.open(path) as image:
            sheet.alpha_composite(image.convert("RGBA"), ((index % columns) * cell_w, (index // columns) * cell_h))
    target.mkdir(parents=True, exist_ok=True)
    sheet_path = target / "spritesheet.png"
    sheet.save(sheet_path)
    fps = float(source_manifest["fps"])
    save_gif(target_frames, target / "preview.gif", fps)
    save_gif(target_frames, target / "preview-repeated-4x.gif", fps, 4)
    write_json(
        target / "manifest.json",
        {
            **{key: value for key, value in source_manifest.items() if key not in ("direction", "frames", "spritesheet", "frame_source")},
            "direction": args.target_direction,
            "derivation": "exact-horizontal-reflection",
            "source_direction": args.source_direction,
            "source_inputs": file_records(root, [source / "manifest.json", *source_frames]),
            "frames": file_records(root, target_frames),
            "spritesheet": sheet_path.relative_to(root).as_posix(),
        },
    )
    print(target)


if __name__ == "__main__":
    main()
