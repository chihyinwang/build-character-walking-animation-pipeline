#!/usr/bin/env python3
"""Generate a metadata-free alternating-pixel guide image."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--size", type=int, default=1024)
    args = parser.parse_args()
    indices = np.indices((args.size, args.size)).sum(axis=0) % 2
    data = np.where(indices[:, :, None] == 0, np.array([32, 32, 32]), np.array([224, 224, 224]))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(data.astype(np.uint8), mode="RGB").save(args.output, optimize=False)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
