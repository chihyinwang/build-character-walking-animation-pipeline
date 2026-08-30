#!/usr/bin/env python3
"""Accept one reviewed video attempt through hash-linked records."""

from __future__ import annotations

import argparse
from pathlib import Path

from pipeline_common import DIRECTIONS, file_records, read_json, records_current, write_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sprite-root", type=Path, required=True)
    parser.add_argument("--direction", choices=DIRECTIONS, required=True)
    parser.add_argument("--attempt", type=int, required=True)
    args = parser.parse_args()
    root = args.sprite_root.resolve()
    video_record = root / "videos" / f"walking-{args.direction}" / f"attempt-{args.attempt:02d}.json"
    review = root / "reviews" / f"walking-{args.direction}" / f"attempt-{args.attempt:02d}" / "review.json"
    video_data = read_json(video_record)
    review_data = read_json(review)
    if not isinstance(video_data, dict):
        raise SystemExit(f"Missing video record: {video_record}")
    if not isinstance(review_data, dict) or review_data.get("status") != "pass":
        raise SystemExit("Attempt does not have a passing complete-timeline review")
    current, errors = records_current(root, review_data.get("source_frames"))
    if not current:
        raise SystemExit("Review is stale: " + "; ".join(errors))
    video = root / video_data["video"]["path"]
    frame_dir = root / "all-frames" / f"walking-{args.direction}" / f"attempt-{args.attempt:02d}"
    write_json(
        root / "videos" / f"walking-{args.direction}" / "selected-attempt.json",
        {
            "schema_version": 1,
            "status": "accepted",
            "direction": args.direction,
            "attempt": args.attempt,
            "inputs": file_records(root, [video, video_record, review]),
            "frame_directory": frame_dir.relative_to(root).as_posix(),
        },
    )


if __name__ == "__main__":
    main()
