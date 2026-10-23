# Mercury Redux — Bulk sprite reconciliation report

**Date:** 2026-10-23  
**Scope:** Existing Sprites, Mercury-redux-dex, and platinum-modern-ds repositories.  
**Safety:** Non-destructive metadata/reviewer changes only. No Pokémon species IDs or ROM files edited.

## Verified recovery

| Check | Outcome |
|---|---:|
| Original GBA decision rows recovered | 1,043 |
| Original imported KEEP / CUT | 566 / 477 |
| Later user GBA decisions recovered | 94 |
| Rows that changed between ledgers | 27 |
| "New import" entries in Final 262 pass | 262 |
| Final 262 entries already matched to earlier rejection | 246 |
| Distinct additional Final 262 identities | 16 |
| Additional imports held for type/asset verification | 16 |
| Earlier verified Fakemon pool entries | 158 |
| Genuine competing-art identity groups | 15 |
| Competing design options | 30 |
| Actionable sprite-art choices now in master reviewer | 154 |
| Items held for metadata/sprite/identity repair | 18 |
| Historical approved rows lacking a linked front/back path | 107 |
| Historical duplicate identity keys | 5 |
| Duplicate identities containing conflicting decisions | 2 |

### Why the backlog shrank

Of the 262 entries labeled as newly imported, 246 were already CUT in the recovered GBA ledger; they were not requeued. All 16 remaining imports are held for back/front or exact typing verification instead of asking the user to judge incomplete art. The review page therefore focuses on verified source-metadata Fakemon, complete competing-art choices, and a small conflict set.

Previous GBA KEEP records are not silently treated as approvals in newer family-review pages. Existing family pages are preserved but their decisions often live only in that specific browser's local storage. The new site uses one versioned storage key and can export/import a full JSON + CSV decision manifest.

### Duplicated historical rows

Arcanine Mega (R0077/R0078), Reuniclus Mega (R0737/R0738), Hydreigon Mega (R0786/R0787), Tsareena Mega (R0867/R0868), Toxtricity Mega (R0901/R0902) have the same normalized identity in more than one historical row. Hydreigon Mega and Tsareena Mega include both KEEP and CUT records. Both original rows are preserved; conflicting identity keys are held for resolution.

### Image verification

The 154 actionable review entries each declare a front and a back path. Their **308 referenced PNG paths** were checked against the GitHub Git tree of each source pack/converted sprite folder on 2026-10-23; all 308 were present. A separate standard-library GitHub Actions validation also checks PNG signatures/dimensions, identity exclusions, metadata completeness, and export support. Git tree presence alone is not a full DS integration-quality guarantee.

### Data contracts

- `master-review-data.json`: actionable choices and technical holds, metadata provenance
- `historical-decisions.json`: immutable original review rows and later overrides
- `repair-queue.json`: known back/type/identity issues and protected old decisions
- `master-review.html`: iPhone-friendly family grouping, filtering, batching, autosave, JSON/CSV export + JSON import
- `tools/validate_master_review.py`: repeatable no-write verification
- `.github/workflows/mercury-master-review-integrity.yml`: CI validation

This is an **artwork selection** system. Pokémon forms remain unimplemented until a later approved ROM-integration pass.

### Known limitations

- The older local-browser decisions from separate family pages cannot be read from GitHub without a user-exported decision file.
- Some official/custom Megas require source/type/role verification; no provisional type is asserted as canon.
- Legacy approved rows with missing linked image paths are held for technical recovery, not re-rejected.
- A real ROM-integrated front/back/shiny/icon quality check has not been performed by this metadata audit.

### Multi-frame image exclusions

The image-dimension validator caught two animated-strip records: Criminalis (5400×100 front, 6400×100 back) and a Mega Flygon option (1920×96 each). These PNGs are preserved without modification but moved from actionable review into technical holds. Their matching standalone frame must be extracted and validated before the reviewer can display them as sprites. Counts after this correction: **164 actionable, 35 technical holds at that intermediate checkpoint**; the subsequent recovered user-export reconciliation lowered the live totals further..

### Original user-export recovery (later than GBA audit)

Recovered decision evidence was added to `review/recovered-user-export-decisions-2026-10-23.json`: 372 DS-art decision rows, 262 polished first-pass rows and 19 polished follow-up rows. This changes our interpretation of the older import ledger. Of the 246 polished imports that matched an older GBA CUT, **eight were explicitly marked KEEP in the later polished export** and are now protected as approved; the other 238 remained CUT. The 16 previously unknown imported identities also resolve as 15 DELETE and one KEEP (Skarmory Mega, held until verified type metadata). No previously rejected artwork has been deleted from the repo.

Ten remaining master-review design-option rows matched the user's exact source+front-path choices in the DS export (including Absol Z, Baxcalibur, Lucario Z, Golisopod and Garchomp Z); these were moved out of the undecided queue into preserved history, not re-reviewed. Seventeen technical holds were already explicitly rejected by a later exported choice and have been marked resolved; their original evidence remains linked in the repair queue.

**Current master reviewer after exported-user-decision reconciliation: 154 actionable designs, 18 technical holds.** This is a visual-artwork review count, not a Pokédex species count. The eight restored KEEP identities remain safe for later front/back family verification. Historical raw files were never overwritten.
