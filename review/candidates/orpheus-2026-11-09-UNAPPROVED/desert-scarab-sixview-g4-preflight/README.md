# Delta Desert Scarab six-view production-format preflight (UNAPPROVED)

[Six normal FRONT/BACK sprites at original 80px and enlarged zoom](desert_scarab_six_normal_native80_mobile.png)

All three stages now have normal front/back 80x80 indexed palette and 4bpp tiles. Trapinch receives source-geometry-locked terracotta/ochre palette and a few subtle interior scutes; Vibrava/Flygon retain their existing published pixels exactly. Each view has an optional **160x80 STATIC repeated-frame PNG** and JASC palette suitable for testing the upstream Platinum nitrogfx input path; a repeated static frame is *not* a finished battle animation. 64x64 previews are deliberately destructive and are **not** Platinum input.

Missing custom shiny views, game icons, artist attribution terms, user artwork approval, engine archive/integration/emulator testing. No votes, game files, IDs or source art modified. [Machine QA](preflight_qa.json).

## Real Platinum NitroGFX encoding probe

Generated six NCGR and six NCLR **standalone files** using the upstream pret/pokeplatinum NitroGFX encoder with the exact native build flags. Each was decoded back to its full 160x80 indexed pixel source with **0 index differences**. This verifies the file-encoding stage only: no approved art, shiny views, converted icon archive, correct form/species NARC index integration or game runtime proof. See [nitrogfx QA](nitrogfx_qa.json).
