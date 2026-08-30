#!/usr/bin/env python3
"""Record a hash-linked user approval without storing absolute paths."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from pipeline_common import file_records, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sprite-root", required=True, type=Path)
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--status", required=True, choices=("approved", "rejected"))
    parser.add_argument("--reviewer", default="user")
    parser.add_argument("--notes", default="")
    parser.add_argument("--input", action="append", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    root = args.sprite_root.resolve()
    output = args.output or root / "approvals" / f"{args.artifact}.json"
    payload = {
        "schemaVersion": 1,
        "artifact": args.artifact,
        "status": args.status,
        "reviewer": args.reviewer,
        "reviewedAt": datetime.now(timezone.utc).isoformat(),
        "notes": args.notes,
        "inputs": file_records(root, args.input),
    }
    write_json(output, payload)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
