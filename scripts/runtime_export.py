#!/usr/bin/env python3
"""Export one approved walk direction to configurable, engine-neutral runtime assets."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image

from animation_media import save_gif
from pipeline_common import (
    DIRECTIONS,
    alpha_bbox,
    file_records,
    keyed_rgba,
    parse_hex_colour,
    parse_point,
    parse_size,
    read_json,
    records_current,
    selection_files,
    write_json,
)


def composite_preview(frames: list[Path], output: Path, colour: str, fps: float, repeats: int = 1) -> None:
    rendered: list[Image.Image] = []
    for path in frames:
        with Image.open(path) as source:
            rgba = source.convert("RGBA")
        background = Image.new("RGBA", rgba.size, colour)
        background.alpha_composite(rgba)
        rendered.append(background.convert("RGB"))
    sequence = rendered * max(1, repeats)
    sequence[0].save(output, save_all=True, append_images=sequence[1:], duration=max(1, round(1000 / fps)), loop=0)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sprite-root", type=Path, required=True)
    parser.add_argument("--direction", choices=DIRECTIONS, required=True)
    parser.add_argument("--cell-size", default="160x160")
    parser.add_argument("--columns", type=int, default=5)
    parser.add_argument("--max-character-height", type=int, default=132)
    parser.add_argument("--ground-anchor", default="80,138")
    parser.add_argument("--fps", type=float, default=10.0)
    parser.add_argument("--chroma", default="#00FF00")
    parser.add_argument("--chroma-tolerance", type=int, default=24)
    args = parser.parse_args()

    root = args.sprite_root.resolve()
    key_root = root / "key-frames" / f"walking-{args.direction}"
    frame_source_path = key_root / "frame-source.json"
    frame_source = read_json(frame_source_path)
    if not isinstance(frame_source, dict) or frame_source.get("status") not in ("approved-original", "approved-pixel-snapped"):
        raise SystemExit("A current approved frame source is required")
    current, errors = records_current(root, frame_source.get("inputs"))
    if not current:
        raise SystemExit("Frame source is stale: " + "; ".join(errors))
    selection = key_root / "selection.json"
    names = selection_files(selection)
    source_dir = root / frame_source["framesRoot"]
    source_paths = [source_dir / name for name in names]
    if any(not path.is_file() for path in source_paths):
        raise SystemExit("Approved frame-source files are incomplete")

    cell_w, cell_h = parse_size(args.cell_size)
    anchor_x, anchor_y = parse_point(args.ground_anchor)
    if not (0 <= anchor_x < cell_w and 0 <= anchor_y < cell_h):
        raise SystemExit("Ground anchor must be inside the runtime cell")
    chroma = parse_hex_colour(args.chroma)
    keyed: list[Image.Image] = []
    boxes: list[tuple[int, int, int, int]] = []
    for path in source_paths:
        with Image.open(path) as image:
            rgba = keyed_rgba(image, chroma, args.chroma_tolerance)
        box = alpha_bbox(rgba)
        if box is None:
            raise SystemExit(f"No foreground after keying: {path.name}")
        keyed.append(rgba)
        boxes.append(box)
    max_width = max(box[2] - box[0] for box in boxes)
    max_height = max(box[3] - box[1] for box in boxes)
    scale = min(args.max_character_height / max_height, (cell_w - 4) / max_width)

    output = root / "runtime" / f"walking-{args.direction}"
    frames_dir = output / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    runtime_paths: list[Path] = []
    alignments: list[dict] = []
    for index, (name, rgba, box) in enumerate(zip(names, keyed, boxes)):
        crop = rgba.crop(box)
        target = (max(1, round(crop.width * scale)), max(1, round(crop.height * scale)))
        crop = crop.resize(target, Image.Resampling.NEAREST)
        left = anchor_x - crop.width // 2
        top = anchor_y - crop.height
        if left < 0 or left + crop.width > cell_w or top < 0:
            raise SystemExit(f"Aligned character exceeds runtime cell: {name}")
        cell = Image.new("RGBA", (cell_w, cell_h), (0, 0, 0, 0))
        cell.alpha_composite(crop, (left, top))
        destination = frames_dir / f"{index:03d}.png"
        cell.save(destination)
        runtime_paths.append(destination)
        alignments.append(
            {
                "index": index,
                "source_file": name,
                "runtime_file": destination.relative_to(root).as_posix(),
                "source_bbox": list(box),
                "scale": scale,
                "placement": [left, top],
                "ground_anchor": [anchor_x, anchor_y],
            }
        )

    rows = math.ceil(len(runtime_paths) / args.columns)
    sheet = Image.new("RGBA", (args.columns * cell_w, rows * cell_h), (0, 0, 0, 0))
    for index, path in enumerate(runtime_paths):
        with Image.open(path) as frame:
            sheet.alpha_composite(frame.convert("RGBA"), ((index % args.columns) * cell_w, (index // args.columns) * cell_h))
    sheet_path = output / "spritesheet.png"
    sheet.save(sheet_path)
    save_gif(runtime_paths, output / "preview.gif", args.fps)
    save_gif(runtime_paths, output / "preview-repeated-4x.gif", args.fps, 4)
    composite_preview(runtime_paths, output / "preview-light.gif", "#F2F2F2", args.fps, 4)
    composite_preview(runtime_paths, output / "preview-dark.gif", "#20242A", args.fps, 4)
    write_json(
        output / "alignment.json",
        {"schema_version": 1, "direction": args.direction, "uniform_scale": scale, "frames": alignments},
    )
    manifest_path = output / "manifest.json"
    write_json(
        manifest_path,
        {
            "schema_version": 1,
            "animation": "walking",
            "direction": args.direction,
            "fps": args.fps,
            "loop": True,
            "cell_size": [cell_w, cell_h],
            "sheet_columns": args.columns,
            "sheet_rows": rows,
            "frame_count": len(runtime_paths),
            "ground_anchor": [anchor_x, anchor_y],
            "max_character_height": args.max_character_height,
            "chroma_key": args.chroma.upper(),
            "chroma_tolerance": args.chroma_tolerance,
            "frame_source_status": frame_source["status"],
            "frame_source": file_records(root, [frame_source_path]),
            "frames": file_records(root, runtime_paths),
            "spritesheet": sheet_path.relative_to(root).as_posix(),
        },
    )
    print(output)


if __name__ == "__main__":
    main()
