# Mercury Native DS Sprite Source Collection — Frozen Intake

Status: **SOURCE COLLECTION COMPLETE TO PUBLICLY RECOVERABLE ASSETS**

## Strict master snapshot

- Actual image asset files in current repository audit: **31,240**
- Exact-unique image hashes: **25,228**
- Exact duplicate copies: **6,012**
- Generic/native-source assets: **28,830**
- Hack-native/source assets: **2,410**
- Rule: links, patch files, documentation-only entries, banners, screenshots, and preview-only images do not count as collected sprites.

## Major collected source groups

- DrPrettyman DS 64x64 library
- hg-engine sprite tree
- DS-Styled Gen 5–8 compilation
- Gen 7 DS backsprites
- Shiny Icons Gen 1–9
- Fakemon Festival full + individual creator packs
- Mikitari
- Earthretha
- Mega Flygon + animated Mega Flygon
- Platinum Redux embedded assets
- Banished Platinum Mega assets
- SoothingSilver embedded assets
- Altered Platinum recovered sprite assets
- Infinite Black 2 unique assets
- Platinum Unlocked shiny/recolor assets
- HGSS-project unique asset buckets

## Unresolved / partial exceptions

### Pokemon XYZ NDS
Status: **KNOWN_SPRITE_SOURCE_UNRECOVERED**
Public thread exposes named attachments, but PokéCommunity protection blocks the attachment bytes.

### Pokemon GoldSoul
Status: **KNOWN_SPRITE_SOURCE_UNRECOVERED**
Public project references were found, but no recoverable loose sprite media was exposed by the current public endpoints.

### Pokemon Moon Black 2
Status: **KNOWN_SPRITE_SOURCE_UNRECOVERED**
The project is known to contain custom/replacement sprites, but no loose public sprite bytes were recovered.

### Pokemon Platinum Unlocked
Status: **PARTIAL**
447 shiny/recolor assets were collected. Regional-form design sprites remain separately unverified and are not assumed collected.

### Project 721
Status: **RECOVERABLE_BUT_NOT_STAGED**
A recovery runner identified 14 sprite-like images, but the source job lost a concurrent push race before those files landed on main. Because Project 721 largely uses Showdown-derived assets and is lower-value for unique Mercury concepts, intake is frozen without counting those runner-only files.

## Next pipeline stage

1. Build species/form/design normalized inventory.
2. Compare the native-DS library against Mercury's GBA/custom library.
3. Collapse exact duplicates and obvious same-source mirrors.
4. Identify:
   - direct DS replacements,
   - alternate DS renditions of the same design,
   - recolors,
   - genuinely distinct concepts,
   - GBA-only designs requiring conversion,
   - Mercury-original bad sources requiring native NDS rebuild.
5. Generate visual approval sheets.
6. Do **not** integrate anything into hg-engine until user visual approval.

This file freezes the source-intake phase. New sources may still be added later if discovered, but they are no longer a prerequisite for beginning the overlap comparison.
