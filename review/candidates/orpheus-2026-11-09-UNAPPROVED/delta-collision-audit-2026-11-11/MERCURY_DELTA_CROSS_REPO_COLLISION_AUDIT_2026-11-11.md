# Mercury Redux — Delta Trapinch / Vibrava / Flygon collision audit

**November 11, 2026 • Read-only game/Dex inspection • Six active integration blockers**

This report references [exact, machine-verified cross-repository QA](delta_form_id_icon_palette_evolution_readonly_QA.json) produced by [GitHub Actions run 43092226916](https://github.com/lionsprideemb-tech/Sprites/actions/runs/43092226916). The auditor uses pinned shallow, sparse, **read-only GitHub clones**, unpacks **all 17 NextDex shards plus 12 sequential overlays**, and reproduces the deployed site's `app.js::applySourceOverlay` rules. Its only published outputs are QA files in this **isolated Sprites research branch**. It did not edit `Mercury-redux-dex`, `platinum-modern-ds`, the standard Pokémon data, or any user vote.

## Pinned evidence / unchanged approvals

| Actual source | Inspected main commit |
| --- | --- |
| [Sprites main](https://github.com/lionsprideemb-tech/Sprites/tree/f15c4671bf7afb15450fc7801bde17aefcdc4f7e) | `f15c4671bf7a` |
| [Mercury-redux-dex main](https://github.com/lionsprideemb-tech/Mercury-redux-dex/tree/faa7cb4016d8030fb4661b49114352d79cac7944) | `faa7cb4016d8` |
| [platinum-modern-ds main](https://github.com/lionsprideemb-tech/platinum-modern-ds/tree/5525e961a1fb98c62bd53bc4a27b0276a39f6719) | `5525e961a1fb` |
| [pret/pokeplatinum upstream](https://github.com/pret/pokeplatinum/tree/62bdaacdca6c56a6a396f3e9911e2f922b79bba8) | `62bdaacdca6c` |

The **166 original user decisions remain exactly 154 KEEP / 12 CUT**, original file Git blob SHA `61c5e53c6ec81b74d192cd62a4c52c970cea15ce`; separate finalized Wailmer/Wailord/Rainther decisions remain protected by SHA `89f328b4471f1531520305e54f63efdbc6251a50`. Protected Flygon Route 2 planning file SHA `e2c29dcbb27c5354f00a594a9ffbb466cc962e85`. Four Vibrava/Flygon Desert Scarab views remain **recommended**, not approved; new Trapinch normal, shiny options, icon options unapproved. No original sprite, icon palette, Pokédex record or ROM file changed.

## ID and form allocation: **BLOCKED**

- [Platinum canonical registry](https://github.com/lionsprideemb-tech/platinum-modern-ds/blob/5525e961a1fb98c62bd53bc4a27b0276a39f6719/data/canonical_species_1025.txt) has **1,025 unique canonical base species**, assigned IDs **1–1025**. Original Trapinch, Vibrava, Flygon are precisely IDs **328, 329, 330**.
- [Planned internal map](https://github.com/lionsprideemb-tech/platinum-modern-ds/blob/5525e961a1fb98c62bd53bc4a27b0276a39f6719/tools/build_ds_species_id_map.py) assigns **NONE 0; EGG 1026; BAD_EGG 1027** after the 1,025 canonical base species. These are reserved **sentinels**, not Delta slots.
- No `SPECIES_*DELTA*TRAPINCH`, `VIBRAVA`, `FLYGON`, or older Redux variants are allocated as new active production constants in the inspected Platinum overlays and canonical registry. Neither three fresh species IDs nor form ID 1 on each original has been authorized or collision-checked.
- The [live Dex metadata](https://github.com/lionsprideemb-tech/Mercury-redux-dex/blob/faa7cb4016d8030fb4661b49114352d79cac7944/data/pokedex/index.json) resolves to **1,599 effective entries**: 1,603 source-shard entries minus four removed entries, after all 12 overlay passes. Its **website numeric IDs** include values up to **2208** and are **not verified direct Platinum runtime species IDs**. Do not allocate 1028–1030 merely because they follow the sentinels.
- **Actual stale-roster conflict:** the newer approved Route 2 scope retires the Electric/Dragon Flygon Redux B and its Mega, but **both still appear in the effective Dex**: `R0494 / SPECIES_FLYGON_REDUX_B / site ID 2081` and `R0496 / SPECIES_FLYGON_REDUX_B_MEGA / site ID 2082`. They must be excluded from the **future playable roster**, not silently imported. The audit did **not** remove their historic Dex cards or votes.
- **Three repeated website-ID groups need classification:** ID **1581** (`R0077` and `R0078`, both Arcanine Mega), **1751** (`R0901` and `R0902`, both Toxtricity Mega), **1761** (`R0737` and `R0738`, both Reuniclus Redux Mega). These may represent intentionally duplicated form cards. **Do not call them proven native game collisions**; reconcile their site-identity meaning before any site-ID-to-game mapping.

**Decision held:** three proposed Delta entries should remain an **unassigned** separate family pending choice of real separate species vs extended forms. The saved Pokémon form field is **5 bits (values 0–31)**, but that alone does not implement a distinct Delta identity; save, battle, evolution, icons, trading, and form sanitization must agree.

## Icon palette bank 3: source-space free, **runtime not certified**

The actual upstream [256-color Pokémon icon palette](https://github.com/pret/pokeplatinum/blob/62bdaacdca6c56a6a396f3e9911e2f922b79bba8/res/pokemon/.shared/pl_poke_icon.pal) has 16 16-color banks. All entries of bank 3 (global indices 48–63) are **zero in the original file**. Exhaustive inspection of upstream species/form `data.json` icon-palette bindings found **540 metadata bindings**, all to banks **0, 1, or 2** (counts **265 / 120 / 155**); **zero** currently refer to index 3.

This confirms bank 3 is **unused by the inspected upstream icon metadata**, **not** that the Mercury-custom engine or VRAM has a collision-free slot. Three unapproved Desert Scarab bank-3 sprites and a separate trial NCLR passed the genuine native encoder/decoder with **zero pixel-index differences**, while original shared palette and existing banks are untouched. [QA](../desert-scarab-sixview-g4-preflight/reserved_icon_bank3_qa.json) · [visual comparison](../desert-scarab-sixview-g4-preflight/reserved-bank3-proposal/three_stage_existing_vs_bank3_visual_study.png).

Concrete routing blockers from [`src/pokemon_icon.c`](https://github.com/pret/pokeplatinum/blob/62bdaacdca6c56a6a396f3e9911e2f922b79bba8/src/pokemon_icon.c): the icon-sprite function, box form-offset function and palette-index function explicitly branch on a small set of **vanilla form families**, but **not** Trapinch, Vibrava or Flygon. Without added logic a Delta form could show the **ordinary icon and ordinary palette** even if custom NCGR art exists. `PokeIconPaletteIndex` has no new Delta-specific bank-3 route.

Other screens use different icon palette slots: [PC boxes](https://github.com/pret/pokeplatinum/blob/62bdaacdca6c56a6a396f3e9911e2f922b79bba8/src/applications/pc_boxes/icon_helper.c) select normal slot **2 + palette index** and selected slot **6 + palette index**; [party menu](https://github.com/pret/pokeplatinum/blob/62bdaacdca6c56a6a396f3e9911e2f922b79bba8/src/applications/party_menu/sprites.c) uses **3 + palette index**. Bank 3 would therefore use PC slots **5 / 9** and party slot **6**, whose interaction with existing screen palette resources must be tested in-game. This is an **unresolved potential collision**, not proven safe or proven broken. No shared palette changes have been applied.

## Evolution integrity: normal line verified; Delta levels NOT decided

- Upstream **ordinary Trapinch**: `EVO_LEVEL 35 → SPECIES_VIBRAVA`, Ground.
- Upstream **ordinary Vibrava**: `EVO_LEVEL 45 → SPECIES_FLYGON`, Ground/Dragon.
- Ordinary Flygon is Ground/Dragon with no further ordinary evolution. All three original species/IDs, moves, typing, abilities and Mega planning remain untouched.
- The **separate Delta progression** is designed as `Delta Trapinch → Delta Vibrava → Delta Flygon`, with Bug required on the two earlier stages and **Bug/Ground** required on the final Flygon. Secondary typing for the two younger stages and exact Delta evolution levels/methods have **not** been explicitly selected, so the normal 35/45 progression is **not automatically a Delta rule**.
- The original Orpheus data had incorrect Trapinch→Flygon and Vibrava→Lycanroc graph edges; importing that graph is explicitly forbidden. The saved [Flygon integration guard](https://github.com/lionsprideemb-tech/platinum-modern-ds/blob/5525e961a1fb98c62bd53bc4a27b0276a39f6719/docs/FLYGON_ROUTE_2_INTEGRATION_GUARD_2026-11-09.md) supersedes older Redux-to-Delta mapping drafts. Preserve **one regular Mega Flygon**, **no Delta Mega**, and **no Electric Redux B family in playable roster**.

## Six exact blockers preventing ROM integration

1. **ID-01:** No validated three-slot Delta species or form ID allocation; canonical IDs and Egg sentinels are protected.
2. **ID-02:** Dex/engine mapping is not reconciled; two retired Electric Redux B identities remain live Dex entries, plus three repeated website numeric-ID groups of uncertain meaning.
3. **FORM-03:** Core icon/form code needs Delta identity routing and full save/summary/battle/PC/party tests.
4. **ICON-04:** Bank 3 is empty *upstream* but not safely registered/loaded for the actual modernized engine; sprite routing and screen palette VRAM must be verified.
5. **EVO-05:** No explicitly selected Delta levels, methods or initial-stage secondary types; no independent valid Delta graph installed.
6. **ART-06:** No user approval for the new normal/shiny/icon artwork, and current 160×80 battle sources repeat a **static** frame; complete animation and ROM/emulator tests still required.

**Next gated release:** First reconcile the custom roster and choose the Delta representation. Without touching game code, produce a provisional collision-free mapping proposal, then seek explicit artwork and gameplay/type/evolution approval before any staged runtime implementation. Verify bank-3 routing and VRAM in isolated emulator tests after that; never overwrite the approved 166 votes or ordinary Flygon resources.

**No approvals, species IDs, form mappings, data, or Platinum/NexDex artifacts were changed in this release.**
