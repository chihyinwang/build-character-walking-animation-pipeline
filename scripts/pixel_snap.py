#!/usr/bin/env python3
"""Recover a coarse pixel grid and write non-destructive nearest-neighbour outputs."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image

from pipeline_common import background_connected_mask, border_background_colour, write_json


def edge_profile(array: np.ndarray, axis: int) -> np.ndarray:
    delta = np.abs(np.diff(array.astype(np.int16), axis=axis)).mean(axis=tuple(i for i in range(3) if i != axis))
    return delta.astype(np.float64)


def estimate_pitch(profile: np.ndarray, maximum: int = 64) -> int:
    if len(profile) < 8 or float(profile.std()) < 1e-6:
        return 8
    centred = profile - profile.mean()
    best_lag, best_score = 2, float("-inf")
    for lag in range(2, min(maximum, len(profile) // 3) + 1):
        score = float(np.dot(centred[:-lag], centred[lag:]) / max(1, len(centred) - lag))
        score /= 1.0 + 0.015 * lag
        if score > best_score:
            best_lag, best_score = lag, score
    return best_lag


def grid_bounds(profile: np.ndarray, pitch: int, length: int) -> list[int]:
    phase_scores = [float(profile[offset::pitch].sum()) for offset in range(pitch)]
    phase = int(np.argmax(phase_scores)) + 1
    cuts = [0]
    cuts.extend(value for value in range(phase, length, pitch) if 0 < value < length)
    cuts.append(length)
    return sorted(set(cuts))


def majority(block: np.ndarray) -> np.ndarray:
    colours, counts = np.unique(block.reshape(-1, block.shape[-1]), axis=0, return_counts=True)
    return colours[int(np.argmax(counts))]


def recover(image: Image.Image, k_colours: int) -> tuple[Image.Image, dict]:
    rgb = image.convert("RGB")
    quantized = rgb.quantize(colors=k_colours, method=Image.Quantize.FASTOCTREE).convert("RGB")
    array = np.asarray(quantized)
    x_profile = edge_profile(array, 1)
    y_profile = edge_profile(array, 0)
    pitch_x = estimate_pitch(x_profile)
    pitch_y = estimate_pitch(y_profile)
    x_bounds = grid_bounds(x_profile, pitch_x, array.shape[1])
    y_bounds = grid_bounds(y_profile, pitch_y, array.shape[0])
    native = np.zeros((len(y_bounds) - 1, len(x_bounds) - 1, 3), dtype=np.uint8)
    for row, (top, bottom) in enumerate(zip(y_bounds[:-1], y_bounds[1:])):
        for column, (left, right) in enumerate(zip(x_bounds[:-1], x_bounds[1:])):
            native[row, column] = majority(array[top:bottom, left:right])
    report = {
        "estimatedPitch": {"x": pitch_x, "y": pitch_y},
        "nativeDimensions": {"width": native.shape[1], "height": native.shape[0]},
        "gridCuts": {"x": x_bounds, "y": y_bounds},
    }
    return Image.fromarray(native, mode="RGB"), report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_png", type=Path)
    parser.add_argument("output_prefix", type=Path)
    parser.add_argument("--k-colors", type=int, default=256)
    parser.add_argument("--target-size", type=int, default=1024)
    parser.add_argument("--chroma", default="#00FF00")
    args = parser.parse_args()

    source = Image.open(args.input_png)
    native, report = recover(source, args.k_colors)
    prefix = args.output_prefix
    prefix.parent.mkdir(parents=True, exist_ok=True)
    native_path = prefix.with_name(prefix.name + "-native.png")
    native.save(native_path)
    target = native
    if args.target_size > 0:
        target = native.resize((args.target_size, args.target_size), Image.Resampling.NEAREST)
    target_path = prefix.with_name(prefix.name + f"-{args.target_size}.png")
    target.save(target_path)
    background = border_background_colour(target)
    mask = background_connected_mask(target, background, tolerance=0)
    chroma = tuple(int(args.chroma[index : index + 2], 16) for index in (1, 3, 5))
    chroma_array = np.asarray(target.convert("RGB")).copy()
    chroma_array[mask] = chroma
    chroma_path = prefix.with_name(prefix.name + f"-{args.target_size}-chroma.png")
    Image.fromarray(chroma_array, mode="RGB").save(chroma_path)
    report.update(
        {
            "schemaVersion": 1,
            "method": "deterministic-grid-majority",
            "sourceDimensions": {"width": source.width, "height": source.height},
            "kColors": args.k_colors,
            "targetDimensions": {"width": target.width, "height": target.height},
            "chroma": args.chroma.upper(),
            "semanticReview": {"status": "pending"},
        }
    )
    report_path = prefix.with_name(prefix.name + "-snap-report.json")
    write_json(report_path, report)
    print(report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
