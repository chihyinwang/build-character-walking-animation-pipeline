#!/usr/bin/env python3
"""Synthetic, non-personal test assets for end-to-end pipeline verification."""

from __future__ import annotations

from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw


PHASES = (
    "contact-a-forward",
    "down-a-support",
    "passing-a-support",
    "up-a-support",
    "contact-b-forward",
    "down-b-support",
    "passing-b-support",
    "up-b-support",
)


def character_frame(index: int, size: int = 96) -> Image.Image:
    offsets = (-8, -6, -3, 0, 8, 6, 3, 0)
    offset = offsets[index % len(offsets)]
    image = Image.new("RGB", (size, size), "#00FF00")
    draw = ImageDraw.Draw(image)
    draw.ellipse((40, 12, 56, 28), fill="#F2C6A0", outline="#20242A", width=2)
    draw.rectangle((37, 28, 59, 61), fill="#355CDE", outline="#20242A", width=2)
    draw.line((42, 38, 35 - offset // 2, 58), fill="#F2C6A0", width=5)
    draw.line((54, 38, 61 + offset // 2, 58), fill="#F2C6A0", width=5)
    draw.line((44, 60, 44 + offset, 82), fill="#26304A", width=6)
    draw.line((52, 60, 52 - offset, 82), fill="#26304A", width=6)
    return image


def write_video(path: Path, fps: float = 10.0) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    writer = imageio_ffmpeg.write_frames(str(path), (96, 96), fps=fps, codec="libx264", quality=8, pix_fmt_in="rgb24", pix_fmt_out="yuv420p")
    writer.send(None)
    try:
        for index in range(len(PHASES)):
            writer.send(np.asarray(character_frame(index), dtype=np.uint8).tobytes())
    finally:
        writer.close()
