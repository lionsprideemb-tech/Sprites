# Final Species & Form Registry — placement reconciliation

Status: partial registry reconciliation, final playable roster still held.

Parent 4c708183502fa118fdb930d79987b9b9cde810c3; evidence 3f9b682ff99874af8cee409364511789c6e3026b. All source pins retained. Rechecked 641 placement records field-for-field against recovered October export and 576 REV6 approved/source-binding rows (572 retained plus two postseal additions). Rechecked 711 exact-art keys, 216 archive keys, 166 original votes, 1025 canonical species, and 468 distinct queue keys; passing queue hashes match preserved archive ledger.

## Counts
- canonical: 1025
- historicalAdditions: 574
- protectedSourceFormGroups: 547
- placementRows: 641
- artworkRecords: 711
- votes: 166
- archives: 216
- roleRecords: 189
- roleStates: {"PLACEMENT_BACKED_NAMED_IDENTITY_CANDIDATE":164,"HISTORICAL_IDENTITY_OVERLAP_HOLD":6,"PROTECTED_FORM_ROUTE_CANDIDATE_NO_NEW_SLOT":12,"FLYGON_ALTERNATIVE_SCOPE_HOLD":1,"EVOLUTION_EDGE_HOLD":5,"REPLACEMENT_NO_NEW_SLOT":1}
- replacementRecords: 33
- replacementStates: {"EXACT_CANONICAL_TARGET":26,"TARGET_OR_FORM_SCOPE_CONFLICT":5,"CANONICAL_FAMILY_MEMBER_SCOPE_HOLD":2}
- typeConflicts: 61
- explicitHistoricalOverrides: 5
- duplicateFamilies: 3
- duplicateSourceIdentities: 6
- duplicateRowArtBindingsHeld: 6
- evolutionWarnings: 5
- unlinkedCompleteDonors: 22
- mappingCompleteDonors: 3
- donorExactAcceptedFrontBlobMatches: 0
- historicalQueue: 468
- queueStates: {"OFFLINE_ARCHIVE_PASS":130,"AWAITING_PIXEL_ANALYSIS":205,"EXACT_PIXEL_HOLD":18,"PRIOR_MANIFEST_HOLD":33,"INCOMPLETE_SOURCE_LINK":82}
- queueNotPassing: 338
- queueNotPassingWithoutFlaggedRegistryHolds: 255
- queueReplacementRecords: 32
- additionalPlacementCandidateRecords: 188
- placementNoNewSlotOrOverlap: 25
- historicalProtectedGroupOverlap: 3
- productionIdsAllocated: 0
- newConversions: 0
- finalRosterLock: false

## Registry policy and blockers
- No final playable count: historical membership, exact artwork, native slots and technical readiness are distinct. A placement role is not proof of native slot uniqueness.
- Exact normalized label/constant and explicit protected-form semantic routes are collision candidates, not pixel equivalence or new approvals. A canonical replacement role is not approval to remove prior independent membership.
- Five type overrides recover explicit historical authority, not a final current typing decision. Other 56 lack explicit REV6 type overrides.
- Donor file hash inequality does not prove pixel inequality. No native sprite conversion or fresh pixel decode performed.
- Original August 28 exact 102 Platinum and final 28 custom membership lists remain unrecovered. 641 placement records preserve verbatim role/family fields even when questionable; 9 rejected-art placements remain held.
- The 468-set queue stays exactly intact. Separate placement candidates are not added to it. Zero conversion authorization in this release.

Three duplicate families: Arcanine Mega (SPECIES_ARCANINE_MEGA_REDUX, SPECIES_ARCANINE_MEGA); Reuniclus Mega (SPECIES_REUNICLUS_REDUX_MEGA, SPECIES_REUNICLUS_MEGA); Toxtricity Mega (SPECIES_TOXTRICITY_REDUX_MEGA, SPECIES_TOXTRICITY_MEGA). All six donor quartets present; original row-to-art assignment still held. 25 complete donor quartets independently checked in nontruncated 7,679-entry Elite source tree bb702ffcf7130ce04e5c2104254e619e0c7a6dc6. All 25 have zero accepted front Git-blob equality. Five named evolution edges remain unverified.

Flygon: one retained ordinary Mega, six superseded historical rows preserved, Platinum scope hold, three planned Delta members with UNAPPROVED artwork. No Delta Mega promoted.

Next: exact decoded-pixel and original review-card donor matching, replacement scope conflicts, explicit type decisions, protected form collision resolution, missing August authorities. Keep all work isolated.
