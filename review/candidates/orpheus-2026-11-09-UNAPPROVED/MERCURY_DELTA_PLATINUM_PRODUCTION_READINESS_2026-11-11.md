# Mercury Redux — Orpheus Delta Desert Scarab: native Platinum production-preflight handoff
**Date: November 11, 2026.** Technical assets are prepared and verified **in the quarantined Sprites branch only**. **No new custom artwork approval, Dex species/form registration, or Platinum ROM integration.**

## Precise engine requirements confirmed against pret/pokeplatinum

- [Native battle frame constants](https://github.com/pret/pokeplatinum/blob/main/include/constants/graphics.h): **10×10 tiles ×8px = 80×80**. Do **not** ship the 64×64 comparison reductions as a battle-sprite source.
- [Actual battle graphics build](https://github.com/pret/pokeplatinum/blob/main/tools/scripts/make_pl_pokegra.py): source **160×80**, two horizontal 80×80 frames, `nitrogfx -encodefronttoback -scan` and standalone character NCGR. Palettes require `nitrogfx -bitdepth 8 -nopad -comp 10` with correctly CRLF-encoded JASC-PAL.
- [Actual Pokémon icon build](https://github.com/pret/pokeplatinum/blob/main/tools/scripts/make_pl_poke_icon.py): source **32×64**, two vertical 32×32 icon frames, `-clobbersize -version101`; icons use the **shared** 256-color `pl_poke_icon.pal` and palette assignments, not an arbitrary per-species BGR555 bank.
- NCGR/NCLR members alone are **not a completed NARC**, and repeating the same normal sprite for frame 2 is only a **static placeholder**, not original Platinum animation.

## Six normal battle sprite views — technical source completed, all unapproved

| Stage | Normal FRONT | Normal BACK | Artwork |
| --- | --- | --- | --- |
| Delta Trapinch | **80×80** indexed BGR555 + genuine 4bpp + 160×80 two-frame source | same | New desert terracotta/ochre source-silhouette-locked, 9 front + 15 back tiny scute pixels; requires user visual choice |
| Delta Vibrava | same | same | **Exact** previously QA-verified Desert Scarab pixel indices and palette; recommended, not approved |
| Delta Flygon | same | same | **Exact** previously QA-verified Desert Scarab pixel indices and palette; recommended, not approved |

[Complete six-view 80px review](desert-scarab-sixview-g4-preflight/desert_scarab_six_normal_native80_mobile.png) · [six-view exact raw-tile/index and source SHA evidence](desert-scarab-sixview-g4-preflight/preflight_qa.json).

## Genuine upstream NitroGFX NCGR/NCLR pass — 12 character members + 12 palettes

**GitHub Actions [run 43043646189](https://github.com/lionsprideemb-tech/Sprites/actions/runs/43043646189): SUCCESS.** The automated runner built libpng from its public source (Ubuntu apt mirrors were unavailable) and compiled genuine [pret/pokeplatinum NitroGFX](https://github.com/pret/pokeplatinum/tree/main/tools/nitrogfx) source at upstream SHA `62bdaacdca6c56a6a396f3e9911e2f922b79bba8`.

- Normal: **6 NCGR** files of **6,448 bytes** each and **6 NCLR** files of **72 bytes** each, decoded through the **same upstream tool** to the full 160×80 frame strip with **zero indexed-pixel differences**.
- Unapproved shiny palette *proposals*: **6 more NCGR** and **6 more NCLR** files, same exact round-trip verification. These are newly created tentative recolors, not recovered original regional shiny designs and not user-approved.
- Each 160×80 input repeats an identical 80×80 still frame because actual stage animation poses have **not** been authored; one normal and one shiny palette reference same stable pixel index geometry.
- [Exact SHA256 / encoded file list / decoder QA](desert-scarab-sixview-g4-preflight/nitrogfx_qa.json) · [encoded NCGR/NCLR files and preflight sources](desert-scarab-sixview-g4-preflight/) · [six optional normal/shiny comparison](delta-shiny-icon-research/six_shiny_vs_normal_unapproved.png).

**What the upstream encoding proves:** genuine file headers and compression, stage-specific BGR555 palette construction, exact indexed pixel preservation, correct single 80×80 frame region. **What it does not prove:** NARC member order/IDs, additional real animation frames, archive injection, vanilla-vs-Delta form isolation, ROM boot, battle rendering, shiny switching, or licensing/artist-credit requirements.

## Three 32px party icons — source and indexed format candidate, still not game-ready

Three original Orpheus regional icon sheets are **128×64**, each showing two **64×64** original icon frames. All three source sheets are **reversible 2× duplicates**: **2,048/2,048 original 2×2 blocks** for each sheet, and alpha also exact, so **32×32 frames lose no source pixels**.

- Six 32×32 candidate icon frames repacked to the upstream-style **32×64 vertical 4-bit indexed PNG**, true 1,024-byte 4bpp tiled data per 2-frame icon, and per-stage trial palette; 4bpp indices round-trip exactly.
- Stage colors are a **first-pass adaptation** to match selected Trapinch/Vibrava/Flygon Desert Scarab appearances. [Three-icon side-by-side image](delta-icon32-candidates/all_three_icon32_technical_comparison.png) · [per-stage QA](delta-icon32-candidates/icon32_qa.json).
- **Critical remaining block:** icons use individual stage battle-color palettes in this experiment, but the original Platinum icon archive uses a **shared 256-color palette** plus palette assignments. Need deliberate shared-palette color adaptation or a safe engine palette-extension plan, then NitroGFX icon NCGR/NCER/NANR/NARC and actual menu/box/party animation tests. **Do not label these icons game-compatible yet.**

## Approval, rights, roster and integration safeguards

- **No new sprite has a user KEEP vote.** Delta Vibrava and Flygon four normal views are *recommended* after visual review; Trapinch two normal views, all six shiny recolor proposals, and adapted icons remain unapproved.
- User reported permission from the original Orpheus artist; precise attribution, modification, redistribution, and credit details have not been independently recorded.
- Original regular Trapinch→Vibrava→Flygon and one existing approved-art Mega Flygon stay untouched; a **separate** Delta family is planned, with Trapinch and Vibrava including Bug and Flygon specifically **Bug/Ground**. No Electric Redux B imports, no Delta Mega, and no unreviewed species IDs.
- Original Orpheus PBS source has incorrect Trapinch→Flygon and Vibrava→Lycanroc evolution entries. **Never import those links.**
- The immutable original iPhone votes (166 = 154 KEEP + 12 CUT), four newer Wailmer/Wailord/Rainther artwork choices, historical Mega choices, source art, main Sprites reviewer, Mercury-redux-dex, and platinum-modern-ds main remain untouched.

## Remaining gates before a *separate explicitly authorized game-integration release*

1. One final family-wide user visual approval for **the exact six new normal view SHA256 files**, then a separate yes/no for the optional shiny treatment and icon color adaptation; preserve all earlier saved votes.
2. Final true battle animation frames (currently static repeated placeholders), source rights/attribution, and final icon compatible colors including shared-palette check.
3. Register collision-free Delta species/forms, valid evolution graph and data/typing **only after approval**; integrate correctly indexed `pl_pokegra` or `pl_otherpoke`, `pl_poke_icon`, form tables, normal/shiny palettes, and animation/sprite offset metadata.
4. Rebuild Platinum reproducibly and perform battle FRONT/BACK, shiny switching, party/box icon, Pokédex/summary and save/reload **emulator/real-hardware visual validation** before calling these playable.

**Outcome:** Normal six-view art and 12 normal/shiny-proposal character+palette pairs have progressed through **genuine native Platinum graphics encoding** with passing exact indexed readback. Icon art source is provably lossless at 32px. Nonetheless the *entire family is NOT YET integration-authorized or ROM-certified*. All work here is isolated experimental technical preparation.
