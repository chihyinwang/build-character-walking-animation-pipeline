---
name: pixel-snap-character-walk
description: Create and review an optional, non-destructive pixel-snapped derivative of approved walking keyframes. Use only after keyframe approval when the user chooses pixel snap; preserve the approved source frames as the default fallback.
---

# Pixel Snap Character Walk

Resolve every executable from `../../scripts/` relative to this skill directory.

## 1. Confirm the branch

Ask whether the user wants to preserve the approved keyframes or compare a pixel-snapped derivative. Preserving originals is the default. Do not infer approval from earlier anchor processing.

Complete this step when the user's choice is explicit.

## 2. Create the candidate

When chosen, run `snap_selected_frames.py` with the character root and direction. Write only under `key-frames/walking-<direction>/pixel-snapped/`. Preserve source filenames and never modify `all-frames/`, `phase-map.json`, or `selection.json`.

Complete this step when every selected source frame has one candidate output and a report.

## 3. Compare and approve

Run `build_snap_comparison.py`. Show original and snapped contact sheets, normal GIFs, and a side-by-side repeated GIF. Inspect eyes, face, hands, feet, outline, palette, scale, frame-to-frame identity, and motion.

If rejected, record `approved-original` in `frame-source.json`. If approved, record `approved-pixel-snapped` with hashes for all snapped frames. Generated files alone are not approval.

Complete this skill when runtime has one explicit, current frame source.
