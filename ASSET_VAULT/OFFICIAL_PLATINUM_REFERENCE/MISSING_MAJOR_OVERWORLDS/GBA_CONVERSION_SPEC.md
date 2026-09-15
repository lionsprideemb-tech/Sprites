# Platinum → GBA Overworld Conversion Spec

Applies first to: Roark, Gardenia, Candice, Flint.

## Platinum source format

The official `pokeplatinum` field character sheets are:
- indexed PNG
- 16-color source art
- 32 px wide × 512 px tall
- sixteen stacked 32×32 frames
- transparency at palette index 0

The character itself occupies substantially less than the full 32×32 canvas.

## Engine finding: native 32×32 is supported

`pokeemerald` already supports 32×32 object-event graphics with the normal object-event system. Examples in the vanilla source use:
- `.width = 32`
- `.height = 32`
- `gObjectEventBaseOam_32x32`
- `sOamTables_32x32`
- 32×32 frame images

Therefore Mercury does **not** need to compress a Platinum major-character sprite into 16 pixels of width simply to make it compatible with the GBA engine.

### Fidelity-first default for named Sinnoh characters

For major named Sinnoh characters, the preferred first candidate is now:
- keep the Platinum artwork at native 32×32 frame scale
- retain the original indexed palette where technically possible
- reorder the required frames into Emerald's 9-frame walking layout
- use a 288×32 sheet containing nine 32×32 frames
- configure the object event for a 32×32 OAM/subsprite footprint

This is a **format conversion**, not a visual redesign. It preserves Platinum's silhouette and pixel work much more faithfully.

A 16×32 redraw remains available as a fallback when:
- in-engine scale proves visually inconsistent,
- VRAM/palette constraints require it,
- or a specific NPC genuinely benefits from the standard narrow footprint.

Do not choose 16×32 merely because most vanilla Emerald NPCs use it.

## Direction/frame structure

The sixteen Platinum frames resolve as four groups of four:
1. back-facing frames: 0–3
2. front-facing frames: 4–7
3. left-facing frames: 8–11
4. right-facing frames: 12–15

Emerald's standard 9-frame object-event order stores three directions and mirrors west for east.

Source-frame mapping for the 9-frame GBA sheet:
- Front/South idle: 4
- Back/North idle: 0
- Left/West idle: 8
- Front/South walk A: 5
- Front/South walk B: 7
- Back/North walk A: 1
- Back/North walk B: 3
- Left/West walk A: 9
- Left/West walk B: 11

Compact mapping: `[4, 0, 8, 5, 7, 1, 3, 9, 11]`.

The mapping is source-verified against Platinum's generic field-walk setup and Emerald's standard animation table.

## Native-32 technical target

- frame size: 32×32
- frames: 9
- sheet size: 288×32
- 4bpp / maximum 16 colors including transparency
- standard Emerald animation indices 0–8
- east-facing animation produced through horizontal flip of the west-facing frames
- object-event OAM footprint: 32×32
- graphics conversion geometry: 4 tiles wide × 4 tiles high per frame

## 16×32 fallback target

When a narrow redraw is deliberately chosen:
- frame size: 16×32
- frames: 9
- sheet size: 144×32
- preserve aspect ratio; never shrink the whole transparent 32×32 canvas
- use one union crop across all selected poses to avoid animation pumping
- align every pose to one stable foot baseline
- manual pixel cleanup is mandatory after any reduction

## Art and QA rules

1. Platinum is the visual authority for silhouette, costume, hair, pose and major color relationships.
2. No bilinear/bicubic filtering for pixel-art conversion.
3. Keep the final palette at 16 colors maximum including transparency.
4. Preserve a stable foot baseline across the walk cycle.
5. Verify east-facing mirroring in engine.
6. Compare the candidate side-by-side with the actual Platinum source and nearby Mercury NPC scale.
7. Verify palette conversion, transparency, VRAM footprint and object-event alignment in the actual Mercury engine.
8. Do not mark anything `MERCURY_APPROVED` until it passes visual and in-engine QA.

## Current recovery decision

Roark, Gardenia, Candice and Flint should receive **native 32×32 Platinum-format-conversion candidates first**. The automatically reduced 16×32 previews are retained only for comparison and must not be treated as final art.

Status: specification locked for the missing-major-character recovery pass.
