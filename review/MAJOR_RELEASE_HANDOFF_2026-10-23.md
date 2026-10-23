# Pokémon Mercury Redux — Bulk Sprite Recovery & Master Reviewer release
Date: 2026-10-23

## Work delivered
- Kept the existing GitHub Pages [master reviewer](../master-review.html) as the **single decision interface**. Added the "Already-approved source art (read-only)" mode: original normal front/back and shiny front/back previews, recorded types, original provenance, 39 evolution-family groupings, search and missing-shiny filter.
- Protected the existing [166 explicitly saved iPhone choices](user-iphone-decisions-2026-10-23.json) (154 KEEP, 12 CUT). The historical GBA/DS source files and approved artwork were never modified or deleted.
- Repaired JSON restore semantics: partial imports now **merge** with existing decisions instead of wiping unmentioned votes. Non-current IDs survive browser reload and continue into exported JSON. Technical-hold identity corrections can round-trip in JSON. CSV is a simplified decision table; JSON remains the complete GitHub handoff.
- Added [approved source repair queue](legacy-approved-artwork-repair-2026-10-23.json) covering the **five** missing shiny pairs (Breloom, Combee, Vespiquen, Dwebble, Crustle).
- Added [source identity and evolution-family triage](identity-family-triage-2026-10-23.json): 19 held source records — 10 evolution-family conflicts, 6 artist/region ambiguity records, and 3 unverified names. Historical family alternatives are preserved, not silently accepted.
- Normalized three impossible "Dragon / Dragon" duplicate type labels (Larvitar/Pupitar/Tyranitar Space Form 4) to one **Dragon** type without touching any artwork, vote or gameplay data.
- The optional recovered-source manifest is now isolated from the voting fetch; a preview loading error does not disable normal creative decisions.
- Added [regression test source](tests/master-review-integrity.cjs) and a [push-triggered GitHub Actions workflow](../.github/workflows/sprite-review-integrity.yml).

## Verification performed
- 12 in-memory/static structural checks passed, including reviewer JavaScript syntax, 156 active entries, exact protected vote totals, source-pair and repair inventory, read-only mode, and backup preservation.
- The committed Node regression script's assertions were also **executed against live-fetched GitHub file contents through an in-memory Node-compatible harness** and passed. This is **not** a claim that a native GitHub-hosted runner passed.
- Checked 14 individual PNG paths using GitHub file reads with base64 encoding and compared each result to its manifest Git blob SHA: all **14/14** matched with PNG signatures. The sample covers both normal images for all five missing-shiny entries and all four Butterfree alternate-form images.
- **Not verified:** complete 286-image runtime load in Safari, live GitHub Pages refresh, completed GitHub Actions status, DS conversion, ROM integration, emulator test, or a compiled new .nds build.

## Protected build boundary
**All 74 linked pairs remain original GBA artwork, not certified DS-ready sprites.** The DS engine and Dex were not modified by this release except cross-repository documentation/handoff notes. Do not assign new species IDs, force original forms into the game, overwrite previously approved art, substitute an unrelated backsprite, or invent shinies.

## Recommended next major work
1. Original matching shiny-source recovery for the exact five outstanding cases, then verifiable DS conversion/format and palette checks across all 74 pairs.
2. Resolve evidence-backed identity and evolution-family disputes without turning source labels into new species.
3. Validate complete image load on GitHub Pages in iPhone Safari, run and review CI, confirm exported user decisions and only then prepare a separate explicit ROM integration gate.
