---
name: export-character-walk-runtime
description: Convert an approved original or pixel-snapped walk selection into aligned RGBA frames, a configurable spritesheet, previews, manifests, and computed stability QA. Use after the frame source is approved and a generic runtime export is required.
---

# Export Character Walk Runtime

Resolve every executable from `../../scripts/` relative to this skill directory.

## 1. Resolve the approved frame source

Read `frame-source.json`. Accept only a current `approved-original` or `approved-pixel-snapped` choice. Reject missing or stale hashes.

Complete this step when all selected input frames exist and match the recorded hashes.

## 2. Export a direction

Use project settings or these configurable defaults: 160×160 cells, five columns, maximum character height 132, ground anchor `(80, 138)`, 10 FPS, and background key `#00FF00`.

Run `runtime_export.py` with the character root and direction. The exporter must use one scale for the complete direction, preserve frame order, remove only background-connected key colour, align the ground contact, and leave unused sheet cells transparent.

Complete this step when frames, spritesheet, previews, manifest, alignment, and QA files exist.

## 3. Derive a mirrored direction

When the action manifest says `mirrored_from_west`, run `mirror_animation.py` after West approval. Verify exact horizontal reflection, equal frame count, equal dimensions, equal timing, and equivalent QA.

Complete this step when every requested direction has an exported or verified mirrored runtime.

## 4. Stability and visual review

Run `check_animation_stability.py`. Show the transparent preview plus light and dark background previews. Check sheet dimensions, frame order, FPS, ground anchor, scale, torso drift, visible fringe, loop seam, and manifest consistency.

Request final visual approval. Record it against the spritesheet, manifest, alignment, previews, and computed QA.

Complete this skill only when computed QA passes and the visual approval remains current.
