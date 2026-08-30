#!/usr/bin/env python3
"""Validate complete frame annotations and the directed semantic phase path."""

from __future__ import annotations

import argparse
from pathlib import Path

from pipeline_common import DIRECTIONS, file_records, numbered_pngs, read_json, read_yaml, selection_files, write_json


MANDATORY_LANDMARKS = {"contact-a-forward", "passing-a-support", "contact-b-forward", "passing-b-support"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sprite-root", type=Path, required=True)
    parser.add_argument("--direction", choices=DIRECTIONS, required=True)
    parser.add_argument("--final", action="store_true")
    parser.add_argument("--profile", type=Path)
    args = parser.parse_args()

    root = args.sprite_root.resolve()
    key_root = root / "key-frames" / f"walking-{args.direction}"
    selection = key_root / ("selection.json" if args.final else "proposed-selection.json")
    phase_map_path = key_root / "phase-map.json"
    profile_path = args.profile or Path(__file__).resolve().parent.parent / "skills" / "select-character-walk-keyframes" / "references" / "walking-profile.yaml"
    profile = read_yaml(profile_path)
    phase_map = read_json(phase_map_path)
    errors: list[str] = []

    accepted = read_json(root / "videos" / f"walking-{args.direction}" / "selected-attempt.json")
    if not isinstance(accepted, dict):
        raise SystemExit("No accepted source video")
    source_dir = root / accepted["frame_directory"]
    source_frames = numbered_pngs(source_dir)
    source_names = [path.name for path in source_frames]
    candidates = phase_map.get("candidates", []) if isinstance(phase_map, dict) else []
    annotations = {item.get("file"): item for item in candidates if isinstance(item, dict) and isinstance(item.get("file"), str)}
    if len(annotations) != len(candidates):
        errors.append("phase map contains duplicate or invalid candidate records")
    if set(annotations) != set(source_names):
        missing = sorted(set(source_names) - set(annotations))
        extra = sorted(set(annotations) - set(source_names))
        if missing:
            errors.append("unannotated source frames: " + ", ".join(missing))
        if extra:
            errors.append("annotations without source frames: " + ", ".join(extra))

    try:
        chosen = selection_files(selection)
    except (ValueError, FileNotFoundError) as error:
        chosen = []
        errors.append(str(error))
    phases: list[str] = []
    required_checks = profile.get("required_visual_checks", []) if isinstance(profile, dict) else []
    allowed = profile.get("allowed_transitions", {}) if isinstance(profile, dict) else {}
    for name in chosen:
        item = annotations.get(name)
        if not item:
            errors.append(f"selected frame lacks annotation: {name}")
            continue
        if item.get("usable") is not True:
            errors.append(f"selected frame is not usable: {name}")
        phase = item.get("phase")
        if phase not in allowed:
            errors.append(f"selected frame has unknown phase: {name}")
        else:
            phases.append(phase)
        checks = item.get("visual_checks", {})
        for check in required_checks:
            if checks.get(check) != "pass":
                errors.append(f"{name}: {check} must pass")
        if item.get("flags"):
            errors.append(f"{name}: selected frame retains defect flags")

    if phases and not MANDATORY_LANDMARKS.issubset(set(phases)):
        errors.append("selection is missing required contact or passing landmarks")
    transitions: list[dict[str, str | bool]] = []
    for index, current in enumerate(phases):
        following = phases[(index + 1) % len(phases)]
        valid = following in allowed.get(current, [])
        transitions.append({"from": current, "to": following, "valid": valid})
        if not valid:
            errors.append(f"illegal phase transition: {current} -> {following}")

    inputs = [path for path in (selection, phase_map_path) if path.is_file()] + source_frames
    report = {
        "schema_version": 1,
        "status": "pass" if not errors else "fail",
        "selection_kind": "final" if args.final else "proposal",
        "selected_files": chosen,
        "selected_phases": phases,
        "transitions": transitions,
        "all_source_frames_annotated": set(annotations) == set(source_names),
        "inputs": file_records(root, inputs),
        "errors": errors,
    }
    output = key_root / ("phase-validation.json" if args.final else "proposal-phase-validation.json")
    write_json(output, report)
    print(output)
    if errors:
        raise SystemExit("Phase validation failed:\n- " + "\n- ".join(errors))


if __name__ == "__main__":
    main()
