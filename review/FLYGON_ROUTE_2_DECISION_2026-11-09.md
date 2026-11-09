# Pokémon Mercury Redux — Flygon Route 2 roster decision (2026-11-09)

## Newer user-directed game roster selection
User selected **Route 2** in the ongoing Flygon sprite conversation and explicitly said to **erase the Electric/Dragon line** from the game plan. This is a **roster supersession**, not a retroactive claim that the user never liked its artwork.

| Game role | Intended content | Current decision |
| --- | --- | --- |
| Vanilla evolution | Trapinch → Vibrava → Flygon | KEEP existing canonical line |
| Vanilla-family Mega | **One Mega Flygon** | KEEP (the archived Elite Redux `flygon-mega` is an approved art candidate; technical integration still requires validation) |
| Separate Delta evolution | Delta Trapinch → Delta Vibrava → **Delta Flygon (Bug/Ground)** | PLAN, awaiting source-specific artwork; do not invent design or assume rejected Redux variants |
| Electric alternate | `flygon-redux-b` | **RETIRED from game roster** |
| Electric alternate Mega | `flygon-redux-b-mega` | **RETIRED from game roster** |
| Delta Mega | None | NOT PLANNED |

**No new custom Delta Pokémon or art has been registered in the playable Pokédex.** The requested Delta Flygon final evolution has **Bug/Ground** typing; earlier evolution-stage typings are still open to matching the chosen designs. The existing normal Flygon family keeps its original typings.

## Avoiding extra species/form clutter
The target game roster is **two three-stage lines and one Mega**, not three lines or multiple Delta Megas. The new line would require at most **three additional Delta species/form identities**, pending a collision-free registry implementation. No additional unrelated Flygon or Mega slots should be created.

## Archived approvals vs current roster choices
The user's original recovered DS art export (2026-10-23) approved `flygon-redux-b` and `flygon-redux-b-mega`, but both are now **excluded for the proposed game**. Their original PNGs, thumbnails, provenance, and historical votes are preserved in the sprite library. Their original KEEP status is *not* a mandate to use those sprites in the ROM.

The same export approved `flygon-mega` from Elite Redux, and also approved an alternate `Mega_Flygon` Design 2 with an unverified back sprite. The two designs do **not** imply two simultaneous Mega Pokémon; the native source-verified `flygon-mega` is the practical baseline candidate pending 4bpp/runtime certification.

Historical rejected `flygon-redux`, `flygon-redux-mega`, `trapinch-redux`, and earlier deleted GBA alternate-family records are still rejected; `vibrava-redux` was undecided. **None are automatically repurposed** as the new Bug/Ground Delta line.

The generic [ER125 Redux-to-Delta map](../ER125_REDUX_TO_DELTA_MAP.csv) predates this explicit decision and must **not** be applied to Flygon/Trapinch/Vibrava without the override.

## Machine-readable source and enforcement
- [Flygon roster plan JSON](flygon-roster-plan-2026-11-09.json) is the newest source-of-truth for this family's *planned game roster*.
- [Flygon roster regression](tests/flygon-roster-plan.cjs) checks original votes and artwork remain intact, excluded Electric variants, single Mega, and missing Delta artwork.
- CI: [sprite-review-integrity.yml](../.github/workflows/sprite-review-integrity.yml).
- This plan **does not certify artwork as game-ready**, insert a ROM sprite, change Pokédex data or allocate new species IDs.
