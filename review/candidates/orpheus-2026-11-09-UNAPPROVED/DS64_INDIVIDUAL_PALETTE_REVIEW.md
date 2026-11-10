# Stage-individual Delta Flygon palette concepts — unapproved (2026-11-10)

**[View full-size actual 160px original → previous DS64 → new stage-specific 64×64 recolors](orpheus_thracean_individual_delta_recolors.png)**

Source: original Orpheus Thracean family PNGs from the public archive SHA256 `72539b83b55a427c4adcdf2f3e5397cc28371875a720f687ffcf4e2a6d803ef9`.
**Verification:** [GitHub Actions experimental recolor run](https://github.com/lionsprideemb-tech/Sprites/actions/runs/42879319371).

## Art direction (not selected)
- **Delta Trapinch:** terracotta/orange/sand, retains small insect-burrower silhouette.
- **Delta Vibrava:** sage-green body + turquoise-blue wings, retains lean antennaed insect silhouette.
- **Delta Flygon:** umber-brown mature body + bronze and teal accents/wings, retains source head/wing/body anatomy.
- Each stage has a **different 15-color palette** (with transparency as 16th entry) so the family has evolutionary individuality, not one shared monotone treatment.

## Exact six-view checks

| Stage | View | Opaque colors actually displayed | 64×64 alpha geometry identical | 4bpp tile bytes | BGR555 palette bytes |
|---|---|---:|---|---:|---:|
| trapinch | front | 10/15 | YES | 2048 | 32 |
| trapinch | back | 9/15 | YES | 2048 | 32 |
| vibrava | front | 10/15 | YES | 2048 | 32 |
| vibrava | back | 10/15 | YES | 2048 | 32 |
| flygon | front | 10/15 | YES | 2048 | 32 |
| flygon | back | 12/15 | YES | 2048 | 32 |

- Source 160×160 original PNGs and previous 64px experiments remain **untouched**.
- The same previous-experiment **64×64 pixel positions and transparency** are preserved. Only source-mapped color indices change; new colors are an intentional palette-design proposal rather than an objective source-fidelity optimization.
- All six graphics pass **native 8×8-tiled DS OBJ 4bpp pack/decode**, 2,048 bytes per view, 16-color BGR555 palette exactly 32 bytes.
- The screenshots, separate front/back PNGs, tile buffers and JSON report are in the [GitHub Actions artifact](https://github.com/lionsprideemb-tech/Sprites/actions/runs/42879319371) under `orpheus-family-DS64-individual-colors-unapproved`.
- **Source artist permission reported by user**; exact artist and distribution/credit terms not independently documented in this repository.
- **Shinies and engine archive packaging** are not done, and no playable ROM test or species entry occurred.
- **Typings from source:** Trapinch Bug; Vibrava Bug/Dragon; Flygon Bug/Dragon. The user desires final Delta Flygon **Bug/Ground**, but that game typing has not been integrated.
- **Approval status:** no artwork approval, no historical vote rewriting, no production sprite imports, no ROM changes. This report and PNG live only on the isolated review branch.

For the next step, visually assess whether the individual palettes are appealing and whether any wing or eye region needs palette-only adjustment. Preserve user choice, no automatic approvals.
