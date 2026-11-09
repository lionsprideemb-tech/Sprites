# Pokémon Mercury Redux — isolated native DS OBJ 4bpp QA release (2026-11-09)

## Verified result
- **58** technically accepted, exact-source-approved PNG views encoded to Nintendo DS **64×64 OBJ 4bpp tiled pixel data (2048 bytes per view)** and their **16-entry BGR555 palettes (32 bytes per view)**.
- **10** source designs have verified normal front/back in this *restricted native-encoding QA pool*.
- **8** designs have verified normal front/back plus shiny front/back in this pool.
- Each artifact was decoded to pixels and byte-verified by a deterministic second run. Channel error from required DS RGB555 rounding is at most **5 levels per 8-bit RGB channel**.
- Independently excluded from staging: **179** oversized no-lossless-fit views, **17** partial-alpha views, **28** missing source slots, **40** pre-quantized views needing actual visual review, and **10** technically source-faithful views without a demonstrated exact-source KEEP authorization (including external/unapproved source art).
- The original **83 source sets / 332 expected slots** and all original source graphics remain untouched. Above numbers describe *source slots*, not species roster completion.

## Provenance
- [Script](../tools/stage_native_ds4bpp_qa.py) and [CI workflow](../.github/workflows/native-ds4bpp-qa.yml).
- [Green native 4bpp round-trip action](https://github.com/lionsprideemb-tech/Sprites/actions/runs/42681775419).
- [Merged implementation PR #1](https://github.com/lionsprideemb-tech/Sprites/pull/1), main merge SHA `51577cde7ef574adfa03152c867de9f817007020`.
- Action artifact: `mercury-native-ds4bpp-qa-not-rom` (includes separate `.4bpp`, `.pal`, decoded PNG previews, and `qa-manifest.json`; 30-day retention).

## Unchanged approval and game boundaries
- Exact four final source decisions still hold: **Wailmer alt KEEP, Wailord alt KEEP, Rainther Design 2 KEEP, Rainther Design 1 CUT**.
- Latest saved Mega choices still hold: **Mega Lucario Z Design 2 KEEP / Design 1 CUT** and **Mega Golisopod Design 1 KEEP / Design 2 CUT**.
- All **166 original votes (154 KEEP, 12 CUT)** remain unchanged. All **158 current actionable decisions** are finished. The historical GBA ledger is unchanged.
- **No playable ROM, Pokédex species IDs, evolution links, title/UI, texture archives or gameplay files were modified.** The artifact is a *raw OBJ 4bpp QA package*, **not a Nitro NCGR/NCLR/NARC production format**, and no entry is runtime/emulator-certified.
- Five uncertain evolution links across Hayog/Hogouse/Hogriks and Minamai/Marelstorm remain quarantined, not automatically invented or inserted.

## Next technical finish-line steps
1. Validate decoded 4bpp graphics visually against the actual DS engine rendering path, then construct DS-compatible sprite archives for only certified complete sets.
2. Prioritize authentic recovery or source-faithful repair of oversized, partial-alpha and missing views in family-sized groups; do not silently treat nearest-neighbor comparison previews as approved replacements.
3. Restrict any later ROM staging to exact-source KEEP identity and verified complete required normal/shiny/icon coverage, with species/form collision checks and full Platinum build/emulator tests.
4. Keep unresolved evolution edges out of the initial playable release if they cannot be verified. No more routine giant approval sheets are required.
