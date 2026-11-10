# Native 64×64 visual assessment — stronger Orpheus Delta Flygon candidates
Date: 2026-11-10 | Research only | **No approvals / no ROM integration**

## Exact reviewed files
- [Vibrava back stronger 64×64 PNG](vibrava_back_stronger64.png)
- [Flygon front stronger 64×64 PNG](flygon_front_stronger64.png)
- [Single mobile before/current/close-up sheet](ds64_stronger_two_view_mobile_review.png)
- [Indexed-geometry QA](ds64_stronger_two_view_qa.json), built in [successful workflow run 42900872568](https://github.com/lionsprideemb-tech/Sprites/actions/runs/42900872568).

## Visual assessment, independently from the binary QA

### Vibrava BACK — conditional visual hold; minor final cleanup recommended
- The body and rear head shape now read reasonably well in the tiny 64px preview; the turquoise eye ring is visible.
- The curled antenna ends are distinct but the stalks are thin and high-contrast narrow strokes, creating visually detached-looking top details even though alpha islands are not detached.
- The large pale rear wing has a long straight edge and a flat pale interior that partly disappears against the light display background. The wing attachment/forebody intersection could use *local* stronger shade clustering and wing-root definition.
- Limit scope to **small anatomy-aware** interior shading and continuity corrections: reinforce the 1px antenna join in places without changing outline; establish a slightly clearer wing-root shadow/transition using existing sage/turquoise shades. Do not enlarge antennae, redraw wing outline, or change its stage-specific palette.
- **Not approved.** A minor final candidate pass might be sufficient, but human judgement is required.

### Flygon FRONT — visual hold; **not approval-ready**
- Silhouette and broad wings remain distinctive, with correct original Orpheus morphology.
- At true 64×64, the eye is difficult to isolate from the bronze/brown head, crest, and upper wing-root shading. The wing's light cyan membrane and small dark chest/forewing details compete with the facial focal point.
- Multiple tiny light/dark clusters around the face-to-forewing crossing give a noisy pixel pattern despite the palette-only and small index corrections.
- Suggested next pass: a **strictly local hand-guided 64px interior re-clustering** of eye rim/eye highlight, muzzle vs neck shadow, and the forewing-body intersection. Use existing 16-color palette. Preserve outer silhouette, antenna, wings, pose, and original design. Test *at 1×* against original source silhouette. Do not assume that more palette smoothing alone will restore details lost during 160→64 conversion.
- **Not approved.** Continue only on these localized internal regions.

## QA interpretation
Existing verified run showed **24 Vibrava back** and **30 Flygon front** indexed pixel changes relative to previous microfix candidates. The DS 4bpp PNG/tile decoding and palette limits passed with identical outer alpha, outline index 1, and color palette. This confirms **format integrity, not aesthetic readiness**. There is no technical justification to approve either image automatically.

## Restrictions
- Both remain research candidates; **not KEEP/CUT or other recorded approvals**.
- Other four family views are not reopened or altered.
- Orpheus source PNGs and historical Mercury user votes stay intact; neither the master sprite library nor `Mercury-redux-dex` nor `platinum-modern-ds` is modified.
- No shiny support, DS engine resource insertion, or ROM test is implied.
- User-reported artist permission exists; exact attribution and redistribution/edit scope have not been documented on this branch.
