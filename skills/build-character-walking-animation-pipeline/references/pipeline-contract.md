# Character walking pipeline contract

## Contents

- [Identity and roots](#identity-and-roots)
- [Approval records](#approval-records)
- [Anchor generation](#anchor-generation)
- [Direction strategy](#direction-strategy)
- [Manual video boundary](#manual-video-boundary)
- [Video acceptance](#video-acceptance)
- [Keyframe selection](#keyframe-selection)
- [Optional pixel snap](#optional-pixel-snap)
- [Runtime export](#runtime-export)
- [Resume state machine](#resume-state-machine)

## Identity and roots

The stable character key is `character_id`, normally `npc-<number>`. The folder name may be the same key or a descriptive name. New examples use `~/Desktop/Sprites/npc-01`.

Never persist an expanded home directory, a source upload location, or a path outside the character root. Manifests use relative paths and SHA-256 hashes.

## Approval records

Every approval record contains a schema version, artifact name, status, reviewer, and a list of root-relative input paths with SHA-256 hashes. Changing or removing an input makes the approval stale. Generated output is never evidence of approval.

## Anchor generation

Codex generates South and every remaining still-image anchor, then presents the results for user approval. Never ask the user to generate, upload, or return a PNG. If Codex has no image-generation capability, the anchor stage is blocked.

The walking video described below is the only source media the user creates and returns.

## Direction strategy

South, North, and West are independent anchors. A symmetric character may derive East by exact horizontal reflection of West. A character with an anatomical-side feature requires an independently generated East.

Use the same policy for walking animation. Record each requested action direction as `generated`, `mirrored_from_west`, or `skipped`.

## Manual video boundary

The agent supplies one approved input image and one complete provider-neutral prompt. The user chooses and operates the video tool, reviews the result there, and returns a selected video file.

The agent does not open or control a video-generation website, submit prompts, spend credits, download results, or access account credentials.

## Video acceptance

Ingested videos are copied into the character root and hash recorded. Export and inspect the complete timeline before acceptance.

Independent checks cover identity, facing, camera, position, scale, gait alternation, arm opposition, hands, leg tracks, limb continuity, pose continuity, temporal smoothness, and a usable cycle. Every check needs `pass` plus frame evidence. `fail`, `unclear`, or missing evidence blocks acceptance.

Persistent identity, camera, direction, scale, anatomy, or gait failure is global. An isolated bad frame may be local only when a complete usable cycle remains elsewhere.

## Keyframe selection

Annotate every source frame. For walking, keep stable leg identities A and B through the whole timeline. Select a directed phase path rather than a fixed interval.

Prefer one chronological cycle. A replacement from another region must be semantically compatible with its previous and next selected frames. Review the loop seam and wraparound triplets.

The proposal requires both semantic phase validation and image-derived fixed-FPS motion validation. Show a normal GIF and at least four repeated loops before approval.

## Optional pixel snap

Pixel snap is an optional derivative after keyframe approval. The default frame source is the approved original selection.

Snapped files live in a separate folder and preserve source filenames. Compare original and snapped results visually. A rejected snapped derivative never changes or invalidates the approved source selection.

## Runtime export

Runtime export accepts either approved source. It creates RGBA frames, a sheet, previews, manifest, alignment, and computed QA. Runtime dimensions, columns, scale, anchor, FPS, and key colour are configurable.

The exporter contains only generic animation data and no game-specific rules.

## Resume state machine

Use the first incomplete gate:

| Evidence | Next action |
|---|---|
| No character spec | Gather and approve the brief |
| No current South approval | Create or review South |
| No current direction-set approval | Create or review directions |
| Generated direction lacks an accepted video | Give image and prompt; await user video |
| Video lacks a complete passing review | Review, revise prompt, or request replacement |
| Accepted video lacks phase map | Annotate all frames |
| Proposal validation fails | Repair the path or reject the video |
| Passing proposal lacks approval | Show keyframe evidence and await approval |
| Keyframes approved, no frame-source decision | Ask original versus optional pixel snap |
| Pixel-snap candidate lacks approval | Show comparison and await decision |
| Approved frame source lacks runtime | Export runtime |
| Runtime QA fails | Repair runtime settings or source |
| Runtime lacks current visual approval | Show previews and await approval |
| All gates current | Complete |
