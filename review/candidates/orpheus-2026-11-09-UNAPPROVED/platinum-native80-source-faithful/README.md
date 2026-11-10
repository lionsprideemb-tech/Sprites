# Mercury Redux — clearer native Platinum 80×80 Orpheus family (UNAPPROVED)
Date: 2026-11-10 • **isolated research branch** • not an artwork approval

[**Open actual original / DS64 / native80 visual comparison**](orpheus_platinum_native80_vs_ds64.png)

## Why the 64px cleanup hit a quality ceiling
The earlier experimental pipeline forced Orpheus' 160×160 pixel-art sprites into **64×64**. The native Generation IV Platinum battle-sprite canvas is **80×80**, so the 64px conversion discarded detail unnecessarily. The original Orpheus 160px art is essentially **2× native 80px pixel art**: five of six views have **100%** identical 2×2 RGBA source blocks, and Vibrava BACK has **99.5%** identical 2×2 blocks. Native 80px half-scale is much more faithful to the original art geometry than repeatedly patching the 64px preview.

## Durable unapproved normal front/back assets
Every view has an **80×80 RGBA PNG**, corresponding **3,200-byte DS 8×8-tiled OBJ 4bpp index buffer** and **32-byte, 16-entry BGR555 palette**. All use the existing experimental stage-specific palettes (terracotta/sand Trapinch, sage/turquoise Vibrava, umber/bronze/teal Flygon). The original 160px Orpheus source files and anatomy/poses remain unchanged.

| View | Source 2×2 blocks identical | Preview | DS tiles |
|---|---:|---|---|
| Trapinch FRONT | 100% | [PNG](trapinch_front_half_80.png) | [4bpp](trapinch_front_half_80_4bpp_tiles.bin) |
| Trapinch BACK | 100% | [PNG](trapinch_back_half_80.png) | [4bpp](trapinch_back_half_80_4bpp_tiles.bin) |
| Vibrava FRONT | 100% | [PNG](vibrava_front_half_80.png) | [4bpp](vibrava_front_half_80_4bpp_tiles.bin) |
| Vibrava BACK | **99.5%** | [PNG](vibrava_back_half_80.png) | [4bpp](vibrava_back_half_80_4bpp_tiles.bin) |
| Flygon FRONT | 100% | [PNG](flygon_front_half_80.png) | [4bpp](flygon_front_half_80_4bpp_tiles.bin) |
| Flygon BACK | 100% | [PNG](flygon_back_half_80.png) | [4bpp](flygon_back_half_80_4bpp_tiles.bin) |

**Vibrava BACK caveat:** Some original 2×2 blocks differ in color or transparency; nearest-sample half-scale is therefore **not perfectly lossless** for this view. The 80px preview alpha matches the nearest-sampled 80px source; the original 160px is preserved unmodified.

## Verified source/format checks
- [**Successful native80 GitHub Actions run 42908445599**](https://github.com/lionsprideemb-tech/Sprites/actions/runs/42908445599)
- Original source RAR SHA256 pinned: `72539b83b55a427c4adcdf2f3e5397cc28371875a720f687ffcf4e2a6d803ef9`.
- All six source PNG SHA256 hashes, original 2×2-block measurements, palette SHA256, tile SHA256, dimensions, palette limit and **decode-to-PNG pixel equality** checked.
- [**Machine-readable six-view native80 source-fidelity QA**](native80_selected_half_qa.json)
- Native80 is research-only, not certified game engine archive resources, NCGR/NCLR/NARC, battle/emulator tested, shiny/icon variants or a built ROM.

## Visual result / next action
**Native80 source-derived pixel art is materially clearer than the 64px experiments**, especially Flygon's face and the antenna detail of Vibrava BACK. This is the best current *source-faithful* basis for subsequent targeted polish. If the original complex Flygon pose still looks crowded at 80px, further meaningful improvements require deliberate **native-80 pixel-art re-pixeling**, not another automatic 64px smoothing pass.

**All six images remain UNAPPROVED.** Historical KEEP/CUT votes and original source artwork untouched. No merges to `Sprites/main`, `Mercury-redux-dex`, `platinum-modern-ds`, no changes to regular Flygon/Mega or game type/evolution registrations. User reports artist permission; exact attribution and distribution terms still need documentation.
