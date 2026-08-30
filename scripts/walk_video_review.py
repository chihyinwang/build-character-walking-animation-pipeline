#!/usr/bin/env python3
"""Prepare complete-timeline evidence and validate an independently filled review form."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from pipeline_common import DIRECTIONS, file_records, numbered_pngs, read_json, records_current, write_json

CHECKS = (
    "identity",
    "facing",
    "locked_camera",
    "in_place_translation",
    "fixed_scale",
    "alternating_legs",
    "opposing_arms",
    "hands_free",
    "leg_tracks",
    "limb_continuity",
    "pose_continuity",
    "no_freezes_or_stutters",
    "usable_complete_cycle",
)


def contact_pages(frames: list[Path], output: Path, columns: int = 6, page_size: int = 48) -> list[Path]:
    output.mkdir(parents=True, exist_ok=True)
    pages: list[Path] = []
    font = ImageFont.load_default()
    for page_index in range(math.ceil(len(frames) / page_size)):
        batch = frames[page_index * page_size : (page_index + 1) * page_size]
        with Image.open(batch[0]) as sample:
            thumb_w = min(160, sample.width)
            thumb_h = min(160, sample.height)
        rows = math.ceil(len(batch) / columns)
        sheet = Image.new("RGB", (columns * (thumb_w + 12), rows * (thumb_h + 28)), "#30343b")
        draw = ImageDraw.Draw(sheet)
        for index, frame in enumerate(batch):
            with Image.open(frame) as image:
                tile = image.convert("RGB")
                tile.thumbnail((thumb_w, thumb_h), Image.Resampling.NEAREST)
            x = (index % columns) * (thumb_w + 12) + 6
            y = (index // columns) * (thumb_h + 28) + 6
            sheet.paste(tile, (x + (thumb_w - tile.width) // 2, y))
            draw.text((x, y + thumb_h + 6), frame.name, fill="white", font=font)
        path = output / f"timeline-{page_index + 1:02d}.png"
        sheet.save(path)
        pages.append(path)
    return pages


def prepare(args: argparse.Namespace) -> None:
    root = args.sprite_root.resolve()
    frames_dir = root / "all-frames" / f"walking-{args.direction}" / f"attempt-{args.attempt:02d}"
    frames = numbered_pngs(frames_dir)
    if not frames:
        raise SystemExit(f"No extracted frames: {frames_dir}")
    review_dir = root / "reviews" / f"walking-{args.direction}" / f"attempt-{args.attempt:02d}"
    pages = contact_pages(frames, review_dir / "timeline-pages")
    payload = {
        "schema_version": 1,
        "direction": args.direction,
        "attempt": args.attempt,
        "timeline_complete": True,
        "source_frames": file_records(root, frames),
        "timeline_pages": file_records(root, pages),
        "checks": {name: {"status": "pending", "evidence_frames": [], "notes": ""} for name in CHECKS},
        "overall_notes": "",
    }
    write_json(review_dir / "review-input.json", payload)
    print(review_dir / "review-input.json")


def validate(args: argparse.Namespace) -> None:
    root = args.sprite_root.resolve()
    review_dir = root / "reviews" / f"walking-{args.direction}" / f"attempt-{args.attempt:02d}"
    input_path = review_dir / "review-input.json"
    payload = read_json(input_path)
    errors: list[str] = []
    if not isinstance(payload, dict):
        raise SystemExit(f"Missing review input: {input_path}")
    current, integrity_errors = records_current(root, payload.get("source_frames"))
    if not current:
        errors.extend(integrity_errors)
    frame_names = {Path(item["path"]).name for item in payload.get("source_frames", []) if isinstance(item, dict)}
    if not payload.get("timeline_complete"):
        errors.append("timeline_complete must remain true")
    checks = payload.get("checks")
    if not isinstance(checks, dict):
        errors.append("checks mapping is missing")
        checks = {}
    for name in CHECKS:
        item = checks.get(name)
        if not isinstance(item, dict) or item.get("status") != "pass":
            errors.append(f"{name}: must be pass")
            continue
        evidence = item.get("evidence_frames")
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"{name}: at least one evidence frame is required")
        elif any(str(frame) not in frame_names for frame in evidence):
            errors.append(f"{name}: evidence references a missing source frame")
    result = {
        "schema_version": 1,
        "status": "pass" if not errors else "fail",
        "direction": args.direction,
        "attempt": args.attempt,
        "review_input": file_records(root, [input_path]),
        "source_frames": payload.get("source_frames", []),
        "errors": errors,
    }
    write_json(review_dir / "review.json", result)
    print(review_dir / "review.json")
    if errors:
        raise SystemExit("Video review failed:\n- " + "\n- ".join(errors))


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("prepare", "validate"):
        child = sub.add_parser(command)
        child.add_argument("--sprite-root", type=Path, required=True)
        child.add_argument("--direction", choices=DIRECTIONS, required=True)
        child.add_argument("--attempt", type=int, required=True)
    args = parser.parse_args()
    prepare(args) if args.command == "prepare" else validate(args)


if __name__ == "__main__":
    main()
