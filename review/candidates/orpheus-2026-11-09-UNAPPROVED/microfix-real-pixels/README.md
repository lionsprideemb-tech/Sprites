# Actual Orpheus 64×64 source-pixel microfix — Vibrava back and Flygon front (UNAPPROVED)

**[View the genuine before/after sprite sheet](orpheus_exact_microfix_two_view_before_after.png)**

This is a continuation of the earlier [full family 6-view comparison](../orpheus_delta_family_mobile_review.png), but edits only **two actual DS64 sprite resources**, not an AI-generated image or alternative design. Original sprite pixels are reconstructed from the source-verified Orpheus archive through the existing GitHub Actions pipeline.

**Verified run:** https://github.com/lionsprideemb-tech/Sprites/actions/runs/42898004221

## Two edited 64×64 source-derived sprites

| Sprite | Changed pixels | Result PNG | Raw DS tiles | BGR555 palette |
|---|---:|---|---|---|
| Vibrava back | 5 | [64×64 preview](vibrava_back_manual_microfix64.png) | [2,048-byte tile buffer](vibrava_back_4bpp_tiles.bin) | [32-byte palette](vibrava_back_bgr555_palette.bin) |
| Flygon front | 8 | [64×64 preview](flygon_front_manual_microfix64.png) | [2,048-byte tile buffer](flygon_front_4bpp_tiles.bin) | [32-byte palette](flygon_front_bgr555_palette.bin) |

Exact coordinate edits and original/replacement indexed palette values:

### vibrava_back — 5 manually selected pixels
- `(45, 15)` index 5 → 2, supported by 3/4 original cardinal neighbors; antenna-to-head color seam
- `(34, 36)` index 4 → 2, supported by 4/4 original cardinal neighbors; wing-root body outlier
- `(35, 37)` index 4 → 2, supported by 4/4 original cardinal neighbors; wing-root diagonal outlier
- `(41, 39)` index 3 → 2, supported by 3/4 original cardinal neighbors; underside shade speckle
- `(48, 41)` index 3 → 2, supported by 4/4 original cardinal neighbors; underside shade speckle

### flygon_front — 8 manually selected pixels
- `(27, 15)` index 3 → 5, supported by 4/4 original cardinal neighbors; head and crest color break
- `(30, 20)` index 2 → 3, supported by 4/4 original cardinal neighbors; face-to-neck single-pixel outlier
- `(23, 25)` index 5 → 10, supported by 4/4 original cardinal neighbors; face and forewing crossing
- `(37, 24)` index 5 → 10, supported by 4/4 original cardinal neighbors; forewing/body junction outlier
- `(33, 37)` index 5 → 10, supported by 4/4 original cardinal neighbors; inner wing/body crossing
- `(43, 15)` index 5 → 11, supported by 4/4 original cardinal neighbors; wing membrane noise
- `(41, 19)` index 5 → 11, supported by 4/4 original cardinal neighbors; inner wing membrane noise
- `(51, 24)` index 5 → 11, supported by 4/4 original cardinal neighbors; wing membrane noise


The edits replace only small internal one-pixel color discontinuities where at least **three original neighboring pixels** support the selected new palette index; they do **not** relocate pixels, alter alpha boundaries, enlarge/shrink a limb, create new anatomy, add colors or modify source outlines.

## Verified protections

- Exact source archive identity preserved: SHA256 `72539b83b55a427c4adcdf2f3e5397cc28371875a720f687ffcf4e2a6d803ef9`.
- Original `safepng` source graphics and previous DS64 source/preview graphics untouched.
- DS 4bpp tiles packed and decoded round-trip; 64×64 sprite, fixed 16-entry BGR555 palette (index 0 transparent), no additional colors.
- Both altered sprites have an **identical alpha mask** and outer silhouette to the prior versions, and their original 32-byte palettes are byte-for-byte unchanged.
- **Other four sprite views untouched:** Trapinch front/back, Vibrava front, Flygon back.
- The user's original KEEP/CUT decisions and existing chosen ordinary Flygon/Mega remain untouched. These candidate images have **no KEEP/CUT approval**.
- No Pokédex, species numbers, shiny sprites, engine NCGR/NCLR/NARC or Platinum ROM integration.
- Artist reuse permission was reported by user; exact attribution/distribution terms remain to be documented.

**Important visual limitation:** these are **13 true pixel edits, not a complete 64×64 hand-drawn redraft**. On a large phone zoom, sprites will still look blocky; that is intrinsic to low-resolution pixel artwork. The corrections reduce a few speckles but may be visually subtle. The remaining face/wing crowding in Flygon and thin details in Vibrava cannot be fully resolved by isolated one-pixel substitutions without a more deliberate anatomy-aware 64×64 pixel-art cleanup.

## Next
A focused *artist-level* detail pass on the actual two preview PNGs, with manual silhouette/eye/wing review at 1× and 4× and strict before/after QA, should be **proposed for user review first**. Do not silently promote these changes to a production sprite approval.
