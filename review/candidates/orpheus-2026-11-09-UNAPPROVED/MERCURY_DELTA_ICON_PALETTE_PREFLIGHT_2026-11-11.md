# Mercury Redux — Desert Scarab icon palette production-preflight, November 11, 2026

**Status:** all three Orpheus Delta icon candidates technically converted, **unapproved, not in Platinum**. Research-only Sprites branch `mercury/orpheus-resource-audit-20261109`. Original artwork, previous reviewer decisions, and game repositories unchanged.

## Proven real Platinum format

- The canonical source file [`pret/pokeplatinum/res/pokemon/.shared/pl_poke_icon.pal`](https://github.com/pret/pokeplatinum/blob/main/res/pokemon/.shared/pl_poke_icon.pal) has **256 colors in 16 groups of 16**; only banks **0, 1, 2** contain nonzero colors. Banks 3..15 are zero-filled in this pinned baseline (original palette SHA-256 `028f1b846fd660fac729a37853fcd78d5c0e5ad37e72fecadb908913752cc569`).
- [`tools/scripts/make_pl_poke_icon.py`](https://github.com/pret/pokeplatinum/blob/main/tools/scripts/make_pl_poke_icon.py) encodes an icon using the native NitroGFX flags `-clobbersize -version101`; source canvas is **32×64**: two vertically stacked 32px icons, not six individual raw tile crops.
- All 3 original Orpheus icon sheets downsample from 128×64 to two 32×32 frames with **2048/2048 identical 2×2 source blocks**, so no original pixels are lost at target size. The exact source silhouette/alpha remains fixed.

## Legacy palette-bank candidates, no global palette changes

The initial conservative test remapped each existing Desert Scarab-colored icon to the closest **already populated** global palette bank, ranked by CIE Lab `ΔE76` RMS. All three **real NCGR** outputs returned zero pixel-index differences when decoded by upstream NitroGFX.

| Delta icon | Existing bank | CIE Lab RMS error | Visual weakness |
| --- | ---: | ---: | --- |
| Trapinch | 2 | 13.3238 | Terracotta changes to a flatter medium brown |
| Vibrava | 1 | 14.7090 | Some dark armor becomes gray |
| Flygon | 2 | 19.1814 | Olive-green wings lose their hue and become orange/brown |

[Compare all populated original palette banks](desert-scarab-sixview-g4-preflight/shared-icon-palette/all_three_shared_palette_choices_mobile.png) · [exact native encoder and palette QA](desert-scarab-sixview-g4-preflight/shared_icon_palette_qa.json).

## Better alternative: isolated trial bank 3 (not allocated in game)

Rather than distort the character designs to the limitations of three unrelated existing palette banks, a **separate, unapproved experimental shared palette** is generated with only reserved palette entries **49..63** customized. All original entries **0..48 and 64..255** are byte-identical; the original upstream palette file is never edited. Colors are chosen from real previously verified Desert Scarab icon/battle palettes, using stage-balanced perceptual color fitting across the whole family. This is an *isolated trial file*, not a game palette patch or ID reservation.

| Delta icon | Best existing bank RMS | Trial bank 3 RMS | Technical roundtrip |
| --- | ---: | ---: | --- |
| Trapinch | 13.3238 | **1.1003** | Exact, 0 pixel-index differences |
| Vibrava | 14.7090 | **1.4790** | Exact, 0 pixel-index differences |
| Flygon | 19.1814 | **3.2168** | Exact, 0 pixel-index differences |

Each of the three trial icons has a true **32×64 indexed 4bpp PNG**, **1,024-byte raw tiles**, and native **1,072-byte NitroGFX NCGR**. The experimental global 256-color palette has its own standalone NCLR. All candidate NCGRs were decoded by the real upstream tool with **zero indexed-pixel differences** and unchanged alpha.

[Compare desired icons versus original banks versus reserved bank 3](desert-scarab-sixview-g4-preflight/reserved-bank3-proposal/three_stage_existing_vs_bank3_visual_study.png) · [entire machine-readable bank 3 audit](desert-scarab-sixview-g4-preflight/reserved_icon_bank3_qa.json) · [candidate file folder](desert-scarab-sixview-g4-preflight/reserved-bank3-proposal/).

**GitHub Actions:** [final passing native format + icon preflight run 43089112617](https://github.com/lionsprideemb-tech/Sprites/actions/runs/43089112617). This succeeds independently of the earlier approved-only sprite QA and does not produce a ROM.

## What still blocks production

1. **Artwork approval:** Delta Trapinch normal front/back, four recommended Vibrava/Flygon normals, all proposed shinies, and icon recolors are still user-UNAPPROVED. This source-hash-specific art gate must remain explicit.
2. **Slot/form audit:** Bank 3 is currently zero-filled in the inspected upstream palette, but no full live-form icon palette index collision audit or game-memory palette loading test has been completed. **Do not reserve or insert bank 3 without proof**. Any Platinum modernization engine extension must also be audited for slot conflicts.
3. **Animations:** battle NCGRs are based on duplicated static 80×80 frames; party icons have two authentic Orpheus source frames but no live animation test. Need valid frame sequences, palette behavior and offsets.
4. **Roster:** no Delta form/species ID assigned, no game tables updated. Original regular Trapinch/Vibrava/Flygon and Mega Flygon remain intact; previously incorrect Orpheus PBS evolution links must not be imported. Intended Delta family forms are Bug-typed, with Flygon specifically Bug/Ground.
5. **Runtime:** no new `pl_poke_icon.narc` / `pl_pokegra.narc` members, no executable patch, no Platinum rebuilt or emulator capture. Resolve source attribution/redistribution terms before publishing art.

**Decision:** The experimental bank-3 result is the strongest technical *visual candidate* and preserves the Desert Scarab brown-and-sage identity far more faithfully than forcing existing banks, but **do not promote or integrate it** without explicit user art approval and collision/engine verification.

All **166** original artwork votes and later Wailmer/Wailord/Rainther and Mega decision history remain untouched. No changes to `platinum-modern-ds` or `Mercury-redux-dex`.
