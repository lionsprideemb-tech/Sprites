# Platinum → GBA Overworld Conversion Spec

Applies first to: Roark, Gardenia, Candice, Flint.

## Platinum source format

The official `pokeplatinum` field character sheets are:
- indexed PNG
- 16-color source art
- 32 px wide × 512 px tall
- sixteen stacked 32×32 frames
- transparency at palette index 0

The character itself occupies substantially less than the full 32×32 canvas, so the correct conversion is **not** to scale a DS screenshot or resize the entire 32×32 frame.

## Direction/frame structure

The sixteen Platinum frames resolve as four groups of four:
1. back-facing frames: 0–3
2. front-facing frames: 4–7
3. left-facing frames: 8–11
4. right-facing frames: 12–15

For an Emerald-style 9-frame overworld sheet, retain one neutral and two walk-step frames for the three stored directions. Right-facing can be mirrored in-engine from the left-facing frames where appropriate.

Working source-frame mapping for the 9-frame GBA sheet:
- Front idle: 4
- Back idle: 0
- Left idle: 8
- Front walk A: 5
- Front walk B: 7
- Back walk A: 1
- Back walk B: 3
- Left walk A: 9
- Left walk B: 11

This mapping must be visually verified per character before final approval.

## Pixel-art conversion rules

1. Crop to the visible character bounds inside each 32×32 source frame; never resize the transparent outer canvas.
2. Preserve the Platinum silhouette, costume details, hair shape, and major color relationships.
3. Target Emerald-compatible 16×32 frames where the character can be represented cleanly. If an essential silhouette cannot survive at 16 px width, use a justified 32×32 object-event footprint rather than mutilating the design.
4. Keep the final palette at 16 colors maximum including transparency.
5. Prefer manual pixel cleanup after reduction. No bilinear/bicubic filtering.
6. Align all frames to a consistent foot baseline to prevent walking jitter.
7. Preserve head/body scale across idle and step frames; do not resize each pose independently in a way that causes animation pumping.
8. Compare final conversions side-by-side against the actual Platinum source and against already accepted Mercury Sinnoh overworld scale.
9. Do not mark a conversion `MERCURY_APPROVED` until it passes palette, transparency, silhouette, animation, and in-engine movement checks.

## Existing conversion comparison

The current Team Aqua-style GBA candidates use 144×32 sheets representing nine 16×32 frames. They are useful as a format/scale comparison, but Platinum remains the authority for character appearance.

Status: specification locked for the missing-major-character recovery pass.
