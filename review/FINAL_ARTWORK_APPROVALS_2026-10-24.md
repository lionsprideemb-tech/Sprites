# Pokémon Mercury Redux — Final Four Artwork Approvals (2026-10-24)

## Verified source-specific creative decisions

The user explicitly submitted these **artwork choices** for the existing canonical GitHub reviewer:

| Exact reviewer ID | User choice | Source |
|---|---|---|
| `reconcile:wailmer-alternate-form-1` | **KEEP** | Original Reborn / Plates of Arceus alternate Wailmer front/back |
| `reconcile:wailord-alternate-form-1` | **KEEP** | Original Reborn / Plates of Arceus alternate Wailord front/back |
| `compare:rainther:1` | **CUT this competing art** | Festival_Magiscarf original battler front/back |
| `compare:rainther:2` | **KEEP** | Festival_Magiscarf Gen 4 Rainther front/back |

**“CUT Rainther Design 1” does not remove the species or its remaining accepted Gen 4 design.** No shiny artwork is implied, and KEEP does not certify native DS rendering.

All four are append-only approvals in [`final-artwork-approval-overlay-2026-10-24.json`](final-artwork-approval-overlay-2026-10-24.json). Their original paths and exact source PNG Git blob hashes are pinned and checked in GitHub CI.

## Historical Mega choices: user's most recent stored decisions win

The user explicitly directed us to honor the latest previously saved iPhone votes over the conflicting older exports:

| Exact design | Final confirmed vote |
|---|---|
| Mega Lucario Z — DrPrettyman DS Design 1 | CUT |
| Mega Lucario Z — Elite Redux Bulk Design 2 | **KEEP** |
| Mega Golisopod — DrPrettyman DS Design 1 | **KEEP** |
| Mega Golisopod — Elite Redux Bulk Design 2 | CUT |

These **four were already saved**, not new or flipped votes. The previous contradictory export history remains preserved so the reconciliation is traceable rather than silently rewritten. No technical sprite hold was reclassified by reaffirming these older artworks.

## Original approval history remains immutable

- Source user iPhone vote backup: [`review/user-iphone-decisions-2026-10-23.json`](user-iphone-decisions-2026-10-23.json).
- Exactly **166 earlier decisions** remain byte-for-byte identical, **154 KEEP / 12 CUT**. Original Git blob SHA-1: `61c5e53c6ec81b74d192cd62a4c52c970cea15ce`.
- Original historical GBA ledger remains byte-for-byte identical at `audit/2026-10-23/historical-decisions.json` with Git blob SHA-1 `e8e8474cbe127ab274086ea818aa86a821c990b5`; its 1,043 recorded lines include 566 historical approved and 477 historical rejected before later reconciliations.
- There are **170 effective decisions** from the 166 original iPhone votes plus four new source-scoped decisions. **All 158 currently actionable designs are decided.** Other historical votes and recovered source-pair decisions are not new tasks.
- **14 technical holds and five evolution-link identity warnings** across Hayog/Hogouse/Hogriks and Minamai/Marelstorm remain unresolved and cannot be auto-promoted.

## One canonical iPhone reviewer and exported decisions

[Master reviewer](https://lionsprideemb-tech.github.io/Sprites/master-review.html) now defaults to **Final four artwork approvals**, with the former “Needs my decision” mode available but empty for this complete set. The reviewer fetches and validates the pinned original 166-vote archive and a separate final user approval overlay, and explicitly applies the newer user decision once to any older browser cache without deleting newer user edits. The JSON backup contains all original user votes, the four new decisions, the latest archived Mega votes and separate technical-quality notes.

The original source metadata in `master-review-data.json` now references this final-approval source and finalized actionable counts **without changing its existing sprite entries, hold rows, artist credits, types, or original source paths**.

## Automated verification and boundary

- `node review/tests/final-user-artwork-approvals.cjs` validates the original two Git source blobs, exact eight front/back original sprite PNG blobs, four new decisions, unchanged four archived Mega votes, and **158/158** active resolved rows.
- `node review/tests/master-review-integrity.cjs` protects original artwork source completeness/identity and old votes.
- `node review/tests/quality-reviewer-browser-smoke.cjs` exercises older browser-cache conflicts, the updated finalized view, JSON export and preservation of 166 historical choices while keeping separate technical-quality feedback.
- The Python reviewer/artist provenance workflow was updated to recognize that the master page now defaults to finalized approvals, not unfinished approvals. No source-identity check was weakened.

**Not accomplished by this creative-vote release:** new DS battle sprite binary encoding, emulator validation of newly finalized artwork, texture insertion, species/evolution data changes, sprite removal, or ROM recompilation. KEEP means the user likes the exact design; it **never authorizes integration of DS-uncertified art**. Continue technical-quality checks, missing source and 4bpp native graphics certification separately.
