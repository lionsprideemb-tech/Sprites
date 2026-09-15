# Pokémon Mercury Redux — Professional Asset Vault

This directory is the curated art/source library for **Pokémon Mercury Redux**.

## Art-direction goal
Mercury Redux should read visually as a faithful Game Boy Advance interpretation of **Pokémon Platinum / Sinnoh**, not as a collage of unrelated ROM-hack assets.

## Fidelity hierarchy
1. Actual Pokémon Platinum source/reference material.
2. Faithful GBA conversion of Platinum/Sinnoh material.
3. High-quality Sinnoh fan recreation when direct conversion is impractical.
4. Other official GBA assets only when restyled to fit Sinnoh.
5. Hack-original/fan assets only after art-direction review.

## Production pipeline
Every candidate moves through these states:

`REFERENCE -> CANDIDATE -> CONVERTED -> QA -> APPROVED -> IN_GAME`

An asset must **not** be treated as Mercury-ready merely because it exists in this vault.

## Provenance classes
- `OFFICIAL_PLATINUM_REFERENCE`
- `OFFICIAL_GBA_BASE`
- `FAITHFUL_SINNOH_GBA_CONVERSION`
- `FANMADE_SINNOH`
- `ROM_HACK_ORIGINAL`
- `MERCURY_ORIGINAL`
- `UNKNOWN_QUARANTINE`

## Planned library areas
- `01_PLATINUM_REFERENCE/` — maps, map models, textures, UI, characters, battle references, audio references.
- `02_OFFICIAL_GBA_BASE/` — Emerald / FireRed / LeafGreen native GBA assets used as technical references.
- `03_SINNOH_GBA_CONVERSIONS/` — faithful converted Sinnoh assets.
- `04_POKEMON_BATTLE_SPRITES/` — front/back/shiny/icon sets.
- `05_CHARACTERS_TRAINERS/` — trainers, overworlds, NPCs.
- `06_MAPS_TILESETS_BUILDINGS/` — maps, tilesets, buildings, interiors, props.
- `07_UI_FONTS_ICONS/` — menus, Pokédex, fonts, frames, badges, item icons.
- `08_BATTLE_BACKGROUNDS_EFFECTS/` — battle scenes, move effects, weather/field effects.
- `09_AUDIO/` — music/SFX/cries/reference material where redistribution permits.
- `10_FAN_AND_HACK_SOURCES/` — clearly separated non-official assets.
- `90_CONVERSION_QUEUE/` — assets requiring GBA conversion or cleanup.
- `95_QA_QUEUE/` — technically converted assets awaiting review.
- `99_MERCURY_APPROVED/` — protected final masters approved for use in the game.

## Non-negotiable rules
- Preserve original creator/project credit.
- Record the original repository/source and source path.
- Do not silently relabel fan-made material as Platinum material.
- Do not promote an asset to `99_MERCURY_APPROVED` without QA.
- Directly converted Platinum material remains traceable to its exact Platinum source.
- Reference-only material stays reference-only when redistribution rights are unclear.
- Duplicate-looking assets from different sources remain distinct until provenance and hashes are checked.

## Sinnoh environment rule
For important Sinnoh locations and interiors, certification requires evidence from the actual Platinum source whenever that data is available. Similar-looking Emerald/Hoenn layouts, generic Sinnoh-style redraws, or mislabeled donor maps do not count as Platinum-faithful evidence.
