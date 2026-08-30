#!/usr/bin/env python3
"""Create a provider-neutral image-to-video handoff package."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from character_identity import resolve_character_id
from pipeline_common import DIRECTIONS, file_records, read_yaml, relative_record_path, sha256_file, write_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sprite-root", type=Path, required=True)
    parser.add_argument("--direction", choices=DIRECTIONS, required=True)
    parser.add_argument("--anchor", type=Path)
    parser.add_argument("--duration", default="4-6 seconds")
    parser.add_argument("--resolution", default="the tool's highest square resolution")
    args = parser.parse_args()

    root = args.sprite_root.resolve()
    identity, _ = resolve_character_id(root)
    anchor = (args.anchor or root / "anchors" / "canonical" / f"{identity}-{args.direction}.png").resolve()
    if not anchor.is_file():
        raise SystemExit(f"Missing canonical anchor: {anchor}")

    request_dir = root / "video-requests" / f"walking-{args.direction}"
    request_dir.mkdir(parents=True, exist_ok=True)
    copied_anchor = request_dir / "input-anchor.png"
    shutil.copyfile(anchor, copied_anchor)

    spec = read_yaml(root / "spec" / "character-spec.yaml", {}) or {}
    style = str(spec.get("style", "Preserve the exact visual style and pixel structure of the reference image."))
    identity_notes = str(spec.get("identity", "Preserve the exact character identity, clothing, colours, proportions, and silhouette."))
    prompt = f"""Animate the supplied {args.direction}-facing character into a clean, in-place walking cycle.

Reference fidelity:
- {identity_notes}
- {style}
- Keep the character facing {args.direction} for the entire clip.
- Keep the full body visible and preserve every identity-defining detail.

Motion:
- Natural alternating left/right steps with clear contact, down, passing, and up poses.
- Arms swing opposite the legs; both hands remain empty and visible.
- Feet follow coherent tracks without leg swaps, sliding, crossing, or teleporting.
- Smooth constant cadence with no freeze, stutter, sudden acceleration, or pose duplication.
- Complete at least two readable walk cycles.

Composition:
- Walk strictly in place at the centre of the frame.
- Locked camera, fixed scale, fixed framing, and no zoom, pan, orbit, cut, or camera shake.
- Keep the original plain background unchanged.
- Do not add scenery, shadows, text, props, particles, or other characters.

Output target: {args.duration}, {args.resolution}.
"""
    prompt_path = request_dir / "prompt.txt"
    prompt_path.write_text(prompt, encoding="utf-8")
    write_json(
        request_dir / "request.json",
        {
            "schema_version": 1,
            "character_id": identity,
            "direction": args.direction,
            "duration": args.duration,
            "resolution": args.resolution,
            "accepted_video_formats": ["mp4", "mov", "webm"],
            "input_anchor": {"path": relative_record_path(root, copied_anchor), "sha256": sha256_file(copied_anchor)},
            "source_inputs": file_records(root, [anchor]),
            "prompt": relative_record_path(root, prompt_path),
            "handoff": "manual-user-generation",
        },
    )
    print(request_dir)


if __name__ == "__main__":
    main()
