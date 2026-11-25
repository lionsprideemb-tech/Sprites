/* Source-aligned isolated icon container prototype; not native acceptance. */
(function factory(){
const req=(v,m)=>{if(!v)throw Error(m)},u16=(a,i)=>a[i]|a[i+1]<<8,u32=(a,i)=>(a[i]|a[i+1]<<8|a[i+2]<<16|a[i+3]<<24)>>>0,ascii=(a,i)=>String.fromCharCode(...a.slice(i,i+4));
const p16=(a,i,v)=>{a[i]=v&255;a[i+1]=v>>>8&255},p32=(a,i,v)=>{p16(a,i,v);p16(a,i+2,v>>>16)},str=(a,i,s)=>{for(let j=0;j<s.length;j++)a[i+j]=s.charCodeAt(j)};
function header(m,block,size,version,bom){let a=new Uint8Array(size);str(a,0,m);p16(a,4,bom);p16(a,6,version);p32(a,8,size);p16(a,12,16);p16(a,14,1);str(a,16,block);p32(a,20,size-16);return a}
function ncgr(tiles){req(tiles.length===1024,"ICON_SIZE");let a=header("RGCN","RAHC",48+tiles.length,0x101,0xfeff);p32(a,24,0xffffffff);p32(a,28,3);p32(a,32,0x10);p32(a,36,0);p32(a,40,tiles.length);p32(a,44,24);a.set(tiles,48);return a}
function nclr(palette){req(palette.length===16&&palette.every(x=>Number.isInteger(x)&&x>=0&&x<=32767),"PALETTE");let a=header("RLCN","TTLP",72,0x100,0xfeff);p32(a,24,3);p32(a,28,0);p32(a,32,32);p32(a,36,16);palette.forEach((v,i)=>p16(a,40+i*2,v));return a}
function common(a,m,b,ver){req(a.length>=40&&ascii(a,0)===m&&u16(a,4)===0xfeff&&u16(a,6)===ver&&u32(a,8)===a.length&&u16(a,12)===16&&u16(a,14)===1&&ascii(a,16)===b&&u32(a,20)===a.length-16,"HEADER")}
function readNCGR(a){common(a,"RGCN","RAHC",0x101);req(a.length===1072&&u32(a,24)===0xffffffff&&u32(a,28)===3&&u32(a,32)===0x10&&u32(a,36)===0&&u32(a,40)===1024&&u32(a,44)===24,"CHAR_CONTRACT");return a.slice(48)}
function readNCLR(a){common(a,"RLCN","TTLP",0x100);req(a.length===72&&u32(a,24)===3&&u32(a,28)===0&&u32(a,32)===32&&u32(a,36)===16,"PLTT_CONTRACT");let p=Array.from({length:16},(_,i)=>u16(a,40+i*2));req(p.every(x=>x<=32767),"PLTT_RANGE");return p}
return {ncgr,nclr,readNCGR,readNCLR}
})
