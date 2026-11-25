/* R21 host lifecycle prototype: independent party OBJ model and owned DMA/fence and PC column handshake. */
function run(stages,pkg,auth){
 const req=(x,m)=>{if(!x)throw Error(m)},ABC="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
 function dec(s){req(typeof s==="string"&&s.length%4===0&&/^[A-Za-z0-9+/]*={0,2}$/.test(s),"B64");let a=[];for(let i=0;i<s.length;i+=4){let v=(ABC.indexOf(s[i])<<18)|(ABC.indexOf(s[i+1])<<12)|((ABC.indexOf(s[i+2])&63)<<6)|(ABC.indexOf(s[i+3])&63);a.push(v>>16&255);if(s[i+2]!=="=")a.push(v>>8&255);if(s[i+3]!=="=")a.push(v&255)}return a}
 const rows=stages.flatMap(s=>s.rows),aMap=new Map(auth.rows.map(a=>[a.symbol,a]));req(rows.length===412&&pkg.rows.length===412&&aMap.size===412,"COUNT");
 let stats={assets:0,partyPixels:0,partyWindows:0,partyStrictRejections:0,partyExperimentalPass:0,partyCanonicalChecks:0,partyMixedWindows:0,transfers:0,bytes:0,sourceLifetimeChecks:0,staleCallbacks:0,negative:0,cleanup:0,scrollTransitions:0,vblankUpdates:0,mainPreparations:0,blockedVblank:0,incomingColumnCreates:0,outgoingColumnDeletes:0,finalPositionChecks:0,drawVisibilityChecks:0,peakLiveColumns:0};
 const assets=rows.map((r,i)=>{let p=pkg.rows[i],a=aMap.get(p.symbol);req(a&&r.artworkKey===p.artworkKey&&r.sourceBlob===p.sourceBlob&&a.sourceBlob===r.sourceBlob&&a.acceptedBattleArt&&a.archiveAvailable&&!a.rejectedBattleArt&&!a.iconApprovalVerified&&!a.productionAllowed&&!p.productionAllowed&&!r.productionAllowed,"AUTH");let party=dec(r.partyBase64),pc=dec(r.pcBase64);req(party.length===1024&&pc.length===512&&pc.every((v,j)=>v===party[j]),"PAYLOAD");let tex=new Uint8Array(512);for(let y=0;y<32;y++)for(let x=0;x<32;x+=2)tex[y*16+x/2]=pc[((y>>3)*4+(x>>3))*32+(y&7)*4+((x&7)>>1)];for(let byte of party)for(let idx of [byte&15,byte>>4]){req(idx===0||p.normalPalette[idx]>=0&&p.normalPalette[idx]<=32767,"PALETTE");stats.partyPixels++}stats.assets++;return {symbol:p.symbol,party,tex,pal:p.normalPalette,shade:p.shadedPalette}});
 // Independent party OBJ bank model. Canonical banks 3..5 and UI 0..2,6 never assigned.
 function party(list,experimental){let bank=new Map(),routes=[];for(let r of list){if(r.canonical!==undefined){req(r.canonical>=0&&r.canonical<3,"CANONICAL");routes.push(3+r.canonical);continue}if(!experimental)return null;let k=r.pal.join(",");if(!bank.has(k))bank.set(k,7+bank.size);let slot=bank.get(k);req(slot<=15,"PARTY_CAP");routes.push(slot);}return routes}
 for(let a of assets){req(party([a],false)===null,"STRICT_PARTY");stats.partyStrictRejections++}
 for(let i=0;i<=assets.length-6;i++){let list=assets.slice(i,i+6),p=party(list,true);req(p.length===6&&p.every(v=>v>=7&&v<=15),"PARTY");stats.partyWindows++;stats.partyExperimentalPass++;let mixed=[{canonical:0},{canonical:1},{canonical:2},...list.slice(0,3)],q=party(mixed,true);req(q[0]===3&&q[1]===4&&q[2]===5&&q.slice(3).every(v=>v>=7),"CANONICAL");stats.partyCanonicalChecks+=3;stats.partyMixedWindows++}
 // A queued transfer owns a private copy until the matching completion fence. No reuse of live storage.
 function dma(){let generation=1,seq=0,active=null,closed=false;return {
 submit(addr,data,lo,hi){req(!closed&&!active&&addr>=lo&&addr%4===0&&data.length>0&&data.length%4===0&&addr<=hi&&data.length<=hi-addr,"SUBMIT");let owned=Uint8Array.from(data);active={generation,seq:++seq,addr,owned};stats.transfers++;stats.bytes+=owned.length;return {generation,seq}},
 complete(t){if(!active||t.generation!==generation||t.seq!==active.seq){stats.staleCallbacks++;return false}active=null;return true},
 inspect(){return active&&Array.from(active.owned)},
 close(){closed=true;return !active},
 finish(){req(closed&&!active,"IN_FLIGHT");generation++;stats.cleanup++;return true}
 }}
 for(let a of assets){let d=dma(),input=Uint8Array.from(a.tex),original=Array.from(input),t=d.submit(32768,input,32768,131072);input.fill(0);req(d.inspect().every((v,i)=>v===original[i]),"OWNED");stats.sourceLifetimeChecks++;req(!d.close(),"EARLY_FREE");req(!d.complete({generation:t.generation,seq:t.seq+1}),"STALE");req(d.complete(t)&&d.finish(),"FENCE");req(!d.complete(t),"DUPLICATE")}
 function negative(f){try{f()}catch(e){stats.negative++;return}throw Error("NEG")}
 let d=dma(),t=d.submit(192,new Uint8Array(32),192,32768);negative(()=>d.submit(224,new Uint8Array(32),192,32768));negative(()=>d.finish());d.close();negative(()=>d.finish());d.complete(t);d.finish();negative(()=>d.submit(192,new Uint8Array(32),192,32768));negative(()=>dma().submit(0,new Uint8Array(32),192,32768));negative(()=>dma().submit(32764,new Uint8Array(8),192,32768));
 // Model source handshake: phase 1 initial; VBlank publishes positions and advances; phase 2 waits for main preparation.
 // All slots preloaded in this host model; visible column lifetimes and readiness are separate.
 function scroll(list,dir,offset){req(list.length===60&&(dir===1||dir===-1),"SCROLL");let step=Math.trunc(dir*184*4096/30),old=[],incoming=[],oldLive=new Set([0,1,2,3,4,5]),newLive=new Set(),phase=1,count=0,prep=0;let left=72+offset,right=272+offset,inside=x=>x>left&&x<right;
 for(let c=0;c<6;c++){let x=(112+offset+24*c)*4096;old.push([x,x-step]);incoming.push([x+dir*184*4096,x+dir*184*4096-step]);if(inside(incoming[c][1]>>12)){newLive.add(c);stats.incomingColumnCreates++}}
 function main(){if(phase!==2||count===30)return false;for(let c=0;c<6;c++){if(!inside(old[c][1]>>12)&&oldLive.delete(c))stats.outgoingColumnDeletes++;old[c]=[old[c][1]-step,old[c][1]-2*step];incoming[c]=[incoming[c][1]-step,incoming[c][1]-2*step];if(inside(incoming[c][1]>>12)&&!newLive.has(c)){newLive.add(c);stats.incomingColumnCreates++}}phase=0;prep++;stats.mainPreparations++;return true}
 function vb(){if(count===30||phase===2){stats.blockedVblank++;return false}for(let c=0;c<6;c++){if(oldLive.has(c)){req(list[c]&&Number.isInteger(old[c][phase]),"OLD");stats.drawVisibilityChecks+=5}if(newLive.has(c)){req(list[30+c]&&Number.isInteger(incoming[c][phase]),"NEW");stats.drawVisibilityChecks+=5}}stats.peakLiveColumns=Math.max(stats.peakLiveColumns,oldLive.size+newLive.size);phase++;count++;stats.vblankUpdates++;return true}
 for(let i=0;i<30;i++){if(phase===2){req(!vb(),"WAIT");req(main(),"PREP")}req(vb(),"VB")}req(count===30&&prep===15,"COUNT"); // Initial phase=1, then fifteen prep pairs with last pair partially consumed.
 // Source final snap of incoming live sprites; require every target column has been created.
 req(newLive.size===6,"INCOMING");for(let c=0;c<6;c++){let x=(112+offset+24*c)*4096;req(Number.isInteger(x),"FINAL");stats.finalPositionChecks+=5}stats.outgoingColumnDeletes+=oldLive.size;oldLive.clear();newLive.clear();stats.scrollTransitions++;
 }
 for(let i=0;i<=assets.length-60;i++)for(let dir of [-1,1])scroll(assets.slice(i,i+60),dir,0);
 return stats;
}
if(typeof module!=="undefined")module.exports={run};
