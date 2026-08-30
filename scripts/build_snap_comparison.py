#!/usr/bin/env python3
"""Build side-by-side evidence for optional pixel-snap approval."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw

from animation_media import contact_sheet, open_rgba
from pipeline_common import DIRECTIONS, read_json, selection_files, write_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sprite-root", type=Path, required=True)
    parser.add_argument("--direction", choices=DIRECTIONS, required=True)
    parser.add_argument("--fps", type=float, default=10.0)
    parser.add_argument("--repeats", type=int, default=4)
    args = parser.parse_args()

    root = args.sprite_root.resolve()
    key_root = root / "key-frames" / f"walking-{args.direction}"
    names = selection_files(key_root / "selection.json")
    accepted = read_json(root / "videos" / f"walking-{args.direction}" / "selected-attempt.json")
    if not isinstance(accepted, dict):
        raise SystemExit("No accepted source video")
    source_dir = root / accepted["frame_directory"]
    snapped_dir = key_root / "pixel-snapped" / "frames"
    originals = [source_dir / name for name in names]
    snapped = [snapped_dir / name for name in names]
    if any(not path.is_file() for path in snapped):
        raise SystemExit("Pixel-snapped candidate is incomplete")
    output = key_root / "pixel-snapped" / "comparison"
    output.mkdir(parents=True, exist_ok=True)
    contact_sheet(originals, output / "original-contact-sheet.png")
    contact_sheet(snapped, output / "snapped-contact-sheet.png")
    pairs: list[Image.Image] = []
    for name, original_path, snapped_path in zip(names, originals, snapped):
        original = open_rgba(original_path)
        candidate = open_rgba(snapped_path)
        height = max(original.height, candidate.height)
        pair = Image.new("RGBA", (original.width + candidate.width, height + 24), (40, 43, 48, 255))
        pair.alpha_composite(original, (0, 0))
        pair.alpha_composite(candidate, (original.width, 0))
        ImageDraw.Draw(pair).text((4, height + 5), f"original | snapped — {name}", fill="white")
        pairs.append(pair)
    sequence = pairs * max(1, args.repeats)
    duration = max(1, round(1000 / args.fps))
    sequence[0].save(output / "side-by-side-repeated.gif", save_all=True, append_images=sequence[1:], duration=duration, loop=0, disposal=2)
    write_json(
        output / "comparison.json",
        {
            "schema_version": 1,
            "fps": args.fps,
            "repeats": args.repeats,
            "review_checks": ["eyes", "face", "hands", "feet", "outline", "palette", "scale", "identity", "motion"],
            "status": "pending-user-review",
        },
    )
    print(output)


if __name__ == "__main__":
    main()
