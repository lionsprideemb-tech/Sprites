# Pokémon Mercury Redux — Oversized Sprite Recovery & Visual Quality Approval
Date: October 23, 2026

## Scope and repository guardrails

This is a **source recovery / visual-preview / reviewer** release, not a new playable Nintendo DS ROM. Reused the latest canonical 83-artwork-source conversion manifest and original source paths, retaining **all 166 protected prior decisions (154 KEEP, 12 CUT)** and the existing original artwork files. Cross-repository Dex and ROM handoffs are documentation-only, not gameplay or Pokédex modifications.

- Canonical iPhone master reviewer: https://lionsprideemb-tech.github.io/Sprites/master-review.html
- [Current quantitative release inventory](oversized-visual-recovery-current-status-2026-10-23.json)
- [Repaired exact original PNG pixel streams](../DS_CUSTOM_LIBRARY/recovered/Reborn_Plates_Legacy_PNG_Container_Repairs/recovery_manifest.json)
- [Current converted technical report](../DS_CUSTOM_LIBRARY/converted/Verified_Source_DS64_Technical_2026_10_23/technical_quality_manifest.json)
- [Quarantined nearest-neighbor visual comparison report](../DS_CUSTOM_LIBRARY/comparison/DS64_Visual_Triage_2026_10_23/comparison_manifest.json)

## Authentic Munna and Musharna file rescue (4 of 4)

Recovered Munna alternate normal front/back and Musharna alternate normal front/back as **actual decodable original compressed PNG pixel data**, rather than substituting vanilla sprites or redrawing artwork.

GitHub Actions ran `tools/recover_legacy_png_containers.py`. Its source SHA-1/Git blob checks validate the original historically approved files. It retained the **exact critical IHDR/PLTE/tRNS/IDAT/IEND chunks**, refusing invalid critical CRCs; removed only nonessential ancillary metadata. The original four PNGs were never overwritten. The broken ancillary `iCCP` chunks failed their CRCs, explaining why Pillow rejected the old files. The separately saved original-pixel PNGs now decode successfully; the original Web/Git records and image-data bytes remain auditable.

**Caveat:** stripped color-profile metadata could affect interpreted color appearance. These image streams have **not** received human visual color approval or native DS tile/palette integration.

The verified converter now uses those four independent source-recovery paths *without changing a previous user-approved source file*, and checks that the old original Git blobs still match.

## Technical conversion results after original-data recovery

| State | Count |
| --- | ---: |
| Original-artwork source sets | 83 |
| 64×64 technical candidates | **108** |
| Original colors retained (13 direct + 55 exact 2× reverse duplication) | **68** |
| Technical palette-quantized views (not visually approved) | **40** |
| Complete normal front/back candidate sets | **27** |
| Complete normal + shiny four-view candidate sets | **17** |
| Views still technically oversized | **179** |
| Views still blocked by partial transparency | **17** |
| Original sources still unreadable | **0** |
| Original view slots without matching source art | **28** |

Technical output means an independently staged 64×64 transparent PNG preview, at most 15 opaque colors. It is **not** binary Nintendo DS engine graphics or an in-game artwork approval. No source design is re-accepted simply because its technical candidate looks plausible.

## Oversized and partial-alpha visual comparisons (196)

`tools/build_visual_rescue_comparisons.py` generated **196 separate comparison-only previews**: 179 oversized and 17 partial-alpha sources. It uses pixel-art nearest-neighbor reduction **only for explicitly marked visual side-by-side comparisons**, never as an unannounced replacement for source artwork or an approved ROM sprite. Before sampling, it may collapse an exact invertible duplicated 2× grid. Partial-alpha images remain transparent and are explicitly labeled as alpha concerns.

The [comparison manifest](../DS_CUSTOM_LIBRARY/comparison/DS64_Visual_Triage_2026_10_23/comparison_manifest.json) tracks the original source SHA256 and comparison output SHA256, source/preview ink extents, exact-2× status, partial-alpha status, provenance, and `gameIntegrationAllowed:false`. The `--check` mode verifies all original and preview PNG hashes and original-output pairing.

