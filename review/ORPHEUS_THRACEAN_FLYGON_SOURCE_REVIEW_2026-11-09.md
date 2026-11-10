# Verified Orpheus / Thracean Flygon family — design-only research (2026-11-09)

The user requested the **actual** Orpheus regional sprite art for review, and **did not authorize approval or integration**. This document is the current exact-source evidence for the Mercury Redux Delta Trapinch/Vibrava/Flygon roster; it does not replace historical source-art votes.

## User-viewable exact sprite previews
- [REGIONAL FAMILY: all 3 original front/back/icon images](https://github.com/lionsprideemb-tech/Sprites/blob/mercury/orpheus-resource-audit-20261109/review/candidates/orpheus-2026-11-09-UNAPPROVED/orpheus_regional_family_actual_pngs.png)
- [VANILLA versus REGIONAL front-sprite sheet](https://github.com/lionsprideemb-tech/Sprites/blob/mercury/orpheus-resource-audit-20261109/review/candidates/orpheus-2026-11-09-UNAPPROVED/orpheus_vanilla_regional_comparison.png)
- [Quarantined source audit README](https://github.com/lionsprideemb-tech/Sprites/blob/mercury/orpheus-resource-audit-20261109/review/candidates/orpheus-2026-11-09-UNAPPROVED/README.md)

All original regional PNG pixels shown in the first sheet were copied unchanged onto display backgrounds; only labels/layout were added. Vanilla comparison source images were nearest-neighbor scaled for side-by-side viewing only. Original Orpheus RAR size: **501,504,299 bytes**, SHA256 `72539b83b55a427c4adcdf2f3e5397cc28371875a720f687ffcf4e2a6d803ef9`.

## Original forms and typings — confirmed from `PBS/pokemonforms.txt` in the RAR

| Original section | Original type 1 | Original type 2 | Mercury fit |
|---|---|---|---|
| `[TRAPINCH,1]` — Thracean | BUG | none | Acceptable typing |
| `[VIBRAVA,1]` — Thracean | BUG | DRAGON | Acceptable typing |
| `[FLYGON,1]` — Thracean | BUG | DRAGON | **Does not yet meet Bug/Ground final requirement** |

The independent Mercury design plan still requires **Delta Flygon = Bug/Ground**. Retyping would be a new game-design decision; do not silently equate source typing with intended Mercury typing.

The original form metadata contains **incorrect evolutions**: `[TRAPINCH,1]` has `Evolutions = FLYGON,Level,25` (skips Vibrava), and `[VIBRAVA,1]` has `Evolutions = LYCANROC,LevelEvening,40` (unrelated species). Therefore the original evolution graph must **not** be imported or treated as reliable despite the presence of all three sprites.

## Exact original sprite file completeness and DS-format limits

| Regional sprite | Source battle front | Back | Regional icon | Front unique RGBA colors including transparency | Back unique RGBA colors |
|---|---|---|---|---:|---:|
| Thracean Trapinch | `Graphics/Battlers/328_1.png` | `328b_1.png` | `Graphics/Icons/icon328_1.png` | 16 | 15 |
| Thracean Vibrava | `329_1.png` | `329b_1.png` | `icon329_1.png` | 25 | 19 |
| Thracean Flygon | `330_1.png` | `330b_1.png` | `icon330_1.png` | 35 | 30 |

Regional battle front/back images are **160×160 RGBA**, regional icon sheets **128×64**; source transparency alpha is binary (0/255). **Not DS64 quality certified.** 4bpp typically needs a maximum of 16 palette entries including transparency, which the Vibrava/Flygon files exceed; downscaling to 64×64 and potentially repalettizing would require a separate *loss and appearance review*. Do not assume original art quality will survive DS conversion.

No confidently identified **regional shiny battle front/back files** were found: original `328s.png`, `329s.png`, `330s.png` exist but are unscoped base-form files, not verified Thracean shiny versions. **The three regional normal-source sets are complete for front/back/icon, not for all required shiny views.**

## Verified original redesign evidence
The original art visibly differs from standard Pokémon: Trapinch has green rounded insect features and yellow antenna-like horns; Vibrava develops long curled antennae and broad yellow wings; Flygon has a larger coiled body, much bigger yellow-green wings and a radically different silhouette. The comparison audit reports low shape overlap with original-source base fronts after normalization (Trapinch 0.151, Vibrava 0.143, Flygon 0.263), and no exact unchanged RGBA art match. These are **morphology redesigns**, not only palette swaps.

The three source art styles fit one another strongly. However, the final design still communicates a winged insect-dragon more immediately than a ground-dwelling creature, so the **Bug/Ground narrative and battle theme need user approval** if chosen.

## Rights / custody
[Resource pack](https://eeveeexpo.com/resources/592/) / [Orpheus original announcement](https://eeveeexpo.com/threads/3565/). Credited game spriters include **Lilly** and **Gray** and regional concept-art contributors are named publicly; the individual creator of these three exact source sprites and reuse permission for Mercury are **not yet verified**. Public sharing of the original resource pack is not an unrestricted license. The source art remains isolated in the dedicated QA branch. The main sprite archive, user votes, Pokédex and ROM remain unchanged.

## QA trail
- [Read-only source-art + PBS visual audit](https://github.com/lionsprideemb-tech/Sprites/actions/runs/42695802925) — **success**; preview PNG and read-only text/JSON were uploaded as an Actions artifact.
- Separate GitHub branch `mercury/orpheus-resource-audit-20261109` contains display-only PNG previews. **No art approved, no integration, no added species IDs and no mutation to existing sprites**.
- Recommended next: user considers actual family as **candidate**, confirms preference and Bug/Ground final retype, requests permission where necessary, then DS-quality prototype for verified sources. Do not perform that prototype without clear source identity and appropriate art rights.


## User update — November 10, 2026: palette preference and permission

User reports they **have the artist's permission** and do **not like the current bright green/yellow palette** on the Thracean family. This is a user-provided permission statement, not an independently examined license document. Before public distribution, record the artist's name/attribution and confirm permission covers recoloring/modification, redistribution, and credit requirements as applicable.

**New direction:** Retain the actual Orpheus original insect-family shapes rather than replacing them with recolors of vanilla Pokémon. Prepare **unapproved alternate palettes** that visually communicate a Bug/Ground final Flygon (suggested research themes: dune sandstone and cocoa, rusty clay and moss, umber and desaturated teal). Recolor the family consistently using native 64×64 source-aligned indexed-palette experiments; do not repaint the silhouette or overwrite original PNGs. This user statement is **not a specific color selection or final art approval**. Keep original source, prior DS64 previews, votes, Dex, and ROM untouched.
