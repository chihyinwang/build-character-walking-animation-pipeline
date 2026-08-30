# Build Character Walking Animation Pipeline

A provider-neutral, approval-gated Codex plugin for turning character anchors and a user-generated walking video into reviewed keyframes and runtime sprites.

Codex generates every still-image anchor. The only source media the user must
create and return is the walking video requested at the explicit video handoff.

## What it does

1. Creates and approves a South anchor.
2. Creates and approves four canonical directions.
3. Gives the user the exact image and prompt for manual video generation.
4. Reviews the returned video and selects a semantic walking loop.
5. Offers non-destructive pixel snap as an optional comparison.
6. Exports configurable runtime frames, spritesheets, previews, and QA.

The plugin never operates a video-generation website and contains only generic animation data.

## Quick start

Clone the repository and install its declared Python dependencies in an isolated environment:

```bash
git clone https://github.com/chihyinwang/build-character-walking-animation-pipeline.git
cd build-character-walking-animation-pipeline
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

Verify the checkout before installing or sharing it:

```bash
python3 -m unittest discover -s tests -p "test_*.py"
python3 scripts/audit_public_release.py .
```

## Requirements

- Python 3.10 or newer
- Packages listed in `requirements.txt`
- An image-generation capability available to Codex for every still-image anchor
- A user-selected image-to-video tool for walking clips

Install dependencies with:

```bash
python3 -m pip install -r requirements.txt
```

## Install the skills

Clone or download this folder, then ask Codex:

```text
Install the skills from this cloned skill-only plugin folder for my user account.
```

After installation, start with:

```text
$build-character-walking-animation-pipeline
```

The default character location is `~/Desktop/Sprites/npc-01`. Pass another character root when needed.

## Self-contained code

All pipeline executables are under `scripts/`. Skills resolve them relative to this plugin and do not call another local skill installation. Python packages remain normal declared dependencies rather than vendored binaries.

The plugin does not bundle an image-generation model, a video-generation provider, Python itself, or generated character media. Codex may use its native image-generation and file-inspection tools, while the user supplies only the walking video at the documented handoff. No script or reference from another locally installed Codex skill is required.

Generated anchors, returned videos, extracted frames, approvals, and runtime exports live in the selected character root outside this repository. Do not commit private character media or user-returned videos to the plugin repository.

## Repository layout

```text
.codex-plugin/   Plugin manifest
skills/          Approval-gated Codex workflow instructions
scripts/         All bundled pipeline executables
tests/           End-to-end and public-release regression tests
requirements.txt Declared Python dependencies
```

## Skill and code map

| Skill | Human checkpoint | Bundled code |
| --- | --- | --- |
| `build-character-walking-animation-pipeline` | Routes to exactly one next step | `pipeline_status.py`, `character_identity.py` |
| `build-character-anchor-set` | Approve South, then approve all four directions | `make_pixel_guide.py`, `pixel_snap.py`, `normalize_directional_anchor.py`, `mirror_image.py`, `build_anchor_review.py`, `record_approval.py` |
| `prepare-character-walk-video` | User receives exact image and prompt; returns a video; approves or rejects the full-timeline review | `build_walk_request.py`, `ingest_walk_video.py`, `extract_video_frames.py`, `walk_video_review.py`, `record_video_selection.py` |
| `select-character-walk-keyframes` | Approve the proposed fixed-FPS loop and validation evidence | `keyframe_pipeline.py`, `validate_phase_map.py`, `validate_motion_continuity.py`, `animation_media.py` |
| `pixel-snap-character-walk` | Choose original by default, or approve/reject a snapped comparison | `snap_selected_frames.py`, `build_snap_comparison.py`, `record_frame_source.py`, `pixel_snap.py` |
| `export-character-walk-runtime` | Approve the final runtime previews and computed QA | `runtime_export.py`, `mirror_animation.py`, `check_animation_stability.py`, `record_approval.py` |

Release checking is handled by `audit_public_release.py`. Every data manifest written by the pipeline stores paths relative to the character root and hashes the approval inputs.

## Checkpoint contract

At each pause, Codex must give the user something concrete to review and name the required response:

1. Codex-generated South contact sheet → `approve`, `reject`, or revision notes.
2. Codex-generated four-direction sheet plus individual anchors → `approve`, `reject`, or direction-specific notes.
3. Exact directional PNG plus video prompt → the only user-created source-media handoff: one MP4, MOV, or WEBM.
4. Full-timeline evidence → accept the video or regenerate from a corrected prompt.
5. Keyframe sheet, loop GIF, four-repeat GIF, and validation reports → `approve`, `reject`, or named transition notes.
6. Optional original/snapped comparison → keep original or approve snapped candidate.
7. Runtime sheet, transparent/light/dark previews, manifest, and QA → final approval or specific revision notes.

## Validate

```bash
python3 -m unittest discover -s tests -p "test_*.py"
python3 scripts/audit_public_release.py .
```

Run the Codex skill and plugin validators before publishing.
