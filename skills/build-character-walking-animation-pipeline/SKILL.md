---
name: build-character-walking-animation-pipeline
description: Build, inspect, and resume an approval-gated character walking animation from a south anchor through four directions, a user-generated video handoff, semantic keyframes, optional pixel snap, and generic runtime export. Use for new or incomplete walking sprite pipelines; do not use for non-walking actions or automatic operation of a video-generation website.
---

# Build Character Walking Animation Pipeline

Run the workflow as a resumable state machine. Treat the filesystem and recorded approvals as the source of truth. Advance only to the next human checkpoint.

Resolve this skill directory first. Every executable used by this pipeline is in `../../scripts/`, inside the same plugin. Never search for or invoke another copy elsewhere.

Read [pipeline-contract.md](references/pipeline-contract.md) before scanning or writing artifacts. Read [artifact-layout.md](references/artifact-layout.md) when creating a character root or explaining outputs.

## 1. Locate or initialize the character

Use a root named like `~/Desktop/Sprites/npc-01`. Accept an explicit root from the user. Otherwise inspect `~/Desktop/Sprites` and choose the requested `npc-<number>` folder. Do not store an expanded home path in manifests; record paths relative to the character root.

Run:

```bash
python3 ../../scripts/pipeline_status.py --sprite-root "<character-root>"
```

If no spec exists, gather the stable character ID, visual identity, costume, palette, silhouette, style, asymmetry, requested directions, runtime FPS, and runtime layout. Write `spec/character-spec.yaml`, show a plain-language summary, and request approval before generating an anchor.

Complete this step when the current state and exactly one next action are known.

## 2. Build and approve anchors

Read the bundled `$build-character-anchor-set` skill completely. Codex generates every still-image anchor; never ask the user to generate or return a PNG. Stop after the South review. Continue only after a current approval record exists for the exact South image. Then generate the remaining directions and stop again for the four-direction review.

If image generation is unavailable, report the anchor stage as blocked instead of delegating still-image creation to the user. The walking video in Step 3 is the only user-created source-media handoff.

Complete this step when current approvals exist for both the South anchor and the complete requested direction set.

## 3. Hand off video generation to the user

Read the bundled `$prepare-character-walk-video` skill completely. For one generated direction at a time, show the exact canonical input image and a provider-neutral prompt. Ask the user to generate the clip with a tool of their choice and return the video file. Do not open, control, sign in to, or generate on an external video website.

Accept the returned video only after its complete timeline review passes. For a global defect, show evidence, revise the prompt for that defect, and request another user-generated attempt.

Complete this step when every generated direction has a hash-linked accepted video, or when the user chooses to stop.

## 4. Select and approve keyframes

Read the bundled `$select-character-walk-keyframes` skill completely. Inspect every source frame, annotate gait state, validate the directed phase path, and validate fixed-FPS image continuity. Show the contact sheet, normal loop GIF, repeated loop GIF, worst-transition sheet, and both passing proposal reports.

Stop for explicit approval. Do not create the final `selection.json` before approval.

Complete this step when the approved selection and final validation reports match the proposal hashes.

## 5. Ask whether to pixel-snap

Read the bundled `$pixel-snap-character-walk` skill completely. Offer two choices after keyframe approval: preserve the approved source keyframes, which is the default, or create a non-destructive pixel-snapped candidate.

If the user chooses pixel snap, show before/after contact sheets and GIFs. Rejection returns to the unchanged source keyframes. Never overwrite approved frames.

Complete this step when `frame-source.json` records either `approved-original` or `approved-pixel-snapped` with current hashes.

## 6. Export and approve runtime assets

Read the bundled `$export-character-walk-runtime` skill completely. Export from the chosen frame source. Produce individual RGBA frames, a spritesheet, normal and repeated previews, a manifest, alignment data, and computed QA. Show transparent, light-background, and dark-background previews.

Stop for final visual approval. Record it with `record_approval.py` using the exact runtime outputs as inputs.

Complete this step only when computed QA passes and the final visual approval remains current.

## 7. Rescan and hand off

Run `pipeline_status.py` again. Report completed directions, generated versus mirrored directions, accepted attempt numbers, selected frame source, runtime settings, output paths, and the exact next action for any incomplete item.

Do not claim completion while a required approval or hash-linked gate is missing, rejected, or stale.
