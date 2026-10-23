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
| Actionable sprite-art choices now in master reviewer | 166 |
| Items held for metadata/sprite/identity repair | 33 |
| Historical approved rows lacking a linked front/back path | 107 |
| Historical duplicate identity keys | 5 |
| Duplicate identities containing conflicting decisions | 2 |

### Why the backlog shrank

Of the 262 entries labeled as newly imported, 246 were already CUT in the recovered GBA ledger; they were not requeued. All 16 remaining imports are held for back/front or exact typing verification instead of asking the user to judge incomplete art. The review page therefore focuses on verified source-metadata Fakemon, complete competing-art choices, and a small conflict set.

Previous GBA KEEP records are not silently treated as approvals in newer family-review pages. Existing family pages are preserved but their decisions often live only in that specific browser's local storage. The new site uses one versioned storage key and can export/import a full JSON + CSV decision manifest.

### Duplicated historical rows

Arcanine Mega (R0077/R0078), Reuniclus Mega (R0737/R0738), Hydreigon Mega (R0786/R0787), Tsareena Mega (R0867/R0868), Toxtricity Mega (R0901/R0902) have the same normalized identity in more than one historical row. Hydreigon Mega and Tsareena Mega include both KEEP and CUT records. Both original rows are preserved; conflicting identity keys are held for resolution.

### Image verification

The 166 actionable review entries each declare a front and a back path. Their **332 referenced PNG paths** were checked against the GitHub Git tree of each source pack/converted sprite folder on 2026-10-23; all 332 were present. A separate standard-library GitHub Actions validation also checks PNG signatures/dimensions, identity exclusions, metadata completeness, and export support. Git tree presence alone is not a full DS integration-quality guarantee.

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
