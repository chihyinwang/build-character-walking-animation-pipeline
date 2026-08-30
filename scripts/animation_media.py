#!/usr/bin/env python3
"""Small image, contact-sheet, and GIF helpers shared by bundled scripts."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable

import numpy as np
from PIL import Image, ImageDraw, ImageFont


def open_rgba(path: Path) -> Image.Image:
    with Image.open(path) as source:
        return source.convert("RGBA")


def common_canvas(images: Iterable[Image.Image], background=(0, 0, 0, 0)) -> list[Image.Image]:
    items = [image.convert("RGBA") for image in images]
    width = max(image.width for image in items)
    height = max(image.height for image in items)
    result: list[Image.Image] = []
    for image in items:
        canvas = Image.new("RGBA", (width, height), background)
        canvas.alpha_composite(image, ((width - image.width) // 2, (height - image.height) // 2))
        result.append(canvas)
    return result


def save_gif(paths: list[Path], output: Path, fps: float, repeats: int = 1) -> None:
    images = common_canvas([open_rgba(path) for path in paths])
    sequence = images * max(1, repeats)
    output.parent.mkdir(parents=True, exist_ok=True)
    sequence[0].save(
        output,
        save_all=True,
        append_images=sequence[1:],
        duration=max(1, round(1000 / fps)),
        loop=0,
        disposal=2,
    )


def contact_sheet(paths: list[Path], output: Path, columns: int = 5, label: bool = True) -> None:
    images = [open_rgba(path) for path in paths]
    max_w = max(image.width for image in images)
    max_h = max(image.height for image in images)
    label_h = 20 if label else 0
    rows = math.ceil(len(images) / columns)
    sheet = Image.new("RGBA", (columns * (max_w + 8), rows * (max_h + label_h + 8)), (40, 43, 48, 255))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for index, (path, image) in enumerate(zip(paths, images)):
        x = (index % columns) * (max_w + 8) + 4
        y = (index // columns) * (max_h + label_h + 8) + 4
        sheet.alpha_composite(image, (x + (max_w - image.width) // 2, y))
        if label:
            draw.text((x, y + max_h + 3), path.name, fill="white", font=font)
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)


def image_difference(first: Path, second: Path) -> float:
    a = np.asarray(open_rgba(first).convert("RGB"), dtype=np.float32)
    b = np.asarray(open_rgba(second).convert("RGB"), dtype=np.float32)
    if a.shape != b.shape:
        raise ValueError("Compared animation frames must share dimensions")
    return float(np.mean(np.abs(a - b)))
