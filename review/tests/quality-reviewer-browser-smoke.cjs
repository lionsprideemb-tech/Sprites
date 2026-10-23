"use strict";
// GitHub-hosted simulated DOM/browser smoke: no Safari claim.
const assert=require("node:assert/strict");
const fs=require("node:fs");
const vm=require("node:vm");
const path=require("node:path");
const root=path.resolve(__dirname,"../..");
const data={
 "master-review-data.json":JSON.parse(fs.readFileSync(path.join(root,"master-review-data.json"),"utf8")),
 "review/user-iphone-decisions-2026-10-23.json":JSON.parse(fs.readFileSync(path.join(root,"review/user-iphone-decisions-2026-10-23.json"),"utf8")),
 "review/recovered-approved-legacy-pairs-2026-10-23.json":JSON.parse(fs.readFileSync(path.join(root,"review/recovered-approved-legacy-pairs-2026-10-23.json"),"utf8")),
 "DS_CUSTOM_LIBRARY/converted/Verified_Source_DS64_Technical_2026_10_23/technical_quality_manifest.json":
  JSON.parse(fs.readFileSync(path.join(root,"DS_CUSTOM_LIBRARY/converted/Verified_Source_DS64_Technical_2026_10_23/technical_quality_manifest.json"),"utf8"))
};
const html=fs.readFileSync(path.join(root,"master-review.html"),"utf8");
const code=html.match(/<script>([\s\S]*?)<\/script>/)?.[1];
assert.ok(code,"canonical inline reviewer script must exist");
function element(tag="div"){
 return {tagName:tag,children:[],style:{},dataset:{},classList:{add(){},remove(){}},value:"",textContent:"",innerHTML:"",disabled:false,
  appendChild(x){this.children.push(x);return x},replaceChildren(...items){this.children=items},
  remove(){},closest(){return this},focus(){},querySelectorAll(){return []},
  click(){if(this.onclick)this.onclick()}};
}
const ids=("root notice q view category qualityStat recStat recFilter qualityFilter qualityStatus shinyOnly "+
"file json csv bulk recoverLegacy prev prev2 next next2 pages bottomPages bar total done history holds identityCount legacy").split(" ");
const elements={};ids.forEach(id=>elements[id]=element(id));
elements.view.value="pending";elements.category.value="all";elements.qualityStatus.value="all";
const downloads=[],doc={
 getElementById(id){return elements[id]||(elements[id]=element(id))},
 createElement:element,body:element("body")
};
const keys=new Map(),localStorage={
 getItem(k){return keys.get(k)||null},setItem(k,v){keys.set(k,v)},
 get length(){return keys.size},key(i){return [...keys.keys()][i]}
};
let blob=null;const warnings=[],errors=[];
const ctx={
 document:doc,localStorage,window:{scrollTo(){}},URL:{createObjectURL(v){blob=v;return "blob:technical-test"},
 revokeObjectURL(){}},Blob:class {constructor(parts,opts){this.parts=parts;this.type=opts.type}},
 fetch:async url=>{if(!(url in data))return {ok:false,status:404};return {ok:true,json:async()=>data[url]}},
 console:{warn:x=>warnings.push(String(x)),error:x=>errors.push(String(x)),log(){}},
 setTimeout(){},alert(){},confirm(){return false}
};
vm.runInNewContext(code,ctx,{filename:"master-review-inline.js"});
async function run(){
 for(let i=0;i<12;i++)await Promise.resolve();
 assert.equal(errors.length,0,errors.join("; "));
 assert.ok(elements.total.textContent.includes("158 actionable"),"active choices failed to load");
 assert.ok(elements.done.textContent.includes("154 decided"),"historical user votes lost");
 assert.ok(elements.identityCount.textContent.includes("5 identity"),"unverified evolution families changed");
 assert.ok(elements.qualityStat.textContent.includes("83 audited"),"technical report inaccessible");

 elements.view.value="dsquality";elements.view.onchange();
 assert.ok(elements.root.children.length>0,"DS64 comparison groups not rendered");
 assert.equal(elements.bulk.disabled,true,"read-only quality mode could change votes");
 assert.equal(elements.category.disabled,true);
 assert.equal(elements.qualityFilter.style.display,"inline-flex");
 assert.ok(elements.pages.textContent.includes("83 source sets"));

 elements.q.value="Furrva";elements.q.oninput();
 assert.equal(elements.root.children.length,1,"Furrva source family not found");
 assert.ok(elements.root.children[0].children.length>1);
 elements.q.value="";elements.qualityStatus.value="blocked";elements.qualityStatus.onchange();
 assert.ok(elements.pages.textContent.includes("source sets"),"blocked filter not functional");

 elements.view.value="pending";elements.qualityStatus.value="all";elements.view.onchange();
 assert.equal(elements.qualityFilter.style.display,"none","quality controls visible on voting page");
 elements.json.onclick();
 assert.ok(blob&&blob.parts.length===1,"JSON backup not generated");
 const obj=JSON.parse(blob.parts.join(""));
 assert.equal(obj.schema,"mercury-sprite-decisions-v1");
 assert.equal(obj.dsTechnicalSummary.designs,83);
 assert.equal(obj.dsTechnicalSummary.noGameIntegration,true);
 const map=new Map(obj.entries.map(v=>[v.id,v]));
 const before=data["review/user-iphone-decisions-2026-10-23.json"].entries;
 for(const v of before){assert.equal(map.get(v.id)?.decision,v.decision,"Protected original vote lost: "+v.id)}
 assert.equal(map.get("compare:rainther:1")?.decision,"pending");
 assert.equal(map.get("compare:rainther:2")?.decision,"pending");
 assert.equal(errors.length,0);
 console.log("PASS browser-simulated iPhone viewer: 83 technical source sets, filters, read-only protection, JSON export and all 166 protected votes.");
}
run().catch(e=>{console.error(e);process.exitCode=1});
