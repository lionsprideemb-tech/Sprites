# Orpheus Delta Flygon — deeper real DS64 sprite cleanup (UNAPPROVED)
2026-11-10 | isolated research branch only

**[Open the actual before/after mobile comparison](ds64_stronger_two_view_mobile_review.png)**

This iteration uses the **already committed genuine Orpheus DS64 microfix tiles and PNGs** as the baseline, not AI-generated substitute art. It improves only the **Vibrava back** and **Flygon front** 64×64 indexed graphics with bounded internal color edits.

| View | New edits vs prior microfix | Result PNG | DS 4bpp tiles | BGR555 palette |
|---|---:|---|---|---|
| Vibrava BACK | **24 pixels** | [preview](vibrava_back_stronger64.png) | [2048-byte buffer](vibrava_back_stronger_4bpp_tiles.bin) | [32-byte palette](vibrava_back_stronger_bgr555_palette.bin) |
| Flygon FRONT | **30 pixels** | [preview](flygon_front_stronger64.png) | [2048-byte buffer](flygon_front_stronger_4bpp_tiles.bin) | [32-byte palette](flygon_front_stronger_bgr555_palette.bin) |

**Intended visual refinements:** Vibrava antenna curl and head/wing transition, plus small eye/face and wing-body separation changes in Flygon. These are **source-derived, true indexed-pixel corrections**: no replacement drawings, no pose or silhouette changes, no new palette colors, and no changes to source Orpheus anatomy. The original individual sage/turquoise and umber/bronze/teal color directions are retained.

## Verification
- [GitHub Actions verified run 42900872568](https://github.com/lionsprideemb-tech/Sprites/actions/runs/42900872568): **SUCCESS**.
- Candidate index buffers exactly re-pack into Nintendo DS 8×8 tiled 4bpp, **2048 bytes** each; palettes **32 bytes** each, and decoded pixels match exported PNGs.
- Both original alpha masks and all index-1 outline pixels are identical; original palette bytes are identical.
- Source tiles pinned by SHA256; candidate edits verified as 24 and 30 pixel changes respectively. Full exact coordinate list: [QA JSON](ds64_stronger_two_view_qa.json).
- **Unchanged views:** Trapinch front/back, Vibrava front, Flygon back.
- All original Orpheus source artwork, previous user votes and approvals, main production sprite library and Platinum ROM remain untouched.
- **No automatic approval** and **no ROM integration**. These are review candidates, not final art or completed in-game DS resources. Shinies, icons, NCGR/NCLR/NARC and emulator testing are not covered.
- Artist permission was reported by the user; precise reuse/credit terms should be recorded before distribution.

## Visual caveat
This is a more visible local cleanup than the earlier 5/8-pixel pass, but 64×64 pixel art is inherently blocky at large zoom. The Flygon front face/forewing overlap still contains many original details; completely separating them would require a deliberate redesign or pose-level edit, which is **not authorized** here.

**Review action:** user can judge this stronger version in the mobile sheet. No KEEP/CUT vote is saved unless they explicitly say so.
