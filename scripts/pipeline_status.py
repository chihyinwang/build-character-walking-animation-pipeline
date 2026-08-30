#!/usr/bin/env python3
"""Inspect a character root and report the first incomplete walking gate."""

from __future__ import annotations

import argparse
from pathlib import Path

from character_identity import resolve_character_id
from pipeline_common import DIRECTIONS, approval_state, read_json, read_yaml, records_current, write_json


def report(root: Path) -> dict:
    spec_path = root / "spec" / "character-spec.yaml"
    spec = read_yaml(spec_path)
    if not isinstance(spec, dict):
        return {"spriteRoot": str(root), "nextStage": "character-spec", "directions": []}

    character_id, source = resolve_character_id(root)
    south_approval, south_errors = approval_state(root, root / "approvals" / "south-anchor.json")
    direction_approval, direction_errors = approval_state(
        root, root / "approvals" / "directional-anchors.json"
    )
    action = read_json(root / "actions" / "walking" / "manifest.json", {})
    direction_policy = action.get("directions", {}) if isinstance(action, dict) else {}
    requested = action.get("requestedDirections", list(DIRECTIONS)) if isinstance(action, dict) else list(DIRECTIONS)
    if not isinstance(requested, list):
        requested = list(DIRECTIONS)

    directions: list[dict] = []
    next_stage = "complete"
    if south_approval != "approved":
        next_stage = "south-anchor-review"
    elif direction_approval != "approved":
        next_stage = "directional-anchor-review"

    priority = {
        "walk-video": 0,
        "video-review": 1,
        "keyframe-annotation": 2,
        "keyframe-validation": 3,
        "keyframe-approval": 4,
        "frame-source-decision": 5,
        "runtime-export": 6,
        "runtime-review": 7,
        "complete": 99,
    }
    candidate_next: list[str] = []
    for direction in requested:
        if direction not in DIRECTIONS:
            continue
        policy = direction_policy.get(direction, {}) if isinstance(direction_policy, dict) else {}
        source_type = policy.get("source", "generated") if isinstance(policy, dict) else "generated"
        video_dir = root / "videos" / f"walking-{direction}"
        selected_attempt = read_json(video_dir / "selected-attempt.json")
        work = root / "key-frames" / f"walking-{direction}"
        frame_source = read_json(work / "frame-source.json")
        runtime = root / "runtime" / f"walking-{direction}"
        stage = "complete"
        if source_type == "mirrored_from_west":
            if not (runtime / "manifest.json").is_file():
                stage = "runtime-export"
        elif not isinstance(selected_attempt, dict) or selected_attempt.get("status") != "accepted":
            stage = "walk-video"
        else:
            frame_directory = selected_attempt.get("frame_directory")
            frames_dir = root / frame_directory if isinstance(frame_directory, str) else None
            if frames_dir is None or not any(frames_dir.glob("*.png")):
                stage = "video-review"
            elif not (work / "phase-map.json").is_file():
                stage = "keyframe-annotation"
            elif not (work / "proposal-phase-validation.json").is_file() or not (
                work / "proposal-motion-validation.json"
            ).is_file():
                stage = "keyframe-validation"
            elif not (work / "selection.json").is_file():
                stage = "keyframe-approval"
            elif not isinstance(frame_source, dict):
                stage = "frame-source-decision"
            else:
                current, _ = records_current(root, frame_source.get("inputs"))
                if not current:
                    stage = "frame-source-decision"
                elif not (runtime / "manifest.json").is_file():
                    stage = "runtime-export"
                else:
                    runtime_approval, _ = approval_state(
                        root, root / "approvals" / f"runtime-walking-{direction}.json"
                    )
                    if runtime_approval != "approved":
                        stage = "runtime-review"
        directions.append({"direction": direction, "source": source_type, "nextStage": stage})
        candidate_next.append(stage)

    if next_stage == "complete" and candidate_next:
        next_stage = min(candidate_next, key=lambda item: priority.get(item, 50))
    return {
        "spriteRoot": str(root),
        "characterId": character_id,
        "characterIdSource": source,
        "southApproval": {"status": south_approval, "errors": south_errors},
        "directionApproval": {"status": direction_approval, "errors": direction_errors},
        "directions": directions,
        "nextStage": next_stage,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sprite-root", required=True, type=Path)
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()
    payload = report(args.sprite_root.resolve())
    if args.json_output:
        write_json(args.json_output, payload)
    import json

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
