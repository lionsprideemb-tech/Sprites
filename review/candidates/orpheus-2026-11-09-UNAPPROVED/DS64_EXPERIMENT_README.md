# Experimental Orpheus Thracean 64×64 Nintendo DS sprite conversion (UNAPPROVED)

## Visual comparison

[**Open original-to-64px-to-DS-palette quality sheet**](orpheus_ds64_quality_sheet.png)

This sheet was produced from the **original unmodified Thracean** `328_1.png / 328b_1.png`, `329_1.png / 329b_1.png`, `330_1.png / 330b_1.png` in the original Orpheus archive. The original RAR has SHA256 `72539b83b55a427c4adcdf2f3e5397cc28371875a720f687ffcf4e2a6d803ef9`; the source-archive SHA is checked before conversion.

[**GitHub Actions run with 6 pixel previews, raw DS OBJ tile experiments, palettes and JSON metrics**](https://github.com/lionsprideemb-tech/Sprites/actions/runs/42702049107) (download `orpheus-family-DS64-experimental-unapproved` artifact).

## Actual results (front/back source 160×160 RGBA)

| Form | Original 64px opaque RGB colors after size reduction | DS colors including transparency | Irreversible palette merging | Opaque pixels changed by 15-color quantization | Avg channel error including DS 5-bit rounding |
|---|---:|---:|---:|---:|---:|
| Trapinch front | 15 | 16/16 | 0 colors | 0% | 2.282/255 |
| Trapinch back | 14 | 15/16 | 0 colors | 0% | 2.662/255 |
| Vibrava front | 24 | 16/16 | 9 colors | 13.84% | 2.932/255 |
| Vibrava back | 17 | 15/16 | 3 colors | 3.34% | 2.155/255 |
| Flygon front | 34 | 16/16 | 19 colors | 41.84% | 4.229/255 |
| Flygon back | 29 | 16/16 | 14 colors | 16.87% | 3.76/255 |

**Read visual loss correctly:** Merely converting RGB to the DS 5-bit BGR555 palette changes many pixel channel values by 1–4 units, even when no actual color merging is required. The **quantization changed %** metric isolates changes caused by the *additional* 15-opaque-color reduction; it is **0%** for Trapinch, **13.84%/3.34%** for Vibrava, and **41.84%/16.87%** for Flygon (front/back). The Flygon front needs the most scrutiny. All six 2048-byte 8×8-tiled 4bpp pixel buffers and 32-byte palette prototypes passed exact index pack/unpack QA.

The source images were alpha-cropped and nearest-neighbor fit to a 64×64 canvas with a 2px margin. No manual cleanup, invented detail, AI recoloring, nontransparent alpha interpolation, source overwrite, user artwork approval, or engine insertion was performed. **The results are raw hardware-format experiments, not production NCGR/NCLR/NARC resources or emulator-tested ROM sprites.**

- **Trapinch:** crisp silhouette and fairly intact facial detail. No lossy palette merging; moderate inevitable scale loss.
- **Vibrava:** coherent winged silhouette and antennae, modest color merging, some thin antenna/wing pixel loss from shrinking.
- **Flygon:** distinct full-body form but a busy 64px wing/head shape and the largest color reduction. Visually needs deliberate pixel-level cleanup if chosen; do not auto-approve based on passing binary QA.
- **Regional shinies:** not verified from the original Orpheus source; no invented shiny sprite in this experiment.
- **Game typing:** original Thracean Trapinch = Bug, Vibrava = Bug/Dragon, Flygon = Bug/Dragon; Mercury target Flygon would require explicit Bug/Ground game typing.
- **Source ownership:** exact artist credit/license is not established; quarantine remains in effect.

This folder is an **isolated candidate-only research branch**. The `Sprites/main` source library, `Mercury-redux-dex`, `platinum-modern-ds`, historical votes, species registry, and game ROM are unchanged.

Next useful action: visually inspect the 64px sprites, particularly Flygon; decide whether further native-scale cleanup is worthwhile while preserving this candidate's unapproved status.
