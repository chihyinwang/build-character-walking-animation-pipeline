# Provider-neutral walk-video prompt

Use the approved directional character anchor as the only image reference.

```text
Create a short image-to-video clip from this exact approved character anchor.

Subject: preserve the same character identity, body proportions, face, hairstyle, clothing, palette, silhouette, and anatomical-side details.
Facing: keep the character facing {DIRECTION} for the entire clip.
Motion: perform a natural in-place walk cycle. Alternate the legs clearly and use opposing arm swing. Keep both hands free unless the character specification explicitly requires otherwise.
Position: keep the character centred. Do not travel across the frame.
Camera: fixed camera, fixed framing, fixed zoom, fixed perspective, and no rotation.
Continuity: stable scale and anatomy, coherent leg tracks through occlusion, no limb swaps, limb teleportation, pose snapping, freeze, or stutter.
Style: preserve the input image's rendering style and hard-edged silhouette. Avoid motion blur and painterly interpolation.
Background: preserve the input background as a flat, uniform field.
Composition: one complete full-body character only, with no floor, cast shadow, text, interface, or new object.
```

Recommended baseline:

- 4–6 seconds;
- the generator's highest practical resolution;
- one stationary full-body character;
- no repeated endpoint requirement, because loop construction happens during keyframe selection.
