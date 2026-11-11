# Mercury Redux — Next sprite completion audit (November 10, 2026)

**Status: audit / recommended artwork only.** This report was committed exclusively on the existing Orpheus research branch `mercury/orpheus-resource-audit-20261109`. It does not approve any art, touch a decision ledger, alter the Pokédex, or integrate sprites into Platinum.

[Machine-readable queue and provenance](mercury-sprite-completion-gates-2026-11-10.json) · [Current Desert Scarab four-view comparison](desert-scarab-vein-scute-polish-native80/desert_scarab_veins_scutes_before_after_mobile.png) · [Canonical iPhone reviewer](https://lionsprideemb-tech.github.io/Sprites/master-review.html)

## Confirmed protected decisions

- **158/158** previously actionable reviewer artwork choices are resolved; **0** remain in that historical creative-decision set. The 166 original iPhone choices remain exactly **154 KEEP / 12 CUT**, as pinned by original Git blob `61c5e53c6ec81b74d192cd62a4c52c970cea15ce`.
- The four October 24 source-specific votes remain: **Wailmer alternate KEEP, Wailord alternate KEEP, Rainther Design 1 CUT, Rainther Design 2 KEEP**. Saved newer archived Mega results remain: **Mega Lucario Z Design 2 KEEP / Design 1 CUT; Mega Golisopod Design 1 KEEP / Design 2 CUT**.
- Original 1,043-row GBA history remains immutable, and all earlier source approvals still mean **creative approval only**, not game-ready binaries.
- The newer Desert Scarab quartet is **recommended for approval** based on final visual QA; it is **not included in any earlier approval tally**, and its four normal-view votes remain **unset**.

## Orpheus / Delta Flygon family state

| Required element | Latest verified state | Gate |
| --- | --- | --- |
| Normal Trapinch FRONT + BACK | Two original-color source-faithful native **80×80** indexed 4bpp candidates exist, but **no matching Desert Scarab final palette/scute treatment** | Finish cohesive **two-view** Trapinch color treatment before family review |
| Normal Vibrava FRONT + BACK | Two Desert Scarab genuine **80×80** 4bpp tiles/palettes and PNGs, latest vein/scute polish | **Recommended**, not approved |
| Normal Flygon FRONT + BACK | Two Desert Scarab genuine **80×80** 4bpp tiles/palettes and PNGs, latest vein/scute polish | **Recommended**, not approved |
| Delta family shinies | **No verified region-specific shiny FRONT/BACK** for any of the three stages (**6 missing views**) | Find/authenticate or commission subject to permission; review separately |
| Regional icons | **Three original Orpheus 128×64 icon sheets exist**; **no extracted/certified DS game-ready icon assets** for the selected Delta appearance | DS icon conversion, form appearance/credit and animation tests |
| Artwork rights | User reports artist permission, but exact modification/redistribution/credit terms are not independently recorded | Attribution/public-distribution check |
| Production archive | Genuine raw sprite tiles and 32-byte BGR555 palettes are **not** engine-ready NCGR/NCLR/NARC assets | Archive formatting, placement/animation, icon and emulator tests |
| Game identity/types | Existing standard family unchanged. Separate Delta line planned: first two stages include Bug, Flygon is **Bug/Ground**; **one** ordinary Mega Flygon; Electric Redux B line retired, no Delta Mega | Do not assign game IDs or import Orpheus's defective evolution graph before approval and collision checks |

Four-view [exact DS 4bpp QA](desert-scarab-vein-scute-polish-native80/veins_scutes_exact_QA.json) verifies **60** interior pixel-index adjustments (52 wing, 8 scute), unchanged stage palettes and alpha silhouettes, intact historical decisions, and no integration. GitHub Actions [run 42943009302](https://github.com/lionsprideemb-tech/Sprites/actions/runs/42943009302) succeeded. **The result is not an in-game rendering certification.**

## Wider technical backlog — restricted 83-source QA set

This inventory is **not** the full number of vanilla Pokémon, Megas, Fakemon, or total species in Mercury. It audits **83 selected original source-art sets, 332 possible normal/shiny front/back slots**:

| Category | Exact count | What it really means |
| --- | ---: | --- |
| Technical DS64 preview candidates | **108** | 68 source-colored pixel-preserved candidates plus 40 quantized previews; **not** gameplay-ready |
| Palette changed, awaiting visual quality review | **40 views / 19 designs** | Use an **exception-only** view; do not re-vote source artwork |
| Oversized for strictly lossless 64×64 fitting | **179 views / 55 designs** | Original art must be recovered in a compatible form or individually artistically adapted and approved |
| Partial alpha source block | **17 views / 7 designs** | Requires intentional alpha/edge repair, never silent transparency truncation |
| Missing original slots | **28 shiny views / 14 designs** | Includes five historically approved original shiny pairs |
| Source views still undecodable | **0** | Four original Munna/Musharna PNG container streams were genuinely recovered |
| Technically complete *preview* normal pairs | **27 designs** | Still only DS64 previews, not all engine assets |
| Technically complete *preview* four-view quartets | **17 designs** | Still not archive/emulator-certified |
| Exact-source-approved raw native DS64 4bpp | **58 views** | 10 complete normal pairs and 8 four-view sets inside this more restrictive QA subset |

Native 4bpp pool excluded a further **10 views** without demonstrated exact-source KEEP authority. This figure is a separate eligibility filter, **not** 10 extra missing slots to add onto 332.

The first five **historically approved** artwork pairs missing authentic shinies are **Breloom, Combee, Vespiquen, Dwebble, and Crustle alternate forms**. Additional missing-source shiny pairs belong to comparison/archival/unapproved-source records and should not be treated as required final imports.

The canonical reviewer has **14 technical/source holds**, plus **five disputed evolution-edge records** across **Hayog/Hogouse/Hogriks** and **Minamai/Marelstorm**. Do not invent those evolution links.

### Detected stale snapshot caveat

The October 23 `review/ds64-technical-quality-repair-queue-2026-10-23.json` still records **104 technical previews**, **39 palette checks**, and **four undecodable Munna/Musharna originals**. It is an *older intermediate snapshot*. The newer current-status JSON and live 83-set manifest both show **108**, **40**, and **0** respectively. Treat the latter as authoritative until generating a new reconciled repair queue.

## Actual next completion order (least repetitive user work)

1. **Finish two Desert Scarab Trapinch normal views**, retaining its existing Orpheus silhouette and source custody. Then show all three stages at **native 80px and enlarged** together, ideally one compact user approval decision per matched family. Vibrava/Flygon remain recommended only.
2. Only after a positive *explicit* user art choice, lock exact per-view hashes and verify artist credit/permission; separately source the **six Delta shiny views** and **three DS-compatible icons** without assuming original base shinies match.
3. Run automated **exception-only color quality** checks for the 40 quantized previews, batch complete easy source-pair repairs, then work in selected family batches on the **179 oversized** and **17 partial-alpha** cases. Existing creative choices remain immutable.
4. Recover original source shinies for the five historically approved Breloom/Combee/Vespiquen/Dwebble/Crustle forms first, then consider lower-priority comparison-source gaps.
5. Preserve the two unresolved evolution groups without canonical arrows until named evidence exists.
6. For **only fully approved, complete and technically certified** assets, format genuine Nintendo DS sprite archives, validate per-form species ID and source collisions, and perform ROM build/emulator/battle/shiny/icon tests **behind a separate integration authorization**. Do not overwrite the existing Platinum modernizations.

## Additional delivery and CI health

- Sprites main latest `f15c4671bf7a`: master reviewer integrity [run 42876959018](https://github.com/lionsprideemb-tech/Sprites/actions/runs/42876959018) **passed**; independent newer reviewer integrity [run 42876959028](https://github.com/lionsprideemb-tech/Sprites/actions/runs/42876959028) also **passed**.
- Sprites main GitHub Pages [run 42876956939](https://github.com/lionsprideemb-tech/Sprites/actions/runs/42876956939): **build passed, deployment failed**. Deploy logs repeatedly reported `syncing_files` and then **timeout**. That is a deployment-health issue, **not evidence that data or user votes failed integrity**. Check/repair Pages deploy before relying on a newly refreshed iPhone site; avoid republishing the entire large asset library if unnecessary.
- Mercury-redux-dex latest main `faa7cb4016d8`: Pages [run 42689487548](https://github.com/lionsprideemb-tech/Mercury-redux-dex/actions/runs/42689487548) **passed**.
- platinum-modern-ds latest main `5525e961a1fb`: repository guard [run 42689493823](https://github.com/lionsprideemb-tech/platinum-modern-ds/actions/runs/42689493823) **passed**. No Desert Scarab files are on its main branch.

### Hard safety boundaries

**No new source art, shiny, icon, user KEEP/CUT vote, historical row, game species ID, evolutionary edge, gameplay file, Platinum ROM, or master Pages reviewer was changed by this audit.** This report and the machine-readable backlog are research-branch documentation only. In particular, no recommendation here constitutes an artwork approval.
