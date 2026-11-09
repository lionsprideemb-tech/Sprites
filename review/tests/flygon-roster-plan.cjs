"use strict";
// Guard current Flygon roster decisions against the original approved-art ledger.
// This is a *roster planning overlay*; historic KEEP/CUT records are immutable.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");
const root = path.resolve(__dirname, "../..");
const get = p => JSON.parse(fs.readFileSync(path.join(root, p), "utf8"));
const gitBlob = data => crypto.createHash("sha1").update(Buffer.from("blob " + data.length + "\0")).update(data).digest("hex");
const plan = get("review/flygon-roster-plan-2026-11-09.json");
assert.equal(plan.schema, "mercury-flygon-roster-plan-v1");
assert.equal(plan.decidedOn, "2026-11-09");
assert.equal(plan.protections.existingSpriteFilesDeleted, false);
assert.equal(plan.protections.originalHistoricVotesModified, false);
assert.equal(plan.protections.romIntegrationAllowed, false);
assert.equal(plan.protections.dexSpeciesEditsAllowed, false);
assert.equal(plan.legacyDraftMap, "ER125_REDUX_TO_DELTA_MAP.csv");
assert.deepEqual(plan.plannedStructure.ordinaryFamily.species, ["Trapinch", "Vibrava", "Flygon"]);
assert.equal(plan.plannedStructure.ordinaryMega.numberOfMegaSlots, 1);
assert.equal(plan.plannedStructure.deltaMega.numberOfMegaSlots, 0);
assert.deepEqual(plan.plannedStructure.deltaFamily.species, ["Delta Trapinch", "Delta Vibrava", "Delta Flygon"]);
assert.equal(plan.plannedStructure.deltaFamily.finalEvolutionType1, "Bug");
assert.equal(plan.plannedStructure.deltaFamily.finalEvolutionType2, "Ground");
assert.equal(plan.plannedStructure.deltaFamily.status, "planned_artwork_unresolved");
assert.deepEqual(plan.acceptance, {
  plannedFamilies: 2, plannedTotalMegaForms: 1, newBugGroundDeltaMembers: 3,
  unresolvedDeltaArtworkMembers: 3, electricLineMembersInRoster: 0
});
const old = get("review/recovered-user-export-decisions-2026-10-23.json");
const rows = old.exports[0].rows;
const byIdentity = new Map(rows.map(x => [x.identity, x]));
assert.equal(byIdentity.get("flygon-mega").decision, "approve");
assert.equal(byIdentity.get("flygon-redux-b").decision, "approve");
assert.equal(byIdentity.get("flygon-redux-b-mega").decision, "approve");
assert.equal(byIdentity.get("flygon-redux").decision, "reject");
assert.equal(byIdentity.get("flygon-redux-mega").decision, "reject");
assert.equal(byIdentity.get("trapinch-redux").decision, "reject");
assert.equal(byIdentity.get("vibrava-redux").decision, "");
assert.equal(plan.plannedStructure.ordinaryMega.artworkCandidate.front, byIdentity.get("flygon-mega").front_path);
const exclusions = new Set(plan.excludedFromPlannedRoster.map(x => x.identity));
assert.deepEqual([...exclusions].sort(), ["flygon-redux-b", "flygon-redux-b-mega"]);
for (const item of plan.excludedFromPlannedRoster) {
  assert.equal(item.currentRosterStatus, "retired_not_for_mercury");
  assert.equal(item.sourceSpritesPreserved, true);
  assert.equal(item.front, byIdentity.get(item.identity).front_path);
  assert.ok(fs.existsSync(path.join(root, item.front)), "Retired art must remain archived: " + item.front);
}
assert.ok(fs.existsSync(path.join(root, plan.plannedStructure.ordinaryMega.artworkCandidate.front)));
const archived = get("review/user-iphone-decisions-2026-10-23.json");
assert.equal(archived.count, 166);
assert.equal(archived.keepCount, 154);
assert.equal(archived.cutCount, 12);
const protectedFile = fs.readFileSync(path.join(root, "review/user-iphone-decisions-2026-10-23.json"));
assert.equal(gitBlob(protectedFile), "61c5e53c6ec81b74d192cd62a4c52c970cea15ce");
assert.ok(plan.legacyDraftMapOverride.includes("Do not auto-import"));
console.log("PASS Flygon roster: original family + 1 Mega, 3 unapproved Bug/Ground Delta stages, Electric Redux B + Mega retired from roster, old sprites/votes untouched.");
