# Mercury Redux — sprite roster handoff (2026-10-23)

## Source of truth
The canonical, iPhone-friendly, family-grouped review page is **Sprites/master-review.html**. Its data is **Sprites/master-review-data.json**. The sprite library keeps its historic sources unchanged.

- Canonical reviewer source: https://github.com/lionsprideemb-tech/Sprites/blob/main/master-review.html
- Review data: https://github.com/lionsprideemb-tech/Sprites/blob/main/master-review-data.json
- Uploaded iPhone choices: https://github.com/lionsprideemb-tech/Sprites/blob/main/review/user-iphone-decisions-2026-10-23.json
- Prior DS and polished CSV snapshots: https://github.com/lionsprideemb-tech/Sprites/blob/main/review/recovered-user-export-decisions-2026-10-23.json
- Artist/name/family attribution audit: https://github.com/lionsprideemb-tech/Sprites/blob/main/review/identity-provenance-audit-2026-10-23.json

## Distinguish names and credits
The **source pack**, **credited artist**, **original filename/source label**, **actual Pokémon/form identity**, **types**, and **evolution family** are different fields. Never promote a label like "Mikitarian" or "Luminian" to a standalone Pokémon name solely because it appeared in an asset filename or creator catalog. Existing labels remain recoverable; suspect names and disputed family links go into the **Identity checks** view.

## Preservation
The previously uploaded user decision file contains **166 decisions: 154 KEEP and 12 CUT**. Of these, 154 match currently actionable cards; older/held entries must remain in exports. Original GBA and DS approval files stay intact. Do not re-ask approvals simply because a back sprite or metadata source is missing.

The current 2026-10-23 canonical snapshot contains **156 active review entries (154 already chosen plus 2 current-pass Wailmer/Wailord decisions), 16 technical holds, and 25 identity/name/family warnings** across active and held records; these counts are overlapping categories and are not final Pokédex species totals.

## Implementation gate
**No source sprites are deleted and no unapproved Pokémon, form, evolution link, or art source is integrated into the Platinum ROM.** A KEEP is an art/roster preference, not proof that a front/back/shiny/icon set is game-ready. Artist-name and family conflicts must be resolved before Pokédex placement and species ID assignment. Non-destructive technical repairs are performed separately.

## Validation
The existing sprite reviewer GitHub Actions integrity check passed at run https://github.com/lionsprideemb-tech/Sprites/actions/runs/40026325615 for the primary page and dataset. This is not a proof of a fully compiled ROM or an end-to-end iPhone Pages deployment.

Internal supplemental recovery files under review/ and mercury-master-review.html are historical/audit artifacts; do not treat them as a second authoritative approval queue.

## Current-pass Wailmer/Wailord unblocked
Recovered and verified original GBA front/back and shiny PNG source pairs in `DS_CUSTOM_LIBRARY/recovered/Reborn_Plates_Legacy/{wailmer,wailord}-alternate-form-1/`. Both designs are now accessible in the canonical reviewer as **unreviewed**, with their old contradictory history retained. They are **not** certified DS sprite conversions or authorized game integration. The canonical page defaults to unresolved families, and bulk KEEP can only touch currently visible, source-verified cards. The original 166 iPhone votes are unchanged. Integrity workflow: https://github.com/lionsprideemb-tech/Sprites/actions/runs/40030558498 (success).
