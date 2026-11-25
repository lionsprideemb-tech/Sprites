/* R24 QA-only symbolic registry builder. No cartridge save changes. */
function build(reg,hand,master,canonicalText){
 const req=(v,m)=>{if(!v)throw Error(m)},unique=(rows,key)=>{let m=new Map();for(let r of rows){let k=key(r);req(typeof k==="string"&&k&&!m.has(k),"DUPLICATE "+k);m.set(k,r)}return m};
 let list=canonicalText.split(/\r?\n/).map(s=>s.trim()).filter(s=>s&&!s.startsWith("#"));
 req(list.length===1025&&reg.canonicalRegistry.length===1025&&reg.historicalRegistry.length===574&&reg.protectedFormGroups.length===547&&master.acceptedSourceAnchoredDesigns.length===711&&hand.rows.length===426,"COUNT");
 let canonical=unique(reg.canonicalRegistry,x=>x.key),history=unique(reg.historicalRegistry,x=>x.key),art=unique(master.acceptedSourceAnchoredDesigns,x=>x.key),routes=unique(hand.rows,x=>x.symbol),artRoutes=unique(hand.rows,x=>x.artworkKey);
 for(let i=0;i<list.length;i++)req(reg.canonicalRegistry[i].key===list[i]&&reg.canonicalRegistry[i].nationalDex===i+1,"CANONICAL ORDER "+i);
 const sentinels={SPECIES_NONE:0,SPECIES_EGG:1026,SPECIES_BAD_EGG:1027};for(let k of Object.keys(sentinels))req(!canonical.has(k),"SENTINEL");
 let formAliases=new Map(),formRows=[];for(let g of reg.protectedFormGroups){let aliases=g.constants.split(";").map(x=>x.trim());req(aliases.every(x=>/^SPECIES_[A-Z0-9_]+$/.test(x)&&!canonical.has(x)&&!(x in sentinels)),"FORM_ALIAS");let key="FORM:"+aliases[0];formRows.push({key,aliases,category:g.category,productionAllowed:false});for(let x of aliases){if(!formAliases.has(x))formAliases.set(x,[]);formAliases.get(x).push(key)}}
 let groups=unique(formRows,x=>x.key);let ambiguousFormAliases=[...formAliases].filter(([k,v])=>v.length>1);
 let nameMap=new Map();function name(n,k){if(typeof n!=="string"||!n.trim())return;let x=n.trim().toLowerCase();if(!nameMap.has(x))nameMap.set(x,new Set());nameMap.get(x).add(k)}
 for(let x of canonical.values())name(x.name,"CANON:"+x.key);
 for(let x of history.values())name(x.name,"REVIEW:"+x.key);
 let historicalRows=[],edges=[];
 for(let x of history.values()){let key="REVIEW:"+x.key;let as=x.exactArtworkKeys||[];let exact=as.filter(k=>art.has(k));let qa=exact.map(k=>artRoutes.get(k)).filter(y=>y&&y.archiveAvailable&&y.routingState==="EXACT_HISTORICAL_ART_JOIN_QA_ONLY"&&y.reviewCandidates.length===1&&y.reviewCandidates[0].reviewId===x.key);
 let parent=x.reviewAuthority?.["ER Evolution Parent"]||"",requirement=x.reviewAuthority?.["ER Requirement"]||"",override=x.reviewAuthority?.["Family/Method Override"]||"";
 if(parent){let candidates=[...(nameMap.get(parent.trim().toLowerCase())||[])];edges.push({child:key,sourceParent:parent,sourceRequirement:requirement,sourceOverride:override,parentCandidates:candidates,disposition:candidates.length===1?"DONOR_REFERENCE_UNIQUE_QA_ONLY":candidates.length?"HOLD_AMBIGUOUS_PARENT":"HOLD_UNRESOLVED_PARENT",nativeMethod:null,productionAllowed:false})}
 historicalRows.push({key,reviewId:x.key,name:x.name,classification:x.classification,status:x.currentRegistryState,sourceConstant:x.sourceConstant||null,sourceFormAliases:x.sourceConstant?formAliases.get(x.sourceConstant)||[]:[],typeStatus:x.typeStatus||null,exactArtworkKeys:exact,qaArchiveSymbols:qa.map(y=>y.symbol),productionAllowed:false});}
 let symbolicRoutes=hand.rows.map(x=>{req(art.has(x.artworkKey)&&x.productionAllowed===false&&x.speciesId===null&&x.formId===null&&x.symbol==="QA_ART_"+x.archiveSha256,"ROUTE");let review=x.reviewCandidates.map(y=>"REVIEW:"+y.reviewId);req(review.every(y=>history.has(y.slice(7))),"REVIEW ROUTE");if(x.routingState==="EXACT_HISTORICAL_ART_JOIN_QA_ONLY"){req(x.archiveAvailable&&review.length===1,"EXACT");}
 return {symbol:x.symbol,artworkKey:x.artworkKey,archiveSha256:x.archiveSha256,archiveAvailable:x.archiveAvailable,routeEvidenceBlob:x.routeEvidenceBlob,reviewCandidates:review,routingState:x.routingState,productionAllowed:false}});
 let blockedWarnings=reg.evolutionWarnings.map(x=>{req(x.evolutionEdgeConfirmed===false&&!x.romIntegrationAllowed,"WARNING");return {id:x.id,name:x.name,source:x.source,needs:x.needs,productionAllowed:false}});
 // QA serialization separate from cartridge save: exact canonical key/ID and review key, no new native numbers.
 const entries=new Map();for(let x of canonical.values())entries.set("CANON:"+x.key,{kind:"canonical",key:"CANON:"+x.key,nativeId:x.nationalDex});for(let x of historicalRows)entries.set(x.key,{kind:"review",key:x.key,nativeId:null});for(let x of groups.values())entries.set(x.key,{kind:"form",key:x.key,nativeId:null});req(entries.size===1025+574+547,"NAMESPACE");
 function encode(key){let x=entries.get(key);req(x,"UNKNOWN KEY");return JSON.stringify({schema:"mercury-symbolic-qa-v1",registry:"6715f35fc91e7d524ac39d8fbb05499640ff09f0",...x})}
 function decode(s){let x=JSON.parse(s);req(x&&x.schema==="mercury-symbolic-qa-v1"&&x.registry==="6715f35fc91e7d524ac39d8fbb05499640ff09f0","SCHEMA");let y=entries.get(x.key);req(y&&x.kind===y.kind&&x.nativeId===y.nativeId&&Object.keys(x).length===5,"MISMATCH");return y}
 function nativeLookup(id){req(Number.isInteger(id)&&id>=1&&id<=1025,"NOT CANONICAL");return "CANON:"+list[id-1]}
 function resolve(symbol,artKey){let r=routes.get(symbol);req(r&&r.artworkKey===artKey,"IDENTITY");if(!r.archiveAvailable||!["EXACT_HISTORICAL_ART_JOIN_QA_ONLY","PLACEMENT_EVIDENCE_QA_ONLY"].includes(r.routingState))return null;return {symbol:r.symbol,archiveSha256:r.archiveSha256,routeEvidenceBlob:r.routeEvidenceBlob,productionAllowed:false}}
 let roundTrips=0,negative=0,routePass=0,routeHold=0;for(let [k,v] of entries){req(JSON.stringify(decode(encode(k)))===JSON.stringify(v),"ROUNDTRIP");roundTrips++;if(v.kind==="canonical")req(nativeLookup(v.nativeId)===k,"ID");else req(v.nativeId===null,"CUSTOM ID")}
 function bad(f){try{f()}catch(e){negative++;return}throw Error("EXPECTED REJECT")}
 for(let id of [0,1026,1027,1028,-1,65535,494.5,"494",null])bad(()=>nativeLookup(id));
 for(let x of historicalRows){let v=JSON.parse(encode(x.key));v.nativeId=1028;bad(()=>decode(JSON.stringify(v)));v.nativeId=494;bad(()=>decode(JSON.stringify(v)))}
 for(let x of formRows){let v=JSON.parse(encode(x.key));v.nativeId=1026;bad(()=>decode(JSON.stringify(v)))}
 let v=JSON.parse(encode("CANON:"+list[0]));v.nativeId=2;bad(()=>decode(JSON.stringify(v)));v.nativeId=1;v.registry="wrong";bad(()=>decode(JSON.stringify(v)));bad(()=>encode("REVIEW:UNKNOWN"));bad(()=>decode("{}"));bad(()=>decode("not json"));
 for(let x of symbolicRoutes){let y=resolve(x.symbol,x.artworkKey);if(y)routePass++;else routeHold++;bad(()=>resolve(x.symbol,"wrong"))}
 req(routePass===396&&routeHold===30,"ROUTE COUNTS");
 const counts={};for(let x of edges)counts[x.disposition]=(counts[x.disposition]||0)+1;
 return {schema:"mercury-r24-symbolic-integration-v1",canonicalCount:list.length,canonicalSentinels:sentinels,canonical:reg.canonicalRegistry,formRows,ambiguousFormAliases,historicalRows,donorEvolutionReferences:edges,unresolvedEvolutionWarnings:blockedWarnings,symbolicRoutes,plannedFlygon:reg.plannedFlygon,summary:{roundTrips,negative,routePass,routeHold,historicalRows:historicalRows.length,formGroups:formRows.length,formAliasCount:formAliases.size,ambiguousFormAliases:ambiguousFormAliases.length,donorReferences:edges.length,donorReferenceCounts:counts,unresolvedEvolutionWarnings:blockedWarnings.length,canonicalNativeIdsVerified:list.length,customNativeIdsAllocated:0,artworkRecords:art.size},productionAllowed:false};
}
if(typeof module!=="undefined")module.exports={build};
