# Mercury Redux — Final Identity and Missing Family Source Recovery
Date: 2026-10-23

## Scope
Source asset reconciliation, canonical iPhone master reviewer and exception tracking. No changes to the game ROM, Pokédex species IDs, existing KEEP/CUT user votes, selected Mega artwork or other stored image bytes.

## Source-pair recovery (8)
Eight previously unpaired original artworks now have exact original source-pack front/back file links, matching species and generation-specific directory labels. Their PNG signatures, file blob SHAs and canvas dimensions were checked by the connector and are recorded in [source-pair evidence](verified-exception-source-pairs-2026-10-23.json).

- Rainther — original 100×100 and Gen 4 160×160: each original front now has its matching same-folder back. Both correspond to **one Water-type species**; these **two** previously unvoted artwork choices were admitted into the canonical reviewer, and neither is DS-certified.
- Hissiorite, Cobarett, Pythonova — original Gen 3 64×64 front/back pairs recovered. Their *earlier Gen 4 art selections already had user KEEP votes*, so the old Gen 3 alternates remain technical references, without new artwork votes.
- PythonovaS Gen 3 (64×64) and Gen 4-5 (96×96) — paired to explicit `S`-suffix original back images in the matching pack, alongside normal companion files. Classified as **Pythonova shiny artwork, not a new evolutionary species**. Kept outside actionable creative votes and game integration.
- Noctowl `NOCTOWL_1` — matched 96×96 Atsui-package front and back. Treated as a source variant distinct from the published Enjin/Ender Noctowl → Enchantowl graphics; earlier selection of design 2 is preserved.

## Furrva original art
Pokéngine documents original designer **Mikitari**, **Bug** type, creator permission **Free to use with credit**, and a branching evolution graph. Confirmed source-view URLs:
- https://pokengine.b-cdn.net/play/images/mons/fronts/00uc0o89.webp?t=56
- https://pokengine.b-cdn.net/play/images/mons/backs/00uc0o89.webp?t=56
- Authoritative page: https://pokengine.org/mons/00uc0o89/Furrva

The single family reviewer displays both as **external reference previews** with creator credit and no approval button. The credited non-destructive original-byte intake script and workflow are `tools/recover_furrva_source.py` and `.github/workflows/recover-furrva-original-source.yml`. Only after GitHub Actions writes the actual source bytes can the GitHub-hosted copies be considered locally recovered. Source PNGs will still not be DS-certified.

## Five remaining evolution-edge exceptions
These original source names and source files are verified, but pages do **not explicitly establish a complete named family graph**:
- **Hayog, Hogouse, Hogriks** (Scotsman333). Source: https://pokengine.org/mons/00jtq3x2/Hayog, https://pokengine.org/mons/00bspmsd/Hogouse, https://pokengine.org/mons/00jegdpk/Hogriks. Hogriks flavour mentions its Grass typing disappearing through evolution; that is *not* sufficient evidence for the exact two directed species links.
- **Minamai, Marelstorm** (Rattila). Source: https://pokengine.org/mons/00rofohd/Minamai and https://pokengine.org/mons/004bj9kp/Marelstorm. Entries establish identity, typing and source credits, but no explicit direct link.
Both candidate groups remain visually together *without new evolution arrows or ROM changes*. See [the remaining-issues record](identity-family-current-status-2026-10-23.json).

## Reconciliation and gates
- Current reviewer: **158 active choices**, **14 source/technical holds**, **five identity-family warnings**. The previous count of 13 included eight now-resolved source-pair/artwork classification problems.
- The original **166 iPhone votes (154 KEEP, 12 CUT)** are still stored in an unchanged authoritative file. Only two Rainther design alternatives have been added as currently undecided.
- The original 74 previously-approved source pairs and the five missing-shiny repairs are untouched.
- The existing history-aware Python CI scripts were corrected to recognize *only the documented exact source-label corrections and Rainther exceptions*, keeping prior approval and original file gates.
- GitHub Actions run [40038273659](https://github.com/lionsprideemb-tech/Sprites/actions/runs/40038273659) passed the historical master reviewer workflow after these guards were updated. The new Node source-pair verifier passed run [40038050572](https://github.com/lionsprideemb-tech/Sprites/actions/runs/40038050572) before eight-pair assertions were added; check its newest run for the latest assertions.

## Next conditions
Confirm Furrva's actual source-byte intake and committed manifest, inspect source-pair visuals for pose/quality and implement DS palette/atlas conversion separately. Do not silently approve artwork, promote unsure evolutions, copy unrelated Noctowl art, invent missing sprites or integrate unverified species.
