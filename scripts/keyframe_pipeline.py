#!/usr/bin/env python3
"""Create timeline overviews, proposal previews, and approval-gated final selections."""

from __future__ import annotations

import argparse
import json
import math
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from animation_media import contact_sheet, save_gif
from pipeline_common import DIRECTIONS, approval_state, numbered_pngs, read_json, selection_files, write_json


def selected_attempt(root: Path, direction: str) -> tuple[int, Path]:
    path = root / "videos" / f"walking-{direction}" / "selected-attempt.json"
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise SystemExit(f"Missing accepted attempt: {path}")
    frame_dir = root / payload["frame_directory"]
    return int(payload["attempt"]), frame_dir


def overview(args: argparse.Namespace) -> None:
    root = args.sprite_root.resolve()
    _, folder = selected_attempt(root, args.direction)
    frames = numbered_pngs(folder)
    if not frames:
        raise SystemExit("Accepted attempt has no source frames")
    output = root / "key-frames" / f"walking-{args.direction}" / "timeline-overview"
    output.mkdir(parents=True, exist_ok=True)
    page_size = args.columns * args.rows
    for page_index in range(math.ceil(len(frames) / page_size)):
        batch = frames[page_index * page_size : (page_index + 1) * page_size]
        contact_sheet(batch, output / f"page-{page_index + 1:02d}.png", columns=args.columns)
    write_json(
        output / "index.json",
        {
            "schema_version": 1,
            "frame_count": len(frames),
            "page_size": page_size,
            "pages": math.ceil(len(frames) / page_size),
            "all_frames_review_required": True,
        },
    )
    print(output)


def selection_paths(root: Path, direction: str, proposal: bool) -> tuple[Path, list[Path]]:
    key_root = root / "key-frames" / f"walking-{direction}"
    selection = key_root / ("proposed-selection.json" if proposal else "selection.json")
    _, source_dir = selected_attempt(root, direction)
    paths = [source_dir / name for name in selection_files(selection)]
    missing = [path.name for path in paths if not path.is_file()]
    if missing:
        raise SystemExit("Missing selected frames: " + ", ".join(missing))
    return selection, paths


def preview(args: argparse.Namespace) -> None:
    root = args.sprite_root.resolve()
    selection, frames = selection_paths(root, args.direction, proposal=True)
    output = root / "key-frames" / f"walking-{args.direction}" / "proposal-review"
    output.mkdir(parents=True, exist_ok=True)
    contact_sheet(frames, output / "selected-contact-sheet.png", columns=args.columns)
    save_gif(frames, output / "loop.gif", args.fps)
    save_gif(frames, output / f"loop-repeated-{args.repeats}x.gif", args.fps, args.repeats)
    write_json(
        output / "preview-settings.json",
        {
            "schema_version": 1,
            "fps": args.fps,
            "repeats": args.repeats,
            "selection": selection.relative_to(root).as_posix(),
            "frame_count": len(frames),
        },
    )
    print(output)


def finalize(args: argparse.Namespace) -> None:
    root = args.sprite_root.resolve()
    key_root = root / "key-frames" / f"walking-{args.direction}"
    proposal = key_root / "proposed-selection.json"
    phase_report = key_root / "proposal-phase-validation.json"
    motion_report = key_root / "proposal-motion-validation.json"
    for path in (proposal, phase_report, motion_report):
        payload = read_json(path)
        if path == proposal and not isinstance(payload, dict):
            raise SystemExit(f"Missing proposal: {path}")
        if path != proposal and (not isinstance(payload, dict) or payload.get("status") != "pass"):
            raise SystemExit(f"Proposal report does not pass: {path}")
    approval = root / "approvals" / f"walking-{args.direction}-keyframes.json"
    status, errors = approval_state(root, approval)
    if status != "approved":
        raise SystemExit(f"Current keyframe approval required ({status}): {'; '.join(errors)}")
    approved = read_json(approval)
    approved_paths = {item.get("path") for item in approved.get("inputs", []) if isinstance(item, dict)}
    required = {path.relative_to(root).as_posix() for path in (proposal, phase_report, motion_report)}
    if not required.issubset(approved_paths):
        raise SystemExit("Approval must cover the proposal and both passing proposal reports")
    destination = key_root / "selection.json"
    shutil.copyfile(proposal, destination)
    print(destination)


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    over = sub.add_parser("overview")
    over.add_argument("--sprite-root", type=Path, required=True)
    over.add_argument("--direction", choices=DIRECTIONS, required=True)
    over.add_argument("--columns", type=int, default=6)
    over.add_argument("--rows", type=int, default=8)
    prev = sub.add_parser("preview")
    prev.add_argument("--sprite-root", type=Path, required=True)
    prev.add_argument("--direction", choices=DIRECTIONS, required=True)
    prev.add_argument("--fps", type=float, default=10.0)
    prev.add_argument("--repeats", type=int, default=4)
    prev.add_argument("--columns", type=int, default=5)
    final = sub.add_parser("finalize")
    final.add_argument("--sprite-root", type=Path, required=True)
    final.add_argument("--direction", choices=DIRECTIONS, required=True)
    args = parser.parse_args()
    {"overview": overview, "preview": preview, "finalize": finalize}[args.command](args)


if __name__ == "__main__":
    main()
