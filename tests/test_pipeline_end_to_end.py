#!/usr/bin/env python3

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml
from PIL import Image, ImageDraw

from make_synthetic_fixture import PHASES, character_frame, write_video


PLUGIN = Path(__file__).resolve().parents[1]
SCRIPTS = PLUGIN / "scripts"


def run(script: str, *arguments: object, expect: int = 0) -> subprocess.CompletedProcess[str]:
    process = subprocess.run(
        [sys.executable, str(SCRIPTS / script), *[str(value) for value in arguments]],
        text=True,
        capture_output=True,
        check=False,
    )
    if process.returncode != expect:
        raise AssertionError(f"{script} returned {process.returncode}\nstdout:\n{process.stdout}\nstderr:\n{process.stderr}")
    return process


class PipelineEndToEndTest(unittest.TestCase):
    def test_direction_normalization_keys_near_chroma_background(self) -> None:
        with tempfile.TemporaryDirectory(prefix="character-anchor-test-") as temporary:
            root = Path(temporary)
            south = root / "south.png"
            north = root / "north.png"

            south_image = Image.new("RGB", (64, 64), "#00F600")
            ImageDraw.Draw(south_image).rectangle((24, 8, 39, 55), fill="#D9A520")
            south_image.save(south)
            north_image = Image.new("RGB", (64, 64), "#00F600")
            ImageDraw.Draw(north_image).rectangle((25, 12, 38, 55), fill="#D9A520")
            north_image.save(north)

            run(
                "normalize_directional_anchor.py",
                south,
                north,
                root / "normalized",
                "--target-size", 64,
                "--chroma", "#00FF00",
                "--chroma-tolerance", 24,
            )
            report = json.loads((root / "normalized-normalize-report.json").read_text(encoding="utf-8"))
            self.assertEqual(48, report["southForegroundHeight"])
            self.assertEqual(44, report["sourceForegroundHeight"])
            self.assertEqual(24, report["chromaTolerance"])

    def test_manual_handoff_keyframes_optional_snap_and_runtime(self) -> None:
        with tempfile.TemporaryDirectory(prefix="character-walk-test-") as temporary:
            workspace = Path(temporary)
            root = workspace / "Sprites" / "npc-01"
            anchor_dir = root / "anchors" / "canonical"
            anchor_dir.mkdir(parents=True)
            anchor = anchor_dir / "npc-01-south.png"
            character_frame(0).save(anchor)
            spec_dir = root / "spec"
            spec_dir.mkdir(parents=True)
            (spec_dir / "character-spec.yaml").write_text(
                yaml.safe_dump({"character_id": "npc-01", "identity": "Blue coat and dark trousers", "style": "Crisp pixel character"}),
                encoding="utf-8",
            )
            directional_anchors = [anchor]
            for direction in ("north", "west", "east"):
                direction_anchor = anchor_dir / f"npc-01-{direction}.png"
                character_frame(0).save(direction_anchor)
                directional_anchors.append(direction_anchor)
            action_dir = root / "actions" / "walking"
            action_dir.mkdir(parents=True)
            (action_dir / "manifest.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "requestedDirections": ["south"],
                        "directions": {"south": {"source": "generated"}},
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            run(
                "record_approval.py",
                "--sprite-root", root,
                "--artifact", "south-anchor",
                "--status", "approved",
                "--input", anchor,
            )
            approval_arguments: list[object] = [
                "--sprite-root", root,
                "--artifact", "directional-anchors",
                "--status", "approved",
            ]
            for direction_anchor in directional_anchors:
                approval_arguments.extend(("--input", direction_anchor))
            run("record_approval.py", *approval_arguments)

            run("build_walk_request.py", "--sprite-root", root, "--direction", "south")
            request = root / "video-requests" / "walking-south"
            self.assertEqual(anchor.read_bytes(), (request / "input-anchor.png").read_bytes())
            request_record = json.loads((request / "request.json").read_text(encoding="utf-8"))
            self.assertEqual("manual-user-generation", request_record["handoff"])
            self.assertNotIn("https://", (request / "prompt.txt").read_text(encoding="utf-8"))

            returned_video = workspace / "returned-video.mp4"
            write_video(returned_video)
            run("ingest_walk_video.py", returned_video, "--sprite-root", root, "--direction", "south", "--attempt", 1)
            record_text = (root / "videos" / "walking-south" / "attempt-01.json").read_text(encoding="utf-8")
            self.assertNotIn(str(workspace), record_text)
            run("extract_video_frames.py", "--sprite-root", root, "--direction", "south", "--attempt", 1)
            frame_dir = root / "all-frames" / "walking-south" / "attempt-01"
            frame_names = [path.name for path in sorted(frame_dir.glob("*.png"))]
            self.assertEqual(len(PHASES), len(frame_names))

            run("walk_video_review.py", "prepare", "--sprite-root", root, "--direction", "south", "--attempt", 1)
            review_input = root / "reviews" / "walking-south" / "attempt-01" / "review-input.json"
            review = json.loads(review_input.read_text(encoding="utf-8"))
            for item in review["checks"].values():
                item.update({"status": "pass", "evidence_frames": [frame_names[0]], "notes": "Synthetic evidence"})
            review_input.write_text(json.dumps(review, indent=2) + "\n", encoding="utf-8")
            run("walk_video_review.py", "validate", "--sprite-root", root, "--direction", "south", "--attempt", 1)
            run("record_video_selection.py", "--sprite-root", root, "--direction", "south", "--attempt", 1)
            selected_attempt = json.loads((root / "videos" / "walking-south" / "selected-attempt.json").read_text(encoding="utf-8"))
            self.assertEqual("accepted", selected_attempt["status"])
            status = json.loads(run("pipeline_status.py", "--sprite-root", root).stdout)
            self.assertEqual("keyframe-annotation", status["nextStage"])

            run("keyframe_pipeline.py", "overview", "--sprite-root", root, "--direction", "south")
            key_root = root / "key-frames" / "walking-south"
            candidates = []
            for name, phase in zip(frame_names, PHASES):
                candidates.append(
                    {
                        "file": name,
                        "usable": True,
                        "phase": phase,
                        "state": {"support_leg": "A", "swing_leg": "B"},
                        "visual_checks": {
                            "arm_opposition": "pass",
                            "hands_free": "pass",
                            "leg_tracks": "pass",
                            "limb_continuity": "pass",
                            "pose_continuity": "pass",
                        },
                        "flags": [],
                        "confidence": 1.0,
                        "notes": "Synthetic phase",
                    }
                )
            (key_root / "phase-map.json").write_text(json.dumps({"schema_version": 1, "candidates": candidates}, indent=2) + "\n", encoding="utf-8")
            proposal = {"schema_version": 1, "fps": 10, "clips": [{"name": "loop", "frames": frame_names}]}
            (key_root / "proposed-selection.json").write_text(json.dumps(proposal, indent=2) + "\n", encoding="utf-8")
            run("validate_phase_map.py", "--sprite-root", root, "--direction", "south")
            run("keyframe_pipeline.py", "preview", "--sprite-root", root, "--direction", "south", "--fps", 10)
            run("validate_motion_continuity.py", "--sprite-root", root, "--direction", "south", "--fps", 10)

            phase_report = key_root / "proposal-phase-validation.json"
            motion_report = key_root / "proposal-motion-validation.json"
            run(
                "record_approval.py",
                "--sprite-root", root,
                "--artifact", "walking-south-keyframes",
                "--status", "approved",
                "--input", key_root / "proposed-selection.json",
                "--input", phase_report,
                "--input", motion_report,
            )
            run("keyframe_pipeline.py", "finalize", "--sprite-root", root, "--direction", "south")
            run("validate_phase_map.py", "--sprite-root", root, "--direction", "south", "--final")
            run("validate_motion_continuity.py", "--sprite-root", root, "--direction", "south", "--fps", 10, "--final")

            run("snap_selected_frames.py", "--sprite-root", root, "--direction", "south", "--fps", 10)
            run("build_snap_comparison.py", "--sprite-root", root, "--direction", "south", "--fps", 10)
            self.assertTrue((key_root / "pixel-snapped" / "comparison" / "side-by-side-repeated.gif").is_file())

            run("record_frame_source.py", "--sprite-root", root, "--direction", "south", "--source", "original")
            run("runtime_export.py", "--sprite-root", root, "--direction", "south", "--fps", 10)
            run("check_animation_stability.py", "--sprite-root", root, "--direction", "south")
            runtime = root / "runtime" / "walking-south"
            self.assertTrue((runtime / "spritesheet.png").is_file())
            runtime_manifest = json.loads((runtime / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual("#00FF00", runtime_manifest["chroma_key"])
            self.assertEqual(24, runtime_manifest["chroma_tolerance"])
            self.assertEqual(132, runtime_manifest["max_character_height"])
            self.assertEqual("pass", json.loads((runtime / "qa.json").read_text(encoding="utf-8"))["status"])
            status = json.loads(run("pipeline_status.py", "--sprite-root", root).stdout)
            self.assertEqual("runtime-review", status["nextStage"])


if __name__ == "__main__":
    unittest.main()
