#!/usr/bin/env python3
"""Build a labelled contact sheet for canonical character anchors."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw

from character_identity import resolve_character_id
from pipeline_common import DIRECTIONS


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sprite-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--tile-size", type=int, default=256)
    args = parser.parse_args()
    character_id, _ = resolve_character_id(args.sprite_root)
    images: list[tuple[str, Image.Image]] = []
    for direction in DIRECTIONS:
        path = args.sprite_root / "anchors" / "canonical" / f"{character_id}-{direction}.png"
        if path.is_file():
            images.append((direction, Image.open(path).convert("RGBA")))
    if not images:
        raise FileNotFoundError("No canonical anchors were found")
    width = args.tile_size * len(images)
    canvas = Image.new("RGB", (width, args.tile_size + 36), "white")
    draw = ImageDraw.Draw(canvas)
    for index, (label, image) in enumerate(images):
        image.thumbnail((args.tile_size, args.tile_size), Image.Resampling.NEAREST)
        x = index * args.tile_size + (args.tile_size - image.width) // 2
        y = (args.tile_size - image.height) // 2
        canvas.paste(image.convert("RGB"), (x, y))
        draw.text((index * args.tile_size + 8, args.tile_size + 10), label.upper(), fill="black")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(args.output)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
