"use strict";
/* Explicit 2026-10-24 final art choices, zero changes to the 166 protected votes.
 * Strict artwork identity/source verification; never implies DS or ROM approval.
 */
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const crypto=require("node:crypto");
const root=path.resolve(__dirname,"../..");
const read=p=>fs.readFileSync(path.join(root,p));
const json=p=>JSON.parse(read(p).toString("utf8"));
const gitBlob=b=>crypto.createHash("sha1").update(Buffer.from("blob "+b.length+"\0")).update(b).digest("hex");
const files={
 "review/user-iphone-decisions-2026-10-23.json":"61c5e53c6ec81b74d192cd62a4c52c970cea15ce",
 "audit/2026-10-23/historical-decisions.json":"e8e8474cbe127ab274086ea818aa86a821c990b5"
};
for(const [p,sha] of Object.entries(files))assert.equal(gitBlob(read(p)),sha,"Protected original file changed: "+p);
const prior=json("review/user-iphone-decisions-2026-10-23.json");
const before=new Map(prior.entries.map(x=>[x.id,x]));
assert.equal(before.size,166);
assert.equal(prior.count,166);assert.equal(prior.keepCount,154);assert.equal(prior.cutCount,12);
const current=json("master-review-data.json");
assert.equal(current.entries.length,158);
assert.equal(current.technicalHolds.length,14);
const all=new Map(current.entries.map(x=>[x.id,x]));
assert.equal(current.entries.concat(current.technicalHolds).filter(x=>x.identityFlag).length,5);
const final=json("review/final-artwork-approval-overlay-2026-10-24.json");
assert.equal(final.schema,"mercury-final-artwork-approval-overlay-v1");
assert.equal(final.approvedOn,"2026-10-24");
assert.equal(final.originalBackupBlobSha,files["review/user-iphone-decisions-2026-10-23.json"]);
assert.equal(final.originalBackupCounts.count,166);
assert.equal(final.decisions.length,4);
assert.equal(final.confirmedLatestSaved.length,4);
assert.equal(current.finalArtworkApproval.file,"review/final-artwork-approval-overlay-2026-10-24.json");
assert.equal(current.finalArtworkApproval.newVotes,4);
assert.equal(current.finalArtworkApproval.remainingActionable,0);
assert.equal(current.finalArtworkApproval.ROMIntegrationAllowed,false);
const expected={
 "reconcile:wailmer-alternate-form-1":"keep",
 "reconcile:wailord-alternate-form-1":"keep",
 "compare:rainther:1":"cut",
 "compare:rainther:2":"keep"
};
const approvedArtwork={
 "reconcile:wailmer-alternate-form-1":["3a5b7da3d29d1b5c26c57613924db1233188caf9","8bd3ed0bc6f7c842d6235422d92028d53258ef85"],
 "reconcile:wailord-alternate-form-1":["223044ea3bab61de68a33089f5fa5a30ae2e9432","6997b7e48a4550bb526fd42cef884441cce36abd"],
 "compare:rainther:1":["7e471fbe59d8498e9823bbd3ec5005ca756e1615","87c3ece0feb9a9e72d097b9660f5bba907633737"],
 "compare:rainther:2":["ea41705ef94233f2f0fd100f291a4871c649b06d","d795ea9a5601608c207407e8533c941d5824e2c6"]
};
const ids=new Set();
for(const item of final.decisions){
 assert.ok(Object.hasOwn(expected,item.id),"Only four explicitly user-approved rows allowed");
 assert.ok(!ids.has(item.id),"duplicate final choice");
 ids.add(item.id);
 assert.equal(item.decision,expected[item.id]);
 assert.ok(!before.has(item.id),"An existing historical vote was overwritten");
 const row=all.get(item.id);assert.ok(row,"Not an active user choice");
 assert.equal(item.identity,row.identity);
 assert.equal(item.front_path,row.front);
 assert.equal(item.back_path,row.back);
 assert.equal(item.source,row.source);
 assert.equal(item.romIntegrationAllowed,false);
 assert.equal(item.sourceArtworkApprovalOnly,true);
 for(const [i,p] of [item.front_path,item.back_path].entries()){
  const file=path.resolve(root,p);
  assert.ok(file.startsWith(root+path.sep)&&fs.existsSync(file),"Missing original source "+p);
  const raw=fs.readFileSync(file);
  assert.equal(raw.subarray(0,8).toString("hex"),"89504e470d0a1a0a");
  assert.equal(gitBlob(raw),approvedArtwork[item.id][i],"Original source art changed: "+p);
 }
}
assert.equal(ids.size,4);
const expectedMegas={
 "compare:lucario-mega-z:1":"cut",
 "compare:lucario-mega-z:2":"keep",
 "compare:golisopod-mega:1":"keep",
 "compare:golisopod-mega:2":"cut"
};
const reconfirmed=new Set();
for(const x of final.confirmedLatestSaved){
 assert.ok(Object.hasOwn(expectedMegas,x.id),"Unknown reconfirmed artwork");
 assert.ok(!reconfirmed.has(x.id),"Duplicate Mega reaffirmation");
 reconfirmed.add(x.id);
 const old=before.get(x.id);assert.ok(old,"Old exact Mega artwork vote absent");
 assert.equal(x.decision,old.decision);
 assert.equal(x.decision,expectedMegas[x.id]);
 assert.equal(x.front_path,old.front_path);
 assert.equal(x.back_path,old.back_path);
 assert.equal(x.source,old.source);
 assert.equal(x.historicalSavedUpdated,old.updated);
 assert.equal(x.romIntegrationAllowed,false);
 assert.equal(x.archivedNotActionable,true);
}
assert.equal(reconfirmed.size,4);
const effective=new Map(before);
final.decisions.forEach(x=>effective.set(x.id,x));
assert.equal(effective.size,170);
assert.equal(current.entries.filter(x=>!effective.has(x.id)).length,0);
assert.equal(current.entries.filter(x=>effective.get(x.id)?.decision==="keep").length+
current.entries.filter(x=>effective.get(x.id)?.decision==="cut").length,158);
assert.equal([...effective.values()].filter(x=>x.decision==="keep").length,157);
assert.equal([...effective.values()].filter(x=>x.decision==="cut").length,13);
assert.equal(final.summary.pendingActionable,0);
assert.equal(final.summary.newKeeps,3);assert.equal(final.summary.newCuts,1);
assert.equal(final.safeguards.unapprovedSpriteRomintegrationProhibited,true);
console.log("PASS: 4 new exact-source creative votes, 4 unmodified archived Mega confirmations, 158/158 actionable decided, 170 effective records, 166 byte-identical protected votes, all 8 art SHA-1s, 5 identity warnings, no ROM integration.");
