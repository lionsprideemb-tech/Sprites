# Orpheus Thracean DS64 eye and wing readability review — UNAPPROVED

**[Open source → prior → new contrast-adjusted side-by-side sheet](orpheus_ds64_eye_wing_contrast_before_after.png)**

This is a **second-stage color-contrast experiment** continuing the user's individuality preference. It runs ONLY on the separate `mercury/orpheus-resource-audit-20261109` research branch. GitHub Actions [successful test 42888921831](https://github.com/lionsprideemb-tech/Sprites/actions/runs/42888921831) generated the exact original 160px-vs-prior 64px-vs-refined 64px comparisons.

## Verified native DS64 readability checks

| Sprite | Wing-to-body mean luma contrast before → after | Wing internal before → after | Outline-to-body before → after | Used opaque colors |
|---|---|---|---|---|
| trapinch front | 84.6 → 94.4 | 45.0 → 51.1 | 78.3 → 90.4 | 10/15 |
| trapinch back | 85.8 → 97.8 | 24.1 → 25.6 | 78.6 → 89.9 | 9/15 |
| vibrava front | 58.9 → 62.1 | 78.4 → 86.1 | 80.4 → 88.5 | 10/15 |
| vibrava back | 61.8 → 68.5 | 117.9 → 130.4 | 77.1 → 83.9 | 10/15 |
| flygon front | 78.5 → 98.2 | 76.9 → 98.4 | 57.7 → 56.8 | 10/15 |
| flygon back | 62.8 → 79.9 | 79.3 → 101.4 | 60.7 → 60.6 | 12/15 |

Important: **Luminance separation** is an objective proxy for visual definition; it does not establish human approval or validate eye anatomy. For Flygon, outline-body contrast decreased slightly (less than 1 luminance unit); the larger wing separation increased. Both wing and internal-wing metrics increased in all six views, but some feature labels are broad pixel-class proxies and **Trapinch does not necessarily have literal wings**.

## Mechanism and unaltered assets
- The RGB colors are adjusted only inside each stage's existing terracotta/sand, sage/turquoise, and umber/bronze/teal scheme.
- Pixel art coordinates, palette indices, shape and transparency mask are **bitwise unchanged**. All six original 64px tiles are reused without alteration; each view remains 64×64 with a 2,048-byte DS OBJ tiled pixel buffer.
- Each experimental palette is 16 BGR555 entries (index 0 transparent), 32 bytes, and all preview pixels are verified to decode from tiles/palette.
- Source archive pinned by SHA256 `72539b83b55a427c4adcdf2f3e5397cc28371875a720f687ffcf4e2a6d803ef9`. Original 160px source art, older candidate previews, all 166 iPhone KEEP/CUT votes, main branch, Dex and Platinum ROM untouched.
- Exact facial/eye readability not independently certified; these are contrast-only changes, not manual pixel edits.
- Original Orpheus Flygon remains Bug/Dragon; the separate Mercury target Bug/Ground is not yet game-integrated.
- User reports artist permission, but written attribution/reuse details are not stored.
- No shiny sprites, native NCGR/NCLR/NARC resources or in-emulator rendering are certified; these **are not production-ready**.

**Result:** A safe, source-geometry-exact candidate for visual comparison. All art still needs user selection and additional production readiness checks. **Never auto-promote this experiment into a KEEP decision.**
