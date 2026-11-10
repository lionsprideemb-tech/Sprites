# Orpheus Thracean family: palette-only 64×64 DS quality refinement (UNAPPROVED)

**Review image:** [actual source vs baseline vs 64×64 palette refinement](orpheus_ds64_palette_refinement_before_after.png)

**Original quality-check run:** https://github.com/lionsprideemb-tech/Sprites/actions/runs/42875145728
**Final preview reproduction (checks successful):** https://github.com/lionsprideemb-tech/Sprites/actions/runs/42875394450

This is a **technical quality experiment only** in the isolated `mercury/orpheus-resource-audit-20261109` branch. None of the archived source PNGs was changed. The official Mercury game, normal Trapinch line, regular Mega Flygon, earlier artwork decisions, Pokédex data, and ROM were **not** changed. New visual drafts remain **unapproved**.

## Results verified from source-pinned CI

All 4 Vibrava/Flygon front/back experimental 64×64 silhouettes are **pixel-for-pixel identical** to the original experiment (same 64×64 resizing, transparency masks and placement). Only 15-color BGR555 color assignments were refined; colors are drawn solely from the original source art after DS 5-bit rounding, with no added or painted pixel details.

| View | Baseline mean RGB error /255 | Refined /255 | Reduction | Baseline luminance edge error | Refined |
|---|---:|---:|---:|---:|---:|
| vibrava front | 2.932 | 2.273 | 22.5% | 1.759 | 1.128 |
| vibrava back | 2.155 | 2.073 | 3.8% | 1.010 | 0.972 |
| flygon front | 4.229 | 2.654 | 37.2% | 2.752 | 1.812 |
| flygon back | 3.760 | 2.960 | 21.3% | 1.731 | 1.210 |

**Caveats:** Error reductions are measured against the *existing unrestricted 64px downscaled original*, not a human preference survey or a claim that fine details lost during scaling have been restored. Visual quality is still limited by the 160→64 resolution reduction. Some colors have merged to fit ≤15 opaque palette slots. The 64px antialiasing/shape is not invented; both comparisons use nearest-neighbor rendering.

## Safeguards
- **Six original Orpheus regional 160px front/back files:** unchanged.
- **Trapinch front/back:** unchanged in this refinement because the earlier experiment already fits the DS color budget.
- **All 4 refined files:** 64×64; source transparency mask identical; each has a verified 2,048-byte DS OBJ 4bpp tiled pixel buffer and 32-byte 16-entry BGR555 palette in the Actions artifact, with decode matching the exact preview.
- These are **raw hardware-compatible tile/palette experiments, not Nintendo NCGR/NCLR/NARC files and not a playable Platinum test**.
- Original Thracean Flygon is **Bug/Dragon**; Mercury would require a separately approved **Bug/Ground** type choice. Do not make this change without approval.
- **Regional shiny sprites:** not verified; not produced.
- Artist-specific permission to import the original Orpheus artwork remains unverified. Source artwork is therefore research-only.
- No exact design approval, species-ID insertion, Dex entry, or ROM integration has occurred.

**Suggested next test:** review 64×64 visual details and isolate any remaining wing/face pixel clarity defects for careful manual art-source-aware cleanup. No artwork approval should be inferred from improved error scores.

