#!/usr/bin/env python3
"""Measure duplicate poses, speed pulses, and the loop seam at fixed FPS."""

from __future__ import annotations

import argparse
import statistics
from pathlib import Path

from PIL import Image, ImageDraw

from animation_media import image_difference, open_rgba
from pipeline_common import DIRECTIONS, file_records, read_json, read_yaml, selection_files, write_json


def transition_sheet(frames: list[Path], differences: list[float], output: Path) -> None:
    ranked = sorted(range(len(differences)), key=lambda index: differences[index], reverse=True)[: min(4, len(differences))]
    rows = []
    for index in ranked:
        first = open_rgba(frames[index])
        second = open_rgba(frames[(index + 1) % len(frames)])
        canvas = Image.new("RGBA", (first.width + second.width, max(first.height, second.height) + 24), (40, 43, 48, 255))
        canvas.alpha_composite(first, (0, 0))
        canvas.alpha_composite(second, (first.width, 0))
        ImageDraw.Draw(canvas).text((4, max(first.height, second.height) + 5), f"{frames[index].name} -> {frames[(index + 1) % len(frames)].name}: {differences[index]:.3f}", fill="white")
        rows.append(canvas)
    result = Image.new("RGBA", (max(row.width for row in rows), sum(row.height for row in rows)), (40, 43, 48, 255))
    y = 0
    for row in rows:
        result.alpha_composite(row, (0, y))
        y += row.height
    output.parent.mkdir(parents=True, exist_ok=True)
    result.save(output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sprite-root", type=Path, required=True)
    parser.add_argument("--direction", choices=DIRECTIONS, required=True)
    parser.add_argument("--final", action="store_true")
    parser.add_argument("--fps", type=float, default=10.0)
    parser.add_argument("--profile", type=Path)
    args = parser.parse_args()

    root = args.sprite_root.resolve()
    key_root = root / "key-frames" / f"walking-{args.direction}"
    selection = key_root / ("selection.json" if args.final else "proposed-selection.json")
    accepted = read_json(root / "videos" / f"walking-{args.direction}" / "selected-attempt.json")
    if not isinstance(accepted, dict):
        raise SystemExit("No accepted source video")
    source = root / accepted["frame_directory"]
    frames = [source / name for name in selection_files(selection)]
    if len(frames) < 4:
        raise SystemExit("Motion validation requires at least four selected frames")
    profile_path = args.profile or Path(__file__).resolve().parent.parent / "skills" / "select-character-walk-keyframes" / "references" / "walking-profile.yaml"
    settings = read_yaml(profile_path)["motion_continuity"]
    differences = [image_difference(frames[index], frames[(index + 1) % len(frames)]) for index in range(len(frames))]
    internal = differences[:-1]
    minimum = min(internal)
    maximum = max(internal)
    median = statistics.median(internal)
    velocity_ratio = maximum / max(minimum, 1e-9)
    seam_ratio = differences[-1] / max(median, 1e-9)
    duplicate_threshold = float(settings["duplicate_mean_absolute_difference"])
    errors: list[str] = []
    if minimum < duplicate_threshold:
        errors.append(f"near-duplicate internal transition: {minimum:.3f} < {duplicate_threshold:.3f}")
    if velocity_ratio > float(settings["maximum_velocity_ratio"]):
        errors.append(f"velocity ratio too high: {velocity_ratio:.3f}")
    if seam_ratio > float(settings["maximum_seam_ratio"]):
        errors.append(f"loop seam ratio too high: {seam_ratio:.3f}")
    review_dir = key_root / ("final-review" if args.final else "proposal-review")
    sheet = review_dir / "worst-transitions.png"
    transition_sheet(frames, differences, sheet)
    report = {
        "schema_version": 1,
        "status": "pass" if not errors else "fail",
        "selection_kind": "final" if args.final else "proposal",
        "fps": args.fps,
        "differences_mean_absolute_0_255": differences,
        "minimum_internal_difference": minimum,
        "maximum_internal_difference": maximum,
        "velocity_ratio": velocity_ratio,
        "seam_ratio": seam_ratio,
        "inputs": file_records(root, [selection, *frames]),
        "errors": errors,
    }
    output = key_root / ("motion-validation.json" if args.final else "proposal-motion-validation.json")
    write_json(output, report)
    print(output)
    if errors:
        raise SystemExit("Motion validation failed:\n- " + "\n- ".join(errors))


if __name__ == "__main__":
    main()
