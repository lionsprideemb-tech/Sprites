# Missing Major Sinnoh Overworlds — Official Platinum Source of Truth

This folder is **reference metadata only**. It intentionally does not duplicate the original copyrighted Platinum PNGs into this public asset repository.

Canonical source repository: `pret/pokeplatinum`
Pinned source commit: `7a0637607bc070516c20a5bf3a9cd71c76b7a894`

## Official field sprite sources

| Character | Platinum source path | Upstream Git blob SHA | Mercury status |
|---|---|---|---|
| Roark | `res/graphics/field_sprites/npc/roark.png` | `18f22ccbf564a5a10d9898a01ab29126c99301ea` | GBA conversion required |
| Gardenia | `res/graphics/field_sprites/npc/gardenia.png` | `bf6a72f70c76c5794040f878953aafab433d093e` | GBA conversion required |
| Candice | `res/graphics/field_sprites/npc/candice.png` | `dde891edc80d1c0edef7c2fb4451437421f16b9e` | GBA conversion required; HGSS-style candidate remains reference only |
| Flint | `res/graphics/field_sprites/npc/flint.png` | `933d30cbcf4df1b0a34d2d5cffc29fc685bf34e1` | GBA conversion required |

## Why these are authoritative

`pokeplatinum/res/graphics/field_sprites/meson.build` explicitly maps these files into Platinum's field-sprite resource build:
- `npc/roark.png` → `leader1`
- `npc/gardenia.png` → `leader2`
- `npc/candice.png` → `leader6`
- `npc/flint.png` → `bigfour3`

Platinum event data also directly uses the named object graphics. Example: Oreburgh Mine B2F assigns Roark `OBJ_EVENT_GFX_ROARK`.

## Asset policy

These Platinum PNGs are the visual source of truth for reconstruction. Fan-made or HGSS-style overworlds may be kept only as comparison/reference candidates. A Mercury-approved sprite must be derived against these Platinum originals and pass the project art-direction review.
