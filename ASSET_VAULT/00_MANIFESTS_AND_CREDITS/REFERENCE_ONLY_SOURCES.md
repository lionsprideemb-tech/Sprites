# Reference-Only Sources

These sources may be useful for visual comparison, reconstruction research, or cross-checking, but their assets must **not** be copied into the Mercury vault unless redistribution/usage is separately cleared.

## knightdx91-alt/Pokemon-Game — Sinnoh 3D map renders/extractions

Status: **REFERENCE_ONLY**

Why useful:
- repository documents a complete Platinum/Sinnoh 3D extraction pipeline
- reports 533 Sinnoh maps under `assets_3d/sinnoh/`
- includes Platinum map-header/matrix/land resolver tooling and top-down render tooling
- can be used as an independent visual cross-check when validating Mercury map conversions

Why not an import source:
- the repository's own `3D_MAPS_HANDOFF.md` states the region assets were extracted from the user's ROMs
- ROM bytes are intentionally not committed, but the derived assets remain ROM-derived
- no general repository-level redistribution license was identified during this intake pass

Mercury policy:
- prefer `pret/pokeplatinum` source/decomp resources as the authoritative Platinum reference
- use this repository only to compare geometry/render interpretation when it helps verify a conversion
- do not promote copied material from this source into `MERCURY_APPROVED`

Repository: `knightdx91-alt/Pokemon-Game`
Reviewed: 2026-09-15
