#!/usr/bin/env python3
"""Compute runtime alignment and manifest stability checks."""

from __future__ import annotations

import argparse
import statistics
from pathlib import Path

from PIL import Image

from pipeline_common import DIRECTIONS, alpha_bbox, file_records, read_json, write_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sprite-root", type=Path, required=True)
    parser.add_argument("--direction", choices=DIRECTIONS, required=True)
    parser.add_argument("--max-height-variation", type=float, default=0.18)
    parser.add_argument("--max-centre-variation", type=float, default=0.12)
    args = parser.parse_args()
    root = args.sprite_root.resolve()
    output = root / "runtime" / f"walking-{args.direction}"
    manifest_path = output / "manifest.json"
    manifest = read_json(manifest_path)
    if not isinstance(manifest, dict):
        raise SystemExit(f"Missing runtime manifest: {manifest_path}")
    frame_paths = [root / record["path"] for record in manifest.get("frames", [])]
    errors: list[str] = []
    if len(frame_paths) != manifest.get("frame_count"):
        errors.append("manifest frame count does not match frame records")
    boxes = []
    for path in frame_paths:
        if not path.is_file():
            errors.append(f"missing runtime frame: {path.name}")
            continue
        with Image.open(path) as image:
            box = alpha_bbox(image)
        if box is None:
            errors.append(f"empty runtime frame: {path.name}")
        else:
            boxes.append(box)
    heights = [box[3] - box[1] for box in boxes]
    centres = [(box[0] + box[2]) / 2 for box in boxes]
    feet = [box[3] for box in boxes]
    height_ratio = (max(heights) - min(heights)) / max(1, statistics.median(heights)) if heights else 1.0
    centre_ratio = (max(centres) - min(centres)) / max(1, manifest.get("cell_size", [1])[0]) if centres else 1.0
    foot_variance = max(feet) - min(feet) if feet else -1
    if height_ratio > args.max_height_variation:
        errors.append(f"character-height variation too high: {height_ratio:.3f}")
    if centre_ratio > args.max_centre_variation:
        errors.append(f"horizontal-centre variation too high: {centre_ratio:.3f}")
    if foot_variance != 0:
        errors.append(f"ground contact varies by {foot_variance} pixels")
    sheet = output / "spritesheet.png"
    if not sheet.is_file():
        errors.append("spritesheet missing")
    else:
        with Image.open(sheet) as image:
            cell_w, cell_h = manifest["cell_size"]
            expected = (manifest["sheet_columns"] * cell_w, manifest["sheet_rows"] * cell_h)
            if image.size != expected:
                errors.append(f"spritesheet size {image.size} does not match {expected}")
    qa = {
        "schema_version": 1,
        "status": "pass" if not errors else "fail",
        "height_variation_ratio": height_ratio,
        "horizontal_centre_variation_ratio": centre_ratio,
        "foot_baseline_variance_pixels": foot_variance,
        "inputs": file_records(root, [manifest_path, sheet, *frame_paths]) if sheet.is_file() and all(path.is_file() for path in frame_paths) else [],
        "errors": errors,
    }
    path = output / "qa.json"
    write_json(path, qa)
    print(path)
    if errors:
        raise SystemExit("Runtime QA failed:\n- " + "\n- ".join(errors))


if __name__ == "__main__":
    main()
