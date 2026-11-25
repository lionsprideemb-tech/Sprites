/* R19 host-only PC graphics capacity and RGB555/alpha pixel tests. */
function run(stages,pkg,auth){
 const req=(x,m)=>{if(!x)throw Error(m)},ABC="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
 function decode(s){req(typeof s==="string"&&s.length%4===0&&/^[A-Za-z0-9+/]*={0,2}$/.test(s),"B64");let a=[];for(let i=0;i<s.length;i+=4){let v=(ABC.indexOf(s[i])<<18)|(ABC.indexOf(s[i+1])<<12)|((ABC.indexOf(s[i+2])&63)<<6)|(ABC.indexOf(s[i+3])&63);a.push(v>>16&255);if(s[i+2]!=="=")a.push(v>>8&255);if(s[i+3]!=="=")a.push(v&255)}return a}
 const same=(a,b)=>a.length===b.length&&a.every((v,i)=>v===b[i]);
 const rows=stages.flatMap(s=>s.rows);req(rows.length===412&&pkg.rows.length===412&&auth.rows.length===412,"COUNT");
 const pixels=[];let normalChecks=0,shadeChecks=0,opaque=0,transparent=0,opaqueBlack=0;
 const shade=c=>(((c&31)+31)>>1)|(((((c>>5)&31)+11)>>1)<<5)|(((((c>>10)&31)+1)>>1)<<10);
 for(let i=0;i<rows.length;i++){
  const r=rows[i],p=pkg.rows[i],a=auth.rows[i];
  req(r.artworkKey===p.artworkKey&&r.sourceBlob===p.sourceBlob&&p.symbol===a.symbol&&a.acceptedBattleArt&&a.archiveAvailable&&!a.rejectedBattleArt&&!a.iconApprovalVerified&&!a.productionAllowed&&!p.productionAllowed&&!r.productionAllowed,"AUTH");
  let t=decode(r.pcBase64);req(t.length===512&&same(t,decode(r.partyBase64).slice(0,512))&&same(r.palette,p.normalPalette),"STAGE");
  let idx=new Uint8Array(1024),n=new Uint16Array(1024),s=new Uint16Array(1024);
  for(let y=0;y<32;y++)for(let x=0;x<32;x++){let offset=((y>>3)*4+(x>>3))*32+(y&7)*4+((x&7)>>1);let v=(t[offset]>>(4*(x&1)))&15;let j=y*32+x;idx[j]=v;n[j]=v?0x8000|p.normalPalette[v]:0;s[j]=v?0x8000|p.shadedPalette[v]:0;if(v){opaque++;if(p.normalPalette[v]===0)opaqueBlack++;req((s[j]&32767)===shade(n[j]&32767),"SHADE")}else{transparent++;req(n[j]===0&&s[j]===0,"ALPHA")}}
  // Independent traversal through sequential tiled nibble stream, check direct words including alpha.
  for(let tile=0;tile<16;tile++)for(let k=0;k<64;k++){let v=(t[tile*32+(k>>1)]>>(4*(k&1)))&15,j=((tile>>2)*8+(k>>3))*32+(tile&3)*8+(k&7);req(n[j]===(v?(32768+p.normalPalette[v]):0),"NORMAL");req(s[j]===(v?(32768+p.shadedPalette[v]):0),"SELECTED");normalChecks++;shadeChecks++}
  pixels.push({symbol:p.symbol,n,s,idx,normal:p.normalPalette,selected:p.shadedPalette,kind:r.kind});
 }
 function setFor(p,selected){return new Set(Array.from(selected?p.s:p.n).filter(v=>v&32768).map(v=>v&32767))}
 function colors(ps,states){let u=new Set();for(let i=0;i<ps.length;i++)for(let c of setFor(ps[i],states(i)))u.add(c);return u}
 function banks(ps,states){return new Set(ps.map((p,i)=>(states(i)?p.selected:p.normal).join(","))).size}
 function pack8(ps,states){let u=colors(ps,states);if(u.size>255)return false;let p=[...u],map=new Map(p.map((v,i)=>[v,i+1]));for(let i=0;i<ps.length;i++){let src=states(i)?ps[i].s:ps[i].n;for(let v of src){let idx=v?map.get(v&32767):0;req(idx===0?v===0:0x8000+p[idx-1]===v,"8BPP")}}return true}
 let results={},eightChecks=0;
 for(let size of [6,30,60]){let stat={windows:0,activeNormalMax:0,activeMixedMax:0,normalPlusSelectedMax:0,active16NormalPass:0,active16MixedPass:0,active5MixedPass:0,unionNormalMin:Infinity,unionNormalMax:0,unionMixedMin:Infinity,unionMixedMax:0,indexed8NormalPass:0,indexed8MixedPass:0,exactDirectColorPass:0};
 for(let i=0;i<=pixels.length-size;i++){let ps=pixels.slice(i,i+size),normal=()=>false,mixed=j=>j%2===0;let bn=banks(ps,normal),bm=banks(ps,mixed),both=new Set(ps.flatMap(p=>[p.normal.join(","),p.selected.join(",")])).size,un=colors(ps,normal).size,um=colors(ps,mixed).size;
 stat.windows++;stat.activeNormalMax=Math.max(stat.activeNormalMax,bn);stat.activeMixedMax=Math.max(stat.activeMixedMax,bm);stat.normalPlusSelectedMax=Math.max(stat.normalPlusSelectedMax,both);stat.active16NormalPass+=bn<=16;stat.active16MixedPass+=bm<=16;stat.active5MixedPass+=bm<=5;stat.unionNormalMin=Math.min(stat.unionNormalMin,un);stat.unionNormalMax=Math.max(stat.unionNormalMax,un);stat.unionMixedMin=Math.min(stat.unionMixedMin,um);stat.unionMixedMax=Math.max(stat.unionMixedMax,um);
 if(pack8(ps,normal)){stat.indexed8NormalPass++;eightChecks+=size*1024}if(pack8(ps,mixed)){stat.indexed8MixedPass++;eightChecks+=size*1024}
 // A packed 32x32 direct-color sprite per icon, no palette, exact transparent word and opaque bit.
 let packed=new Uint8Array(size*2048);for(let j=0;j<size;j++){let src=mixed(j)?ps[j].s:ps[j].n;for(let k=0;k<1024;k++){let v=src[k];packed[j*2048+k*2]=v&255;packed[j*2048+k*2+1]=v>>8}}
 for(let j=0;j<size;j++){let src=mixed(j)?ps[j].s:ps[j].n;for(let k=0;k<1024;k++){let off=j*2048+k*2;req((packed[off]|packed[off+1]<<8)===src[k],"DIRECT")}}
 stat.exactDirectColorPass++;
 }results[size]=stat;}
 // Simulated full screen compositing: exact 24px grid spacing and 32px icon canvas, host-defined anchor and clipping.
 // Two arrays, incoming horizontal shift 168px. Use topmost nontransparent icon, later draws win.
 const W=256,H=192;
 function render(draws){let dst=new Uint16Array(W*H);for(let d of draws){for(let y=0;y<32;y++)for(let x=0;x<32;x++){let X=d.x+x,Y=d.y+y;if(X<0||X>=W||Y<0||Y>=H)continue;let v=d.p[y*32+x];if(v&32768)dst[Y*W+X]=v}}return dst;}
 function verifyComposition(draws,dst){for(let y=0;y<H;y++)for(let x=0;x<W;x++){let expected=0;for(let i=draws.length-1;i>=0;i--){let d=draws[i],dx=x-d.x,dy=y-d.y;if(dx>=0&&dx<32&&dy>=0&&dy<32){let v=d.p[dy*32+dx];if(v&32768){expected=v;break}}}req(dst[y*W+x]===expected,"COMPOSITE")}}
 let scrollFrames=0,compositePixels=0,canonicalChecks=0;
 // Stock palette-derived synthetic canonical reference; no canonical source icon bytes claimed.
 const canonical=new Uint16Array(1024);for(let y=4;y<28;y++)for(let x=4;x<28;x++)canonical[y*32+x]=0x8000|pkg.stockBanks[0][1+(x+y)%15];
 for(let start=0;start<pixels.length;start+=30){let ps=Array.from({length:60},(_,i)=>pixels[(start+i)%pixels.length]);
 for(let shift of [0,24,48,84,120,144,168]){let draws=ps.map((p,i)=>({x:96+24*(i%6)+168*Math.floor(i/30)-shift,y:24+24*Math.floor((i%30)/6),p:(i+shift)%2?p.n:p.s}));let before=canonical.slice();draws.push({x:8,y:8,p:canonical});let dst=render(draws);verifyComposition(draws,dst);req(same(before,canonical),"CANONICAL MUTATION");for(let y=4;y<28;y++)for(let x=4;x<28;x++){req(dst[(y+8)*W+x+8]===canonical[y*32+x],"CANONICAL OVERLAY");canonicalChecks++}scrollFrames++;compositePixels+=W*H;}}
 return {icons:pixels.length,normalChecks,shadeChecks,opaque,transparent,opaqueBlack,results,eightChecks,scrollFrames,compositePixels,canonicalChecks,directSpriteBytes:2048,oneBoxDirectBytes:30*2048,twoBoxDirectBytes:60*2048,visibleBitmapBytes:W*H*2,hardware256SquareBitmapBytes:256*256*2,productionAllowed:false};
}
if(typeof module!=="undefined")module.exports={run};
