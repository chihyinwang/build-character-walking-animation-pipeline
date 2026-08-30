#!/usr/bin/env python3
"""Shared helpers for the self-contained character walking pipeline."""

from __future__ import annotations

import hashlib
import json
import re
from collections import deque
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import yaml
from PIL import Image

DIRECTIONS = ("south", "north", "west", "east")
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
VIDEO_SUFFIXES = {".mp4", ".mov", ".webm"}
ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def read_json(path: Path, default: Any = None) -> Any:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def read_yaml(path: Path, default: Any = None) -> Any:
    if not path.is_file():
        return default
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return default if data is None else data


def write_yaml(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    temporary.replace(path)


def ensure_inside(root: Path, path: Path) -> Path:
    root_resolved = root.resolve()
    path_resolved = path.resolve()
    if path_resolved != root_resolved and root_resolved not in path_resolved.parents:
        raise ValueError(f"Path must be inside the character root: {path}")
    return path_resolved


def relative_record_path(root: Path, path: Path) -> str:
    return ensure_inside(root, path).relative_to(root.resolve()).as_posix()


def parse_size(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"(\d+)[xX](\d+)", value.strip())
    if not match:
        raise ValueError(f"Expected WIDTHxHEIGHT, received: {value}")
    return int(match.group(1)), int(match.group(2))


def parse_point(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"(-?\d+),(-?\d+)", value.strip())
    if not match:
        raise ValueError(f"Expected X,Y, received: {value}")
    return int(match.group(1)), int(match.group(2))


def parse_hex_colour(value: str) -> tuple[int, int, int]:
    cleaned = value.strip().lstrip("#")
    if not re.fullmatch(r"[0-9a-fA-F]{6}", cleaned):
        raise ValueError(f"Expected a six-digit hex colour, received: {value}")
    return tuple(int(cleaned[index : index + 2], 16) for index in (0, 2, 4))


def numbered_pngs(folder: Path) -> list[Path]:
    return sorted(path for path in folder.glob("*.png") if path.is_file())


def selection_files(selection_path: Path) -> list[str]:
    payload = read_json(selection_path)
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid selection file: {selection_path}")
    clips = payload.get("clips")
    if not isinstance(clips, list) or not clips:
        raise ValueError("Selection requires a non-empty clips list")
    files: list[str] = []
    for clip in clips:
        if not isinstance(clip, dict) or not isinstance(clip.get("frames"), list):
            raise ValueError("Every selection clip requires a frames list")
        files.extend(str(name) for name in clip["frames"])
    if not files or len(files) != len(set(files)):
        raise ValueError("Selection filenames must be non-empty and unique")
    return files


def file_records(root: Path, paths: Iterable[Path]) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for path in paths:
        resolved = ensure_inside(root, path)
        if not resolved.is_file():
            raise FileNotFoundError(path)
        records.append({"path": relative_record_path(root, resolved), "sha256": sha256_file(resolved)})
    return records


def records_current(root: Path, records: Any) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if not isinstance(records, list) or not records:
        return False, ["missing input records"]
    for record in records:
        if not isinstance(record, dict):
            errors.append("invalid input record")
            continue
        rel = record.get("path")
        expected = record.get("sha256")
        if not isinstance(rel, str) or not isinstance(expected, str):
            errors.append("input record requires path and sha256")
            continue
        candidate = ensure_inside(root, root / rel)
        if not candidate.is_file():
            errors.append(f"missing: {rel}")
        elif sha256_file(candidate) != expected:
            errors.append(f"stale: {rel}")
    return not errors, errors


def approval_state(root: Path, path: Path) -> tuple[str, list[str]]:
    payload = read_json(path)
    if not isinstance(payload, dict):
        return "missing", ["approval file missing"]
    if payload.get("status") != "approved":
        return str(payload.get("status", "invalid")), ["approval is not approved"]
    current, errors = records_current(root, payload.get("inputs"))
    return ("approved" if current else "stale"), errors


def border_background_colour(image: Image.Image) -> tuple[int, int, int]:
    rgb = np.asarray(image.convert("RGB"))
    border = np.concatenate((rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]), axis=0)
    colours, counts = np.unique(border.reshape(-1, 3), axis=0, return_counts=True)
    return tuple(int(value) for value in colours[int(np.argmax(counts))])


def background_connected_mask(
    image: Image.Image,
    colour: tuple[int, int, int] | None = None,
    tolerance: int = 24,
) -> np.ndarray:
    rgb = np.asarray(image.convert("RGB"), dtype=np.int16)
    target = np.asarray(colour or border_background_colour(image), dtype=np.int16)
    candidate = np.max(np.abs(rgb - target), axis=2) <= tolerance
    height, width = candidate.shape
    connected = np.zeros_like(candidate, dtype=bool)
    queue: deque[tuple[int, int]] = deque()
    for x in range(width):
        if candidate[0, x]:
            queue.append((0, x))
        if candidate[height - 1, x]:
            queue.append((height - 1, x))
    for y in range(height):
        if candidate[y, 0]:
            queue.append((y, 0))
        if candidate[y, width - 1]:
            queue.append((y, width - 1))
    while queue:
        y, x = queue.popleft()
        if connected[y, x] or not candidate[y, x]:
            continue
        connected[y, x] = True
        if y:
            queue.append((y - 1, x))
        if y + 1 < height:
            queue.append((y + 1, x))
        if x:
            queue.append((y, x - 1))
        if x + 1 < width:
            queue.append((y, x + 1))
    return connected


def keyed_rgba(
    image: Image.Image,
    colour: tuple[int, int, int] | None = None,
    tolerance: int = 24,
) -> Image.Image:
    rgba = np.asarray(image.convert("RGBA")).copy()
    mask = background_connected_mask(image, colour, tolerance)
    rgba[mask, :3] = 0
    rgba[mask, 3] = 0
    rgba[~mask, 3] = 255
    return Image.fromarray(rgba, mode="RGBA")


def alpha_bbox(image: Image.Image, threshold: int = 1) -> tuple[int, int, int, int] | None:
    alpha = np.asarray(image.convert("RGBA"))[:, :, 3]
    ys, xs = np.where(alpha >= threshold)
    if not len(xs):
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1
