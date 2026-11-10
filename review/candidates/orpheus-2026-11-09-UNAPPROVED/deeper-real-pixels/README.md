# Mercury Redux / Orpheus Thracean — deeper native DS64 pixel-art readability pass

**STATUS: experimental working candidates — NOT APPROVED, NOT INTEGRATED.**

[**Open the real 64×64 before-and-after mobile comparison**](orpheus_two_sprite_deeper_mobile_review.png)

This work uses the **previously committed, source-verifiable 64×64 Orpheus sprite PNGs and indexed DS OBJ tile buffers** as input. It does not generate substitute illustrations or change the original artwork, and does not merge anything into the production sprite library.

## Actual two-view sprite assets

| Stage | Prior verified experimental source | Proposed revised normal view | Palette + 4bpp tile files | Additional index changes |
|---|---|---|---|---:|
| Vibrava BACK | [Previous microfix](../microfix-real-pixels/vibrava_back_manual_microfix64.png) | [64×64 revised PNG](vibrava_back_refined64.png) | [4bpp tiles](vibrava_back_4bpp_tiles.bin) + [BGR555 palette](vibrava_back_bgr555_palette.bin) | **24** |
| Flygon FRONT | [Previous microfix](../microfix-real-pixels/flygon_front_manual_microfix64.png) | [64×64 revised PNG](flygon_front_refined64.png) | [4bpp tiles](flygon_front_4bpp_tiles.bin) + [BGR555 palette](flygon_front_bgr555_palette.bin) | **30** |

The new changes emphasize details within the existing source-derived 64px shapes: Vibrava's antenna curvature and eye region, and Flygon's eye/face shading and the separation between body and wing membranes. The individual stage color identities remain **sage/turquoise** and **umber/bronze/teal** respectively. The source original Trapinch, Vibrava and Flygon anatomical poses have not been redrawn.

### Technical checks

- CI: [Successful GitHub Actions run #42901153191](https://github.com/lionsprideemb-tech/Sprites/actions/runs/42901153191) (artifact `orpheus-family-DS64-deeper-mobile-qa-unapproved`).
- **54 real color-index pixel changes** since the previous microfix, restricted to the two specified views. The actual per-coordinate differences are in [readability_qa_manifest.json](readability_qa_manifest.json).
- Each view remains **64×64**, with exact unchanged exterior sprite silhouette and binary alpha map. Transparent pixels and indexed outline pixels are unchanged.
- The **original palette data is byte-for-byte identical** to the prior 32-byte, 16-entry BGR555 palette (index 0 reserved transparent), with at most 15 opaque colors displayed.
- Each revised DS OBJ 4bpp sprite is **2,048 bytes** of 8×8 tiles; exact index decode reconstructs the committed PNG and passes pixel-level roundtrip checks.
- Unchanged views: **Trapinch front, Trapinch back, Vibrava front, Flygon back.** Historical iPhone votes and any unrelated source artwork are untouched.
- **No** new source imports, Dex records, shaders, ROM changes, compilation or game-engine NARC integration; **no creative artwork approval** recorded.

### Cautions

This is a **more substantial local pixel-color cleanup**, not a replacement drawn from scratch. 64×64 art necessarily has visible pixel blocks. The original Orpheus Flygon's type is Bug/Dragon; Mercury's intended separate Delta Flygon type is Bug/Ground, which is not yet implemented. No regional shiny sprites or emulator rendering were certified, and artist credits and reuse scope should be recorded before distribution (user states they have permission).

**User design review remains necessary** before these are accepted. The next practical choice is whether this real pixel-art cleanup is visually acceptable at native 1× size, or whether the two views need a larger deliberate DS-scale re-pixeling that changes more than just local indices.
