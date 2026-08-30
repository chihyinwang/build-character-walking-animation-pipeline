#!/usr/bin/env python3
"""Match a directional anchor's height and foot baseline to an approved South anchor."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image

from pipeline_common import alpha_bbox, keyed_rgba, parse_hex_colour, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("south_png", type=Path)
    parser.add_argument("direction_png", type=Path)
    parser.add_argument("output_prefix", type=Path)
    parser.add_argument("--target-size", type=int, default=1024)
    parser.add_argument("--chroma", default="#00FF00")
    parser.add_argument("--chroma-tolerance", type=int, default=24)
    args = parser.parse_args()

    chroma = parse_hex_colour(args.chroma)
    south = keyed_rgba(Image.open(args.south_png), chroma, args.chroma_tolerance)
    direction = keyed_rgba(Image.open(args.direction_png), chroma, args.chroma_tolerance)
    south_box = alpha_bbox(south)
    direction_box = alpha_bbox(direction)
    if not south_box or not direction_box:
        raise ValueError("Both anchors require visible foreground")
    south_height = south_box[3] - south_box[1]
    direction_height = direction_box[3] - direction_box[1]
    scale = south_height / direction_height
    cropped = direction.crop(direction_box)
    resized = cropped.resize(
        (max(1, round(cropped.width * scale)), max(1, round(cropped.height * scale))),
        Image.Resampling.NEAREST,
    )
    canvas = Image.new("RGBA", south.size, (0, 255, 0, 255))
    x = (canvas.width - resized.width) // 2
    y = south_box[3] - resized.height
    canvas.alpha_composite(resized, (x, y))
    rgb = Image.new("RGB", canvas.size, args.chroma)
    rgb.paste(canvas.convert("RGB"), mask=canvas.getchannel("A"))
    prefix = args.output_prefix
    prefix.parent.mkdir(parents=True, exist_ok=True)
    native_path = prefix.with_name(prefix.name + "-native.png")
    rgb.save(native_path)
    target = rgb.resize((args.target_size, args.target_size), Image.Resampling.NEAREST)
    target_path = prefix.with_name(prefix.name + f"-{args.target_size}-chroma.png")
    target.save(target_path)
    report = {
        "schemaVersion": 1,
        "scale": scale,
        "southForegroundHeight": south_height,
        "sourceForegroundHeight": direction_height,
        "chroma": args.chroma.upper(),
        "chromaTolerance": args.chroma_tolerance,
        "translation": {"x": x, "y": y},
        "semanticReview": {"status": "pending"},
    }
    report_path = prefix.with_name(prefix.name + "-normalize-report.json")
    write_json(report_path, report)
    print(report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
