# Orpheus (2021) regional Flygon family — quarantined source-art review

This folder contains **two image previews** made solely for visual inspection. The PNGs were extracted from the original public Orpheus Resources RAR (SHA256 `72539b83b55a427c4adcdf2f3e5397cc28371875a720f687ffcf4e2a6d803ef9`), with a read-only GitHub Actions audit: https://github.com/lionsprideemb-tech/Sprites/actions/runs/42695802925 . The comparison view scales *vanilla* source fronts only for side-by-side viewing with nearest-neighbor; the regionals are shown directly at source size.

- [Original regional family front/back/icon contact sheet](regional-sprites.svg)
- [Vanilla-versus-regional front sprite comparison](vanilla-vs-regional.svg)

Actual source files in the RAR:
`Graphics/Battlers/328_1.png`, `328b_1.png`, `329_1.png`, `329b_1.png`, `330_1.png`, `330b_1.png`; icons `Graphics/Icons/icon328_1.png`, `icon329_1.png`, `icon330_1.png`.

Regional battle front/back files are **160×160** each, with 16/15, 25/19 and 35/30 unique RGBA palette colors respectively, including transparency. Icons are **128×64** sheets. They are **not DS-ready 64×64**, and some views exceed 16 colors even before color-depth tests. A matching regional shiny quartet was **not proven**; base `328s`, `329s`, `330s` entries cannot be assumed to be the custom regional shinies.

Verified type data from `PBS/pokemonforms.txt` in the same original RAR:
- `[TRAPINCH,1]` `FormName = Thracean` `Type1 = BUG`
- `[VIBRAVA,1]` `FormName = Thracean` `Type1 = BUG`, `Type2 = DRAGON`
- `[FLYGON,1]` `FormName = Thracean` `Type1 = BUG`, `Type2 = DRAGON`
- Original `[TRAPINCH,1]` `Evolutions = FLYGON,Level,25` skips Vibrava, corroborating an old Orpheus forum bug report. The intended final Mercury family would require an independently designed proper evolution map.
- The regional Vibrava records also had `Evolutions = LYCANROC,LevelEvening,40` in the source pack: **an unrelated erroneous evolution**, not a reusable family registration.

Art assessment: unlike the ordinary family, Thracean forms have green/yellow insect-themed anatomy, custom antennae and wing shapes, and drastically different source silhouettes. Fits distinct-design requirement, but `FLYGON` originally Bug/Dragon rather than the required final Bug/Ground. A faithful DS-size conversion is **not certified**.

**All art remains unapproved, isolated in this research branch, with no original sprite files imported into the main sprite library, Pokédex or Platinum ROM.** Artist-specific permission is unverified. Credits source: https://eeveeexpo.com/resources/592/ . Do not treat these previews or the published resource pack as an unrestricted reproduction license.
