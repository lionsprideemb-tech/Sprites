# Orpheus native DS64 clarity linework — candidate only
Generated from the existing authentic 64×64 indexed pixels on the isolated `mercury/orpheus-resource-audit-20261109` branch.

[**Open the current vs polished source-exact comparison**](orpheus_ds64_linework_before_after.png)

- **Flygon FRONT:** 18 color-index pixel refinements: a stronger eye/muzzle region and a more continuous dark teal division between forewing and body.
- **Vibrava BACK:** 41 index changes: antenna shade refinements, wing-root contrast, and two connected pale blue wing veins. This deliberately replaces the earlier blank-looking, nearly monochrome wing with clearer internal structure.
- **Verified CI run:** [42905592470](https://github.com/lionsprideemb-tech/Sprites/actions/runs/42905592470) — SUCCESS; indexed tiles 2048 bytes, palette 32 bytes, exact reconstruction, unchanged 64×64 alpha masks and outline-index pixels.
- Full provenance: [machine-readable QA](linework_qa.json).

**Aesthetic caveat:** Flygon's dense original face and forewing overlap still looks crowded at native 64×64. These are meaningful color-plane and linework changes, but not a replacement DS-pixel illustration; if truly clean at 1× is the requirement, the original composition may need a deliberate source-faithful native-64 re-pixel, possibly relocating internal lines and preserving only the overall anatomy/pose.

**All assets UNAPPROVED.** No main branch, historical KEEP/CUT decisions, ordinary Flygon/Mega, Pokédex, DS engine sprites, shiny resources, or Platinum ROM changed. Artist-specific distribution terms still need recording even though the user reports permission.
