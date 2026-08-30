---
name: select-character-walk-keyframes
description: Inspect every frame of an accepted walking video, annotate stable gait semantics, select a coherent closed phase path, validate fixed-FPS motion, and show contact sheets and repeated GIF previews for approval. Do not use fixed-interval sampling.
---

# Select Character Walk Keyframes

Treat the source timeline as candidate evidence rather than trustworthy motion. Read [walking-profile.yaml](references/walking-profile.yaml) and [phase-map-schema.yaml](references/phase-map-schema.yaml) before annotation. Resolve every executable from `../../scripts/` relative to this skill directory.

## 1. Review every source frame

Run `keyframe_pipeline.py overview` on the complete extracted frame folder. Inspect every contact-sheet page.

Create `phase-map.json` with one record per source frame. Assign stable leg identities A and B at the first unambiguous contact and do not relabel them later. Record phase, support and swing roles, front/back state, foot contact, swing direction, opposing arms, hand state, continuity checks, defects, confidence, and notes.

Complete this step when every source filename has exactly one annotation.

## 2. Assemble a closed path

Prefer one intact chronological gait cycle. Replace only an isolated unusable frame with a phase-compatible candidate after reviewing `previous → candidate → next`. Check wraparound triplets and the final-to-first transition.

Keep required gait landmarks and any in-between frames needed for even fixed-FPS motion. Do not select evenly spaced frames or duplicate the endpoint. Write `proposed-selection.json` derived from `phase-map.json`.

Complete this step when the proposed loop follows a legal directed phase path.

## 3. Validate and preview

Run `validate_phase_map.py`, then `keyframe_pipeline.py preview` with at least four repeats, then `validate_motion_continuity.py` using the exact proposed selection and FPS.

If a report fails, inspect the named transition. Retain an in-between frame, replace the incompatible pose, or reject the source video. Do not hide a source defect by reducing the selected frame count.

Complete this step when both proposal reports pass.

## 4. Obtain approval

Show selected filenames and phases, the contact sheet, normal loop GIF, repeated loop GIF, worst-transition sheet, proposal phase report, and proposal motion report. Stop for explicit approval.

After approval, use `keyframe_pipeline.py finalize` to copy the proposal exactly to `selection.json`, then rerun both validators against the final selection filenames.

Complete this skill when final phase and motion reports pass and their hashes match the approved selection.
