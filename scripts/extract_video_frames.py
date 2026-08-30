#!/usr/bin/env python3
"""Decode every frame of an ingested video with the declared imageio-ffmpeg dependency."""

from __future__ import annotations

import argparse
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image

from pipeline_common import DIRECTIONS, read_json, relative_record_path, sha256_file, write_json


def find_attempt(root: Path, direction: str, attempt: int) -> tuple[Path, Path]:
    folder = root / "videos" / f"walking-{direction}"
    record = folder / f"attempt-{attempt:02d}.json"
    data = read_json(record)
    if not isinstance(data, dict):
        raise SystemExit(f"Missing video record: {record}")
    video = root / data["video"]["path"]
    if not video.is_file() or sha256_file(video) != data["video"]["sha256"]:
        raise SystemExit("Recorded video is missing or stale")
    return video, record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sprite-root", type=Path, required=True)
    parser.add_argument("--direction", choices=DIRECTIONS, required=True)
    parser.add_argument("--attempt", type=int, required=True)
    args = parser.parse_args()

    root = args.sprite_root.resolve()
    video, record = find_attempt(root, args.direction, args.attempt)
    output = root / "all-frames" / f"walking-{args.direction}" / f"attempt-{args.attempt:02d}"
    if output.exists() and any(output.glob("*.png")):
        raise SystemExit(f"Frame output is not empty: {output}")
    output.mkdir(parents=True, exist_ok=True)

    reader = imageio_ffmpeg.read_frames(str(video), pix_fmt="rgb24")
    metadata = next(reader)
    width, height = metadata["size"]
    count = 0
    for count, frame_bytes in enumerate(reader, start=1):
        array = np.frombuffer(frame_bytes, dtype=np.uint8).reshape(height, width, 3)
        Image.fromarray(array, mode="RGB").save(output / f"{count:06d}.png")
    if count == 0:
        raise SystemExit("No frames were decoded")

    write_json(
        output / "extraction.json",
        {
            "schema_version": 1,
            "direction": args.direction,
            "attempt": args.attempt,
            "source_video": {"path": relative_record_path(root, video), "sha256": sha256_file(video)},
            "source_record": {"path": relative_record_path(root, record), "sha256": sha256_file(record)},
            "frame_count": count,
            "source_fps": metadata.get("fps"),
            "source_size": [width, height],
            "duration_seconds": metadata.get("duration"),
            "numbering": "%06d.png",
        },
    )
    print(output)


if __name__ == "__main__":
    main()
