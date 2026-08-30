---
name: prepare-character-walk-video
description: Prepare a provider-neutral image-to-video walking request, show the exact directional anchor and prompt, accept a video returned by the user, and review its complete timeline. Use after directional anchors are approved; never operate a video-generation website for the user.
---

# Prepare Character Walk Video

Use this skill for manual video handoff. Read [walk-prompt-template.md](references/walk-prompt-template.md) immediately before preparing a request. Resolve every executable from `../../scripts/` relative to this skill directory.

## 1. Prepare one direction

Run `build_walk_request.py` with the character root and direction. Show the exact copied input anchor, complete prompt text, recommended duration and resolution, and accepted return formats: MP4, MOV, or WEBM.

Ask the user to review the result in their chosen generator and return the selected file. Do not choose a provider or control its website.

Complete this step when the user returns one video file for this direction.

## 2. Ingest and extract

Run `ingest_walk_video.py` to copy the returned file into the character root and record a SHA-256 hash without storing its original absolute path. Then run `extract_video_frames.py` to export the complete timeline.

Complete this step when the video record and a contiguous numbered PNG sequence exist.

## 3. Review the complete source

Run `walk_video_review.py prepare` to make contact sheets and a review form. Inspect the whole timeline directly and fill each independent check with `pass`, `fail`, or `unclear` plus concrete frame evidence.

Review identity, facing, camera, translation, scale, alternating legs, opposing arms, free hands, coherent leg tracks, limb continuity, pose continuity, freezes, stutters, and the presence of at least one usable cycle.

`fail` or `unclear` blocks selection. A repeated anatomical or motion defect is a global failure. Show evidence, revise only the prompt constraint that addresses the defect, and ask the user for another video.

Complete this step when `walk_video_review.py validate` passes.

## 4. Accept the attempt

Run `record_video_selection.py` to create a hash-linked `selected-attempt.json`. Do not hand-edit the selection record.

Complete this skill when the accepted video, review, and extracted frames remain current.
