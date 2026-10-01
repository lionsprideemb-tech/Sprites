# DS-ready Mega source sweep — 2026-10-01

Primary verified repository candidate: **AxelLoquendo/PokeDot-Engine**

This repository contains dedicated battle-sprite folders for:
- `graphics/pokemon/front`
- `graphics/pokemon/back`
- `graphics/pokemon/front_shiny`
- `graphics/pokemon/back_shiny`
- `graphics/pokemon/icons`

## Missing Mega coverage candidates found

| Mercury audit key | PokeDot battle sprite set | Front | Back | Front shiny | Back shiny | Icon | Status |
|---|---|---:|---:|---:|---:|---:|---|
| crabominable-mega | MEGA_CRABOMINABLE | ✅ | ✅ | ✅ | ✅ | ✅ | COMPLETE SOURCE SET |
| eelektross-mega | MEGA_EELEKTROSS | ✅ | ✅ | ✅ | ✅ | ✅ | COMPLETE SOURCE SET |
| emboar-mega | MEGA_EMBOAR | ✅ | ✅ | ✅ | ✅ | ✅ | COMPLETE SOURCE SET |
| garchomp-mega-z | MEGA_GARCHOMP_Z | ✅ | ✅ | ✅ | ✅ | ✅ | COMPLETE SOURCE SET |
| golurk-mega | MEGA_GOLURK | ✅ | ✅ | ✅ | ✅ | ✅ | COMPLETE SOURCE SET |
| magearna-mega | MEGA_MAGEARNA | ✅ | ✅ | ✅ | ✅ | ✅ | COMPLETE SOURCE SET |
| meowstic-male-mega | MEGA_MEOWSTIC | ✅ | ✅ | ✅ | ✅ | ✅ | COMPLETE SOURCE SET |
| raichu-mega-y | MEGA_RAICHU_Y | ✅ | ✅ | ✅ | ✅ | ✅ | COMPLETE SOURCE SET |
| tatsugiri-curly-mega | MEGA_TATSUGIRI | ✅ | ✅ | ✅ | ✅ | ✅ | COMPLETE SOURCE SET |

## Variant slots still requiring semantic mapping

The PokeDot tree does not expose separately named battle PNG sets for:
- magearna-original-mega
- meowstic-female-mega
- tatsugiri-droopy-mega
- tatsugiri-stretchy-mega

Before treating these as missing artwork, inspect the source form resources to determine whether they intentionally reuse the common Mega sprite set or require palette/form-specific variants.

## Secondary source

**Ghasty001/Animated_sprites_by_Ghasty001** contains an explicit animated Mega Eelektross front and shiny front. Keep as an alternate/native animated DS candidate for comparison.

## Rule

Do not use Mirror Gold documentation PNGs as the first-line source. Prefer battle sprite repositories with explicit front/back/shiny organization.
