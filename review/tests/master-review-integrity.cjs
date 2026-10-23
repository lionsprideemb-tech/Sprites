"use strict";
const assert=require("node:assert/strict");
const fs=require("node:fs");
const vm=require("node:vm");
const path=require("node:path");
const root=path.resolve(__dirname,"../..");
const read=(p)=>fs.readFileSync(path.join(root,p),"utf8");
const html=read("master-review.html");
const main=JSON.parse(read("master-review-data.json"));
const votes=JSON.parse(read("review/user-iphone-decisions-2026-10-23.json"));
const src=JSON.parse(read("review/recovered-approved-legacy-pairs-2026-10-23.json"));
const repair=JSON.parse(read("review/legacy-approved-artwork-repair-2026-10-23.json"));
const js=html.match(/<script>([\s\S]*?)<\/script>/);
assert.ok(js,"review script missing");
new vm.Script(js[1],{filename:"master-review.js"});
assert.ok(html.includes('value="recovered"')&&html.includes("function renderRecovered()"));
assert.ok(html.includes("Object.assign(STATE,incoming)"));
assert.ok(!html.includes("STATE=incoming;"),"partial import erases saved decisions");
assert.equal(votes.entries.length,166);
assert.equal(votes.entries.filter(x=>x.decision==="keep").length,154);
assert.equal(votes.entries.filter(x=>x.decision==="cut").length,12);
assert.equal(new Set(votes.entries.map(x=>x.id)).size,166);
assert.equal(main.entries.length,156);
assert.equal(src.entries.length,74);
assert.equal(new Set(src.entries.map(x=>x.family)).size,39);
assert.equal(src.entries.filter(x=>x.missingShiny).length,5);
assert.equal(src.entries.filter(x=>!x.missingShiny).length,69);
assert.equal(repair.repairs.length,5);
assert.equal(repair.counts.originalApprovedPairs,74);
const types=new Set("Normal Fire Water Grass Electric Ice Fighting Poison Ground Flying Psychic Bug Rock Ghost Dragon Dark Steel Fairy".split(" "));
const ids=new Set();
for(const x of src.entries){
 assert.ok(!ids.has(x.reviewId),"duplicate review ID");ids.add(x.reviewId);
 assert.ok(x.front?.path&&x.back?.path&&x.front?.gitBlobSha&&x.back?.gitBlobSha);
 assert.ok(types.has(x.type1)&&(!x.type2||types.has(x.type2)),"noncanonical type");
 assert.ok(!x.type2||x.type1!==x.type2,"duplicate primary and secondary type");
 assert.equal(x.effectiveDecision,"keep");
 assert.equal(x.reviewRequired,false);
 assert.equal(x.artworkIntegrationAllowed,false);
}

const allRows=main.entries.concat(main.technicalHolds);
const one=(key)=>{const x=allRows.find(x=>x.id.startsWith(key));assert.ok(x,"missing "+key);return x;};
assert.equal(new Set(main.entries.map(x=>x.id)).size,156);
assert.equal(main.entries.concat(main.technicalHolds).filter(x=>x.identityFlag).length,13,
 "identity warnings should drop from historical 25 to 13 after source-backed corrections");
assert.equal(main.familyGrouping.missingReferenceStages[0].name,"Furrva");
assert.equal(main.familyGrouping.missingReferenceStages[0].status,
 "source confirmed; not present as a current actionable sprite review entry");
assert.ok(main.familyGrouping.familyNotes[one("fakemon:beelitant:").family].includes("Furrva"));
assert.equal(one("fakemon:beelitant:").evolutionStageOrder,2);
assert.equal(one("fakemon:kocomb-1:").displayName,"Kocomb — militant form");
assert.equal(one("fakemon:kocomb:5").displayName,"Kocomb — normal form");
assert.equal(one("fakemon:granebee:").evolutionStageOrder,2);
assert.equal(one("fakemon:yamask-2:").family,one("fakemon:platerigus:").family);
assert.equal(one("fakemon:spritzee-1:").family,one("fakemon:traumatisse:").family);
assert.notEqual(one("fakemon:yamask-2:").family,one("fakemon:spritzee-1:").family);
assert.notEqual(one("fakemon:falinks-1:").family,one("fakemon:spritzee-1:").family);
assert.equal(one("fakemon:falinks-1:").name,"Falinks");
assert.equal(one("fakemon:buneary-1:").name,"Buneary");
assert.equal(one("fakemon:lopunny-1:").name,"Lopunny");
assert.equal(one("fakemon:spinarak-1:").name,"Spinarak");
assert.equal(one("fakemon:ariados-1:").name,"Ariados");
assert.equal(one("compare:rainther:1").type1,"Water");
assert.equal(one("compare:rainther:2").type1,"Water");
assert.equal(one("compare:pythonovas:1").family,"Hissiorite → Cobarett → Pythonova");
for(const x of allRows){
 assert.ok(!x.family.includes("Platerigus → Mikitarian → Traumatisse"),"fictional mix persisted "+x.id);
 assert.ok(!x.family.includes("Beelitant → Kocomb → Granebee"),"reversed bee evolution "+x.id);
 if(x.sourceRegionLabel)assert.ok(x.originalSourceName&&x.canonicalSpeciesName,"missing original source/verified species attribution");
}
assert.ok(html.includes("Missing from current review: ")&&html.includes("Verified branch: "));
const reconciliation=JSON.parse(read("review/identity-family-reconciliation-2026-10-23.json"));
assert.equal(reconciliation.totals.metadataEdits,27);
assert.equal(reconciliation.totals.approvedVotesChanged,0);
console.log("PASS — 27 source reconciliations, 12 cleared warnings, 13 remaining checks, correct branched bee and Mikitari families; decisions preserved");

console.log("PASS — syntax, 166 protected votes, 74 recovered pairs, 39 families, five missing shiny sets, safe merging and read-only master reviewer");
