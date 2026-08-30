#!/usr/bin/env python3
"""Create an exact horizontal reflection of an approved image."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageOps

from pipeline_common import sha256_file, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_png", type=Path)
    parser.add_argument("output_png", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    args.output_png.parent.mkdir(parents=True, exist_ok=True)
    ImageOps.mirror(Image.open(args.input_png)).save(args.output_png)
    if args.report:
        write_json(
            args.report,
            {
                "schemaVersion": 1,
                "operation": "horizontal-reflection",
                "sourceSha256": sha256_file(args.input_png),
                "outputSha256": sha256_file(args.output_png),
                "semanticReview": {"status": "pending"},
            },
        )
    print(args.output_png)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
