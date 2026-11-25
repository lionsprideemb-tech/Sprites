/* R18 isolated host-only QA; no native slots or production approval. */
function createManager(screen, stock, assets, experimentalSlots=[]){
 const check=(v,m)=>{if(!v)throw Error(m)};
 check(screen==="party"||screen==="pc","SCREEN");const pc=screen==="pc";
 const reserved=pc?[0,1,2,3,4,6,7,8,10,11,12]:[0,1,2,3,4,5,6];
 const unknown=Array.from({length:16},(_,i)=>i).filter(i=>!reserved.includes(i));
 const slots=[...experimentalSlots].sort((a,b)=>a-b);
 check(new Set(slots).size===slots.length&&slots.every(i=>unknown.includes(i)),"RESERVED_OR_INVALID_SLOT");
 const key=p=>p.join(",");
 const valid=p=>Array.isArray(p)&&p.length===16&&p.every(x=>Number.isInteger(x)&&x>=0&&x<=32767);
 const shade=c=>(((c&31)+31)>>1)|(((((c>>5)&31)+11)>>1)<<5)|(((((c>>10)&31)+1)>>1)<<10);
 check(stock.length===3&&stock.every(valid),"STOCK");
 const by=new Map();for(const a of assets){check(a.productionAllowed===false&&a.normalSlot===null&&a.shadedSlot===null&&valid(a.normalPalette)&&valid(a.shadedPalette)&&a.normalPalette[0]===0&&a.normalPalette.every((c,i)=>shade(c)===a.shadedPalette[i]),"ASSET");check(!by.has(a.symbol),"DUPLICATE_SYMBOL");by.set(a.symbol,{normal:a.normalPalette.slice(),shaded:a.shadedPalette.slice()});}
 let live={version:0,banks:[],routes:[]};
 const snapshot=()=>JSON.parse(JSON.stringify(live));
 function plan(window,epoch=live.version){
  check(epoch===live.version,"STALE");check(Array.isArray(window)&&window.length<=(pc?60:6),"WINDOW_LIMIT");
  let next={version:epoch+1,banks:[],routes:[]},seen=new Set(),needed=new Map();
  function use(p){let k=key(p);if(!needed.has(k))needed.set(k,p);return k;}
  for(const r of window){check(r&&typeof r.handle==="string"&&r.handle.length>0&&!seen.has(r.handle),"HANDLE");seen.add(r.handle);check(typeof r.selected==="boolean"&&(!r.selected||pc),"SELECTED");if(r.kind==="canonical"){check(Number.isInteger(r.bank)&&r.bank>=0&&r.bank<3,"CANONICAL_BANK");next.routes.push({handle:r.handle,kind:r.kind,normal:(pc?2:3)+r.bank,shaded:pc?6+r.bank:null,active:(r.selected?6:pc?2:3)+r.bank});}else{check(r.kind==="candidate"&&typeof r.symbol==="string"&&by.has(r.symbol),"UNAUTHORIZED_SYMBOL");let a=by.get(r.symbol),normal=use(a.normal),shaded=pc?use(a.shaded):null;next.routes.push({handle:r.handle,kind:r.kind,symbol:r.symbol,normal,shaded,selected:r.selected});}}
  if(needed.size>slots.length)return {ok:false,reason:"PALETTE_EXHAUSTED",required:needed.size,capacity:slots.length,version:epoch};
  let used=new Set(),allocation=new Map();for(const old of live.banks){if(needed.has(old.key)){allocation.set(old.key,old.slot);used.add(old.slot);}}
  for(const [k,p] of needed){if(!allocation.has(k)){let slot=slots.find(i=>!used.has(i));check(slot!==undefined,"INTERNAL_CAPACITY");allocation.set(k,slot);used.add(slot);}let slot=allocation.get(k);next.banks.push({slot,key:k,palette:p.slice()});}
  for(const r of next.routes){if(r.kind==="candidate"){r.normal=allocation.get(r.normal);r.shaded=pc?allocation.get(r.shaded):null;r.active=r.selected?r.shaded:r.normal;delete r.selected;}}
  return {ok:true,version:epoch,window:JSON.parse(JSON.stringify(window)),next};
 }
 function commit(token){check(token&&token.ok===true&&token.version===live.version,"STALE_OR_FAILED");let expected=plan(token.window,token.version);check(expected.ok&&JSON.stringify(expected.next)===JSON.stringify(token.next),"TAMPERED_PLAN");live=expected.next;return snapshot();}
 function clear(){return commit(plan([]));}
 return {plan,commit,clear,snapshot,slots:slots.slice(),reserved:reserved.slice(),productionAllowed:false};
}
function runTests(pkg,auth,contract){
 const fail=(v,m)=>{if(!v)throw Error(m)},rows=pkg.rows,stock=pkg.stockBanks;
 fail(rows.length===412&&auth.rows.length===412&&contract.party.verifiedFree.length===0&&contract.pc.verifiedFree.length===0,"pins");
 const authBy=new Map(auth.rows.map(r=>[r.symbol,r]));for(const r of rows){let a=authBy.get(r.symbol);fail(a&&a.artworkKey===r.artworkKey&&a.sourceBlob===r.sourceBlob&&a.kind===r.kind&&a.acceptedBattleArt&&!a.rejectedBattleArt&&a.archiveAvailable&&!a.iconApprovalVerified&&!a.productionAllowed,"authority");}
 const c=(h,bank=0,selected=false)=>({handle:h,kind:"canonical",bank,selected});
 const q=(h,r,selected=false)=>({handle:h,kind:"candidate",symbol:r.symbol,selected});
 const stats={strictCandidateRejections:0,strictCanonicalPasses:0,hypotheticalSingleCandidatePasses:0,actualCandidateSelectionPasses:0,exactBankSharePasses:0,negativeTests:0,windowResults:{},scrollSteps:0,scrollSuccess:0,scrollExhaustion:0,cleanupPasses:0,atomicFailureChecks:0,canonicalRouteChecks:0};
 const key=x=>JSON.stringify(x);const same=(a,b)=>key(a)===key(b);
 function expectThrow(f){try{f()}catch(e){stats.negativeTests++;return}throw Error("expected rejection");}
 function validate(m,state,win,screen){let pc=screen==="pc",banks=new Map(state.banks.map(b=>[b.slot,b]));fail(banks.size===state.banks.length,"bank collision");for(const b of state.banks)fail(m.slots.includes(b.slot)&&!m.reserved.includes(b.slot),"protected overwrite");for(let i=0;i<win.length;i++){let w=win[i],r=state.routes[i];fail(r.handle===w.handle,"route identity");if(w.kind==="canonical"){fail(r.normal===(pc?2:3)+w.bank&&r.shaded===(pc?6+w.bank:null)&&r.active===(w.selected?6:pc?2:3)+w.bank,"canonical drift");stats.canonicalRouteChecks++;}else{let a=rows.find(x=>x.symbol===w.symbol);fail(same(banks.get(r.normal)?.palette,a.normalPalette)&&(!pc||same(banks.get(r.shaded)?.palette,a.shadedPalette))&&r.active===(w.selected?r.shaded:r.normal),"palette identity");}}}
 for(const screen of ["party","pc"]){let pc=screen==="pc",strict=createManager(screen,stock,rows),m=createManager(screen,stock,rows,pc?contract.pc.unknown:contract.party.unknown);
  let canonical=Array.from({length:pc?60:6},(_,i)=>c("c"+i,i%3,pc&&i%2===0));let base=strict.commit(strict.plan(canonical));validate(strict,base,canonical,screen);stats.strictCanonicalPasses+=canonical.length;
  for(const r of rows){let w=[c("stock",2,pc),q("custom",r)],before=strict.snapshot(),p=strict.plan(w);fail(!p.ok&&same(strict.snapshot(),before),"strict fail closed");stats.strictCandidateRejections++;let v=m.commit(m.plan(w));validate(m,v,w,screen);stats.hypotheticalSingleCandidatePasses++;
   if(pc){w=[c("stock",2,true),q("custom",r,true)];let next=m.commit(m.plan(w));validate(m,next,w,screen);fail(same(v.banks,next.banks),"selection reallocates banks");stats.actualCandidateSelectionPasses++;}
  }
  let repeated=Array.from({length:pc?60:6},(_,i)=>q("r"+i,rows[0],pc&&i%2===0));let rp=m.plan(repeated);fail(rp.ok&&rp.next.banks.length===(pc?2:1),"share");validate(m,m.commit(rp),repeated,screen);stats.exactBankSharePasses++;
  for(const size of pc?[3,6,30,60]:[6]){let pass=0,hold=0,min=Infinity,max=0,windows=0;for(let i=0;i<=rows.length-size;i++){let w=rows.slice(i,i+size).map((r,j)=>q("v"+j,r,pc&&j%2===0)),before=m.snapshot(),p=m.plan(w);let n=p.ok?p.next.banks.length:p.required;min=Math.min(min,n);max=Math.max(max,n);windows++;if(p.ok){validate(m,m.commit(p),w,screen);pass++;stats.scrollSuccess++;}else{fail(same(before,m.snapshot()),"failed scroll mutated");hold++;stats.scrollExhaustion++;stats.atomicFailureChecks++;}stats.scrollSteps++;}stats.windowResults[screen+"_"+size]={windows,pass,hold,minDistinctBanks:min,maxDistinctBanks:max,experimentalCapacity:m.slots.length};}
  const w=[q("a",rows[0])];let t=m.plan(w),tampered=JSON.parse(JSON.stringify(t));tampered.next.routes[0].active=0;expectThrow(()=>m.commit(tampered));m.commit(t);expectThrow(()=>m.commit(t));expectThrow(()=>m.plan([q("a",rows[0]),q("a",rows[1])]));expectThrow(()=>m.plan([{handle:"x",kind:"candidate",symbol:"unknown",selected:false}]));expectThrow(()=>m.plan([c("x",3)]));expectThrow(()=>m.plan(Array.from({length:pc?61:7},(_,i)=>c("x"+i))));expectThrow(()=>createManager(screen,stock,rows,[0]));expectThrow(()=>createManager(screen,stock,rows,[16]));expectThrow(()=>createManager(screen,stock,rows,[m.slots[0],m.slots[0]]));expectThrow(()=>m.plan([],m.snapshot().version-1));if(!pc)expectThrow(()=>m.plan([q("a",rows[0],true)]));let clear=m.clear();fail(clear.routes.length===0&&clear.banks.length===0,"cleanup");stats.cleanupPasses++;strict.clear();fail(strict.snapshot().routes.length===0,"strict cleanup");stats.cleanupPasses++;
 }
 return stats;
}
if(typeof module!=="undefined")module.exports={createManager,runTests};
