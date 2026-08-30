---
name: build-character-anchor-set
description: Create and review a south-facing character anchor followed by a canonical north, south, east, and west set for a walking animation pipeline. Use when anchors are missing, rejected, stale, or need redesign; stop at the south and four-direction approval gates.
---

# Build Character Anchor Set

Create identity anchors without changing the character between directions. Resolve every executable from `../../scripts/` relative to this skill directory. All code must remain inside the plugin.

## 1. Create the South anchor

Use the user's brief and `spec/character-spec.yaml`. Codex must use its available image-generation capability to generate exactly one full-body south-facing character on a square canvas with a flat background suitable for extraction.

Never ask the user to generate, upload, or return a still image. Still-image generation is Codex's responsibility throughout this skill. If image generation is unavailable, report that the anchor stage is blocked and name the missing capability; do not replace it with a user PNG handoff. The only user-created source-media handoff in the complete walking pipeline is the walking video.

Keep identity, silhouette, costume, proportions, palette, and named asymmetry explicit. Do not add unrequested props or scene elements. Save the source under `anchors/raw/<character-id>-south-raw.png`.

For pixel art, run:

```bash
python3 ../../scripts/pixel_snap.py \
  "<south-raw.png>" \
  "<anchors/processed/character-id-south>" \
  --target-size 1024
```

Create a one-direction review with `build_anchor_review.py`. Show the original, processed result, native-scale view, and intended display-scale view. Request explicit approval and record it with `record_approval.py`.

Complete this step only when the approved South image is copied exactly to `anchors/canonical/<character-id>-south.png` and the approval hash is current.

## 2. Choose direction strategy

For a visually symmetric character, generate North and West independently and mirror West for East. For a character with an anatomical-side feature, generate East independently. Record each direction as `generated` or `mirrored_from_west` in `anchors/direction-manifest.yaml`.

Complete this step when each requested direction has an explicit source strategy.

## 3. Create remaining directions

Codex generates each direction from the approved canonical South anchor. Never ask the user to create a directional image. Preserve identity, character height, foot position, palette, and anatomical-side details.

Process new pixel-art directions with `pixel_snap.py`. Use `normalize_directional_anchor.py` only when an otherwise correct direction has a material height or baseline mismatch. Use `mirror_image.py` for exact symmetric reflection.

Never use deterministic alignment to conceal an identity, facing, or costume error.

Complete this step when canonical North, South, West, and required East images exist.

## 4. Four-direction review

Run:

```bash
python3 ../../scripts/build_anchor_review.py \
  --sprite-root "<character-root>" \
  --output "<character-root>/anchors/review/four-directions.png"
```

Show the contact sheet and all individual anchors. Check facing, identity, silhouette, character scale, foot baseline, palette, and asymmetry. Request explicit approval.

Complete this skill only when `approvals/directional-anchors.json` is current for every canonical image.
