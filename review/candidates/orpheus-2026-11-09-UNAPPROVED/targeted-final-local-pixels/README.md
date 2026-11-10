# Orpheus Delta Flygon — final targeted local DS64 detail pass (UNAPPROVED)
_Date: 2026-11-10 • review-branch candidate only_

[**Open the real current-vs-targeted correction sheet**](orpheus_final_targeted_before_after.png)

## Scope and source
This correction starts from the **verified stronger 64×64 Orpheus sprite assets**, not any generated or redrawn art. It changes **only** the indexed color pixels inside the following two normal views; the original artist's source PNGs and the previous stronger variants remain untouched.

| Normal view | Exact newly changed 64px pixels | Candidate PNG | Raw DS 4bpp buffer | Unmodified BGR555 palette |
|---|---:|---|---|---|
| **Flygon FRONT** | 8 | [View](flygon_front_targeted64.png) | [2,048 bytes](flygon_front_4bpp_tiles.bin) | [32 bytes](flygon_front_bgr555_palette.bin) |
| **Vibrava BACK** | 8 | [View](vibrava_back_targeted64.png) | [2,048 bytes](vibrava_back_4bpp_tiles.bin) | [32 bytes](vibrava_back_bgr555_palette.bin) |

The precisely localized changes are:
- **Flygon front**: one dark pupil within the existing pale eye highlight, three connected brown muzzle/neck shadow pixels, and four teal wing-edge pixels at the forewing/body crossing.
- **Vibrava back**: five darker sage antenna-stalk pixels and three sage body/wing-root shade pixels. No antenna outline was moved or grown.

Each original 64×64 pixel stays in the same location; no alpha/transparency or existing outline-index-1 pixel changes. This is **not** a re-pixeling of the entire sprite, and any detail lost from the original 160→64 downscale is not magically recovered.

## Actual source-tile QA
- [**Successful isolated GitHub Actions run 42902915431**](https://github.com/lionsprideemb-tech/Sprites/actions/runs/42902915431)
- **Exact source inputs pinned by SHA256:**
  - Flygon front source buffer: `6b0b955d002f13d0ddaaca20c3c84ddeefd97a2ea7fe5ce1c77ad86e3c1639dc`
  - Vibrava back source buffer: `0e7ed7ea6c96e6884a3195fe4fc0186f69b9e0546e7be0cb75c8e9f949c2c261`
- **Exact output tile SHA256:**
  - Flygon front: `0d906469534f897c50813673ba3473c54173dc975cdaceb93a371e80f6df6d3d`
  - Vibrava back: `5b58eb559e085e08e2da013c804b265a9ecdb8179b84b76e1bc097d8972b301b`
- Each modified PNG is decoded pixel-for-pixel from its **2,048-byte DS OBJ 4bpp tiled buffer** and original **32-byte 16-entry BGR555 palette**.
- Exactly **8 indexed pixel changes per view**; original colors/transparent mask/outline indexes and palette bytes preserved. Full per-coordinate edits, before/after indexes, and SHA evidence are in [machine-readable QA JSON](targeted64_qa.json).
- **The other four views remain untouched:** Trapinch FRONT/BACK, Vibrava FRONT, Flygon BACK.

## Artistic judgment and release boundary
These corrections attempt better eye readability and internal color separation, but they are a **candidate**, not an approved sprite. Real native 64×64 pixel art will still look blocky when enlarged; Flygon's complex face and forewing remain somewhat crowded, and the external DS engine presentation has not been tested.

**No KEEP/CUT votes changed; no original art overwritten; no Pokédex/species/Platinum ROM modifications; no production sprite-library merge; no shiny or engine NCGR/NCLR/NARC certification.** The user reports artist permission but exact artist attribution and permitted distribution terms still need recording before any release.

Next safe step: open the comparison at native 1× and enlarged size, decide whether the **two targeted candidates** look sufficiently clear. Do not create a new approval vote or promote them to ROM automatically.