No new art is drawn or fabricated. **Nearest-neighbor previews necessarily lose some pixels at smaller resolution**, so they are for comparing artistic acceptability and identifying a need for authentic smaller art, **not a faithful native replacement**.

## 40 palette-limited candidates — pending user's actual visual approval

The original 39 palette-quantized views grew to **40** when the recovered Munna front became decodable. All 40 now have quantitative color-change measurements in the comparison manifest. These are comparisons, **not user approvals**. High-change examples include alternate Poliwag front (about 32.5% of visible pixels), Durant alternate shiny back (~30.0%), and Sunflora alternate front (~28.3%). These measured fractions do not on their own establish visual quality.

## One iPhone reviewer, separate quality feedback

The [existing master reviewer](https://lionsprideemb-tech.github.io/Sprites/master-review.html) retains the former creative KEEP/CUT pages and family sort. In **DS technical conversion quality (read-only)** it now displays:

- Original artwork, any DS64 technical candidate, and a **clearly labeled nearest-neighbor comparison preview** together, plus original types and source/family names.
- Palette-change fraction/mean RGB delta and explicit warning that human review is needed, with safe searchable family groupings.
- A **separate user quality review control** for individual views: `Preview looks acceptable`, `Needs original art or palette repair`, `Unsure—hold`, or no response. User notes and source/output hashes persist in browser storage and export to JSON as `qualityChecks`. Changed source hashes invalidate stale quality choices. These controls **do not modify creative KEEP/CUT and never permit automatic ROM insertion**.
- Existing historical decision import/export and pending design selection are preserved. Original KEEP/CUT choices are always the authoritative creative votes, not a technical preview rating.

An independent GitHub Actions simulated browser workflow validates the user-facing quality control, JSON download, saved notes/check metadata and preservation of the prior 166 artwork decisions. The same workflow separately revalidates the original and technical candidate image hashes and palette limits. A simulated DOM result does **not** substitute for a manual Safari session on the user's phone.

## Still outstanding

1. **179 oversized views** remain blocked for lossless DS64 conversion. The nearest-neighbor comparison is an *option to assess* and should never be promoted without explicit visual review and native DS rendering tests.
2. **17 original views** retain partial alpha and require source-level artistic/alpha review (no silent alpha-thresholding).
3. **28 missing original views** include shinies in the historically approved source set and nonrequired comparison shinies; no substitute sprites were invented.
4. **40 palette-quantized views** await explicit creative visual judgments, which cannot be inferred from automated metrics.
5. The five previously unresolved evolution edges for **Hayog/Hogouse/Hogriks** and **Minamai/Marelstorm** remain blocked pending primary-source confirmation.
6. No sprites were encoded into DS engine sprite/tile binaries or inserted in the playable ROM. No new species IDs, game events or Pokédex stages were assigned.

## Source code and workflow

- [Lossless PNG container recovery](../tools/recover_legacy_png_containers.py)
- [Original source-to-DS64 technical converter](../tools/convert_verified_source_pairs_ds64.py)
- [Nearest-neighbor comparison and palette-metric pipeline](../tools/build_visual_rescue_comparisons.py)
- [Browser quality/export test](tests/quality-reviewer-browser-smoke.cjs)
- [GitHub integrity workflow](../.github/workflows/sprite-review-integrity.yml)
- [Nearest-neighbor comparison workflow](../.github/workflows/visual-source-recovery-comparisons.yml)

The next large release should prioritize user-backed visual decisions for the 40 color-changed images and the most important family front/back comparisons; targeted authentic small-size source research for the 179 oversized and 28 missing cases; and separate native DS texture/tile encoding tests. Do not reopen the 166 old decisions or enter ROM integration without all relevant gates.
