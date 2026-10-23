# Pokémon Mercury Redux — DS64 source-faithful technical sprite conversion and quality gates
Date: 2026-10-23

## Audited release inventory
- **83 source artwork sets**: 74 historically approved Reborn/Plates GBA originals, eight matched original source comparison pairs and one creator-credited Furrva original front/back pair.
- **332 expected view slots** (normal front/back and shiny front/back; the source only supplies 304 views). An absent original view is counted `MISSING_SOURCE`, not fabricated.
- **104 generated 64×64 technical PNG previews** with ≤15 opaque palette colors and binary alpha. Of these:
  - **12** original-colored pixel-preserved crops/canvas placements.
  - **53** original-colored previews recovered by **exact reversible 2× duplicate-pixel collapse** (the entire original image reconstructs pixel-for-pixel). No smooth scaling or invented pixels.
  - **39** quantized previews: **palette changed — user visual review required**. Never silently replace the prior approved art.
- **228 blocked or missing slots**: 179 oversized visible images without lossless fitting, 17 partial-alpha sources, **four undecodable original PNGs**, and 28 missing source views. These cannot be called DS-ready.
- **25 complete normal front/back technical pairs** and **15 four-view quartets** have output candidates. Individual green technical slots should not be interpreted as complete family sets. These are *still* not native engine tile format or ROM-integrated.
- The four unreadable original streams are **Munna alternate front/back** and **Musharna alternate front/back**. Their original Git objects and source paths are retained; other shiny slots remain independently usable where technically valid.

## Implemented pipeline and provenance
- [Deterministic Pillow converter](https://github.com/lionsprideemb-tech/Sprites/blob/main/tools/convert_verified_source_pairs_ds64.py). It refuses to overwrite original source files, verifies each source's exact Git blob SHA-1 or committed Furrva SHA-256, ensures no source in the manifest points outside this repository, detects unreadable PNG streams, quarantines semi-transparent and oversized artwork, and trims only transparent margins.
- [Conversion technical report](https://github.com/lionsprideemb-tech/Sprites/blob/main/DS_CUSTOM_LIBRARY/converted/Verified_Source_DS64_Technical_2026_10_23/technical_quality_manifest.json), including per-original SHA-256, dimensions, occupied pixel bbox, source color count, per-slot status and converted-output SHA-256. Every staged technical PNG has `gameIntegrationAllowed:false`.
- [GitHub Actions conversion workflow](https://github.com/lionsprideemb-tech/Sprites/blob/main/.github/workflows/verified-source-ds64-conversion.yml) invokes conversion, runs a **second `--check` pass** to rehash and inspect every technical output, validates original votes, and commits only the isolated converted folder and its report.
- The converter deliberately builds **64×64 transparent RGBA review sprites** following the repository's pre-existing technical staging convention. It does **not** emit native Nintendo DS 4bpp engine tiles, an insertion archive, approved Pokémon species data, palettes for the engine, or gameplay changes.

## Single iPhone master reviewer
[Open master-review.html](https://lionsprideemb-tech.github.io/Sprites/master-review.html) and select **DS technical conversion quality (read-only)**. The existing family-grouped reviewer now loads the technical manifest independently, preserving the ordinary creative review even if the technical report is unavailable. Per-view cards show original beside converted candidates, type/source names, status, original canvas/visible bbox/colors, lossless 2× provenance and palette-change warnings. Filter **All / Needs source repair / Palette review / Original colors retained**; original KEEP/CUT controls are disabled here.

The JSON backup adds a read-only technical summary without altering user choices. [Simulated browser export smoke test](https://github.com/lionsprideemb-tech/Sprites/blob/main/review/tests/quality-reviewer-browser-smoke.cjs) checks the family cards, controls, filters, and exports every originally protected decision. The ordinary [GitHub CI](https://github.com/lionsprideemb-tech/Sprites/blob/main/.github/workflows/sprite-review-integrity.yml) now runs this smoke test alongside node history/vote checks and technical source/output hash verification.

## Protected policy and remaining work
**All 166 previously recorded user artwork votes remain unchanged (154 KEEP, 12 CUT).** The 74 original approvals were neither reopened nor altered. Two unvoted Rainther options and prior Wailmer/Wailord source comparisons remain pending. No Pokémon were silently accepted.

**All five original evolution-link warnings remain unresolved:** Hayog/Hogouse/Hogriks and Minamai/Marelstorm must not acquire invented named evolution edges. Native DS sprite palette/tile encoding, positional and style-quality acceptance, quantized artwork approval, broken PNG repair, oversized source reconstruction, remaining shinies, and separate ROM integration are future gates.

**Never call these 104 technical previews game-ready or DS-certified.** This release stages independent conversion outputs plus a machine-readable quarantine report and provides a functional iPhone review mode. Platinum-modern-ds and Mercury-redux-dex should retain documentation/handoff status only, not copy these technical candidates into their production Pokédex or ROM.
