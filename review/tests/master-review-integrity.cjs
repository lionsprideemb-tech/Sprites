"use strict";
const assert=require("node:assert/strict");
const fs=require("node:fs");
const vm=require("node:vm");
const path=require("node:path");
const crypto=require("node:crypto");
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
assert.equal(main.entries.length,158);
assert.equal(main.technicalHolds.length,14);
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
assert.equal(new Set(main.entries.map(x=>x.id)).size,158);
assert.equal(main.entries.concat(main.technicalHolds).filter(x=>x.identityFlag).length,5,
 "five evolution edges remain unresolved; recovered art is not an identity warning");
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
const sources=JSON.parse(read("review/verified-exception-source-pairs-2026-10-23.json"));
const newStatus=JSON.parse(read("review/identity-family-current-status-2026-10-23.json"));
assert.equal(sources.matches.length,8);
assert.equal(sources.counts.remainingIdentityWarnings,5);
assert.equal(sources.counts.promotedUnvotedArtOptions,2);
assert.equal(newStatus.totals.currentWarnings,5);
assert.equal(newStatus.resolvedCurrentBatch.length,8);
assert.equal(newStatus.previousUnresolvedSnapshot.total,13);
assert.ok(main.entries.find(x=>x.id==="compare:rainther:1"),"Rainther first original-source design not actionable");
assert.ok(main.entries.find(x=>x.id==="compare:rainther:2"),"Rainther second original-source design not actionable");
assert.ok(!votes.entries.some(x=>x.id.startsWith("compare:rainther:")),"Rainther choices must be newly undecided");
const shiny1=one("compare:pythonovas:1");
const shiny2=one("compare:pythonovas:2");
assert.equal(shiny1.identityFlag,"");
assert.equal(shiny2.identityFlag,"");
assert.equal(shiny1.category,"shiny-companion");
assert.equal(shiny2.category,"shiny-companion");
assert.equal(shiny1.type1,"Fire");
assert.equal(shiny2.type1,"Fire");
assert.ok(shiny1.shinyFront&&shiny1.shinyBack&&shiny2.shinyFront&&shiny2.shinyBack);
assert.ok(one("compare:noctowl-1:1").family.includes("Enchantment")===false);
assert.ok(one("compare:noctowl-1:1").family.includes("pairing unverified"));
const fm=main.familyGrouping.missingReferenceStages.find(x=>x.name==="Furrva");
assert.ok(fm.frontReference.includes("00uc0o89.webp")&&fm.backReference.includes("00uc0o89.webp"));
assert.equal(fm.localAssetComplete,true);
assert.equal(fm.inGameReady,false);
const furrva=JSON.parse(read("DS_CUSTOM_LIBRARY/recovered/Pokengine_Mikitari_Furrva_Source/source_manifest.json"));
assert.equal(furrva.species,"Furrva");
assert.equal(furrva.type,"Bug");
assert.equal(furrva.source_artist,"Mikitari");
assert.equal(furrva.artwork_fabricated,false);
assert.equal(furrva.game_integration_allowed,false);
assert.equal(furrva.assets.front.source_pixel_dimensions.join("x"),"34x30");
assert.equal(furrva.assets.back.source_pixel_dimensions.join("x"),"55x51");
for(const [side,data] of Object.entries(furrva.assets)){
 assert.equal(side==="front"?fm.frontLocal:fm.backLocal,data.png_path);
 const png=fs.readFileSync(path.join(root,data.png_path));
 const webp=fs.readFileSync(path.join(root,data.raw_path));
 assert.equal(png.subarray(0,8).toString("hex"),"89504e470d0a1a0a");
 assert.equal(png.readUInt32BE(16),data.source_pixel_dimensions[0]);
 assert.equal(png.readUInt32BE(20),data.source_pixel_dimensions[1]);
 assert.equal(webp.subarray(0,4).toString("ascii"),"RIFF");
 assert.equal(webp.subarray(8,12).toString("ascii"),"WEBP");
 assert.equal(crypto.createHash("sha256").update(png).digest("hex"),data.png_sha256);
 assert.equal(crypto.createHash("sha256").update(webp).digest("hex"),data.raw_sha256);
}

assert.ok(html.includes("BACK (external reference)"));
assert.ok(!main.entries.concat(main.technicalHolds).some(x=>x.id.toLowerCase().includes("furrva")));
for(const e of sources.matches){
 const row=one(e.id);
 assert.equal(row.front,e.front.path,"original front changed "+e.id);
 assert.equal(row.back,e.back.path,"back not linked "+e.id);
 assert.equal(row.dsReady,false);
 for(const asset of [e.front,e.back]){
  const full=path.join(root,asset.path);
  assert.ok(fs.existsSync(full),"missing original PNG "+asset.path);
  const bytes=fs.readFileSync(full);
  assert.equal(bytes.subarray(0,8).toString("hex"),"89504e470d0a1a0a","PNG signature");
  assert.equal(bytes.readUInt32BE(16),asset.dimensions.width,"PNG width "+asset.path);
  assert.equal(bytes.readUInt32BE(20),asset.dimensions.height,"PNG height "+asset.path);
  const digest=crypto.createHash("sha1").update(Buffer.from("blob "+bytes.length+"\0")).update(bytes).digest("hex");
  assert.equal(digest,asset.blobSHA,"Git blob hash "+asset.path);
 }
}
console.log("PASS — 8 PNG source pairs with SHA-1, original Furrva front/back PNG+WebP SHA-256, 2 Rainther options, 2 Pythonova shinies, 5 unresolved edges.");

console.log("PASS — syntax, 166 protected votes, 74 recovered pairs, 39 families, five missing shiny sets, safe merging and read-only master reviewer");
