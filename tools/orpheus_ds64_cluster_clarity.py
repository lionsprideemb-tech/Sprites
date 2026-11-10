#!/usr/bin/env python3
"""Protected native-64px Flygon pixel-cluster simplification.

Only modifies tiny isolated RGB555 shade components inside the existing sprite;
leaves anatomy, eye, all indexed outlines, wing separation, silhouette, palette
and artwork decisions untouched. Always emits objective before/after metrics.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from collections import Counter,deque
import hashlib,struct,base64,json
ROOT=Path("review/candidates/orpheus-2026-11-09-UNAPPROVED/linework-polish")
OUT=Path("report/cluster_clarity")
OUT.mkdir(parents=True,exist_ok=True)
F_SHA="72c4a618daa039603c547535cba3de0aa1d2a0492884942ed9064ed9b02a6fb8"
V_SHA="f2e04270b13e6e97eae4e4488dce2e1cab7ec2576ff238ea8d0f2d6d93da01b9"
def sha(d):return hashlib.sha256(d).hexdigest()
def decode(raw):
 assert len(raw)==2048
 idx=[0]*4096;k=0
 for by in range(0,64,8):
  for bx in range(0,64,8):
   for dy in range(8):
    for dx in range(0,8,2):
     v=raw[k];k+=1
     idx[(by+dy)*64+bx+dx]=v&15
     idx[(by+dy)*64+bx+dx+1]=v>>4
 return idx
def encode(a):
 b=bytearray()
 for by in range(0,64,8):
  for bx in range(0,64,8):
   for dy in range(8):
    for dx in range(0,8,2):
     i=(by+dy)*64+bx+dx;b.append(a[i]|(a[i+1]<<4))
 assert len(b)==2048 and decode(bytes(b))==a
 return bytes(b)
def render(a,pal):
 words=struct.unpack("<16H",pal)
 def rgb(word):return tuple(round(((word>>(5*j))&31)*255/31) for j in range(3))
 im=Image.new("RGBA",(64,64))
 im.putdata([(*rgb(words[v]),255) if v else (0,0,0,0) for v in a])
 return im
def cat(v):
 if v<=1:return v
 return 2 if v<=6 else 3 if v<=11 else 4
def nbr(p,diagonal=False):
 x=p%64;y=p//64
 for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))+(((1,1),(-1,1),(1,-1),(-1,-1)) if diagonal else ()):
  xx=x+dx;yy=y+dy
  if 0<=xx<64 and 0<=yy<64:yield yy*64+xx
def tiny_components(a,roi):
 x0,y0,x1,y1=roi;covered=set();ret=[]
 for yy in range(y0,y1):
  for xx in range(x0,x1):
   p=yy*64+xx;v=a[p]
   if p in covered or cat(v) not in (2,3):continue
   q=deque([p]);covered.add(p);part=[]
   while q:
    k=q.popleft();part.append(k)
    for nb in nbr(k):
     if nb in covered or a[nb]!=v:continue
     nx=nb%64;ny=nb//64
     if x0<=nx<x1 and y0<=ny<y1:covered.add(nb);q.append(nb)
   if len(part)<=3:ret.append((v,part))
 return ret
def preserved(p,original):
 x=p%64;y=p//64;v=original[p]
 if v<=2:return True # transparent, outline, and darkest feature index
 if 20<=x<=27 and 12<=y<=17:return True # Flygon's focal eye and brow
 if 33<=x<=40 and 23<=y<=31:return True # continuity of source-authentic wing rim
 if x<19 or x>51 or y<11 or y>53:return True
 if any(original[k] in (0,1) for k in nbr(p)):return True
 return False
p=(ROOT/"flygon_front_linework_4bpp_tiles.bin").read_bytes()
palette=(ROOT/"flygon_front_linework_bgr555_palette.bin").read_bytes()
assert sha(p)==F_SHA
assert len(palette)==32
orig=decode(p);current=orig[:]
before_tiny=tiny_components(orig,(17,11,53,55))
changes=[]
for passnum in range(3):
 small=tiny_components(current,(18,11,52,54))
 candidates=[]
 for value,comp in small:
  if len(comp)>3 or any(preserved(p,orig) for p in comp):continue
  border=[]
  for k in comp:
   for n in nbr(k,True):
    if n not in comp and cat(current[n])==cat(value):
     border.append(current[n])
  if len(border)<6:continue
  (target,frequency)=Counter(border).most_common(1)[0]
  if target==value or target in (0,1,2):continue
  if frequency < (5 if len(comp)==1 else 6):continue
  if frequency/len(border)<0.34:continue
  candidates.append((-frequency,len(comp),comp[0],value,target,comp))
 candidates.sort()
 used=set()
 for negfreq,size,start,old,new,comp in candidates:
  if any(k in used or current[k]!=old for k in comp):continue
  for k in comp:
   current[k]=new;used.add(k)
   changes.append(dict(x=k%64,y=k//64,old=old,new=new,size=size,round=passnum+1))
 if not used:break
final_tiny=tiny_components(current,(17,11,53,55))
tiny_before=sum(1 for val,pts in before_tiny if len(pts)==1)
tiny_after=sum(1 for val,pts in final_tiny if len(pts)==1)
small_before=sum(1 for val,pts in before_tiny if len(pts)<=2)
small_after=sum(1 for val,pts in final_tiny if len(pts)<=2)
assert tiny_after<=tiny_before,(tiny_before,tiny_after)
assert all((a==0)==(b==0) and (a==1)==(b==1) for a,b in zip(orig,current))
assert current[14*64+23]==orig[14*64+23]==2 and current[14*64+24]==orig[14*64+24]==2
tile=encode(current)
out=render(current,palette)
base=render(orig,palette)
assert out.getchannel("A").tobytes()==base.getchannel("A").tobytes()
assert render(decode(tile),palette).tobytes()==out.tobytes()
assert sum(a!=b for a,b in zip(orig,current))==len(changes)
out.save(OUT/"flygon_front_cluster_clean64.png",optimize=True)
(OUT/"flygon_front_cluster_clean_4bpp_tiles.bin").write_bytes(tile)
(OUT/"flygon_front_cluster_clean_bgr555_palette.bin").write_bytes(palette)
vdata=(ROOT/"vibrava_back_linework_4bpp_tiles.bin").read_bytes()
vpal=(ROOT/"vibrava_back_linework_bgr555_palette.bin").read_bytes()
assert sha(vdata)==V_SHA
vimg=render(decode(vdata),vpal)
vimg.save(OUT/"vibrava_back_linework64.png",optimize=True)
(OUT/"vibrava_back_linework_4bpp_tiles.bin").write_bytes(vdata)
(OUT/"vibrava_back_linework_bgr555_palette.bin").write_bytes(vpal)

fontpath=next((s for s in ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf","/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"] if Path(s).exists()),None)
def font(n):return ImageFont.truetype(fontpath,n) if fontpath else ImageFont.load_default()
def panel(im,size):
 enlarged=im.resize((size,size),Image.Resampling.NEAREST)
 bg=Image.new("RGBA",(size,size),(239,243,247,255));bg.alpha_composite(enlarged)
 return bg.convert("RGB")
S=Image.new("RGB",(980,730),"#f5f7f9");d=ImageDraw.Draw(S)
d.text((18,17),"MERCURY REDUX / LOW-NOISE DS64 SPRITE CLEANUP",font=font(21),fill="#263846")
d.text((18,48),"Linework version vs focused shade-island cleanup, protected eye and wing boundary",font=font(13),fill="#526474")
d.text((18,71),"UNAPPROVED — source art, silhouettes, palettes, votes, engine and ROM untouched",font=font(13),fill="#9b4a44")
y=105;d.rounded_rectangle((12,y,968,494),radius=12,outline="#ced9df",fill="#ffffff",width=2)
d.text((22,y+11),f"FLYGON FRONT • {len(changes)} color-pixel edits • tiny islands {tiny_before} → {tiny_after}",font=font(16),fill="#263846")
d.text((22,y+42),"Earlier linework (4×)",font=font(13),fill="#536675")
d.text((291,y+42),"Shade-cluster cleanup (4×)",font=font(13),fill="#536675")
d.text((582,y+42),"Native detail crop",font=font(13),fill="#536675")
S.paste(panel(base,244),(22,y+63));S.paste(panel(out,244),(291,y+63))
detail=out.crop((18,10,50,42)).resize((256,256),Image.Resampling.NEAREST)
b=Image.new("RGBA",detail.size,(238,243,247,255));b.alpha_composite(detail)
S.paste(b.convert("RGB"),(583,y+63));S.paste(panel(out,64),(860,y+101))
d.text((844,y+185),"Native 1×",font=font(13),fill="#536675")
d.text((22,y+342),"Same 2,048-byte tiled DS4bpp format and identical 32-byte BGR555 palette",font=font(13),fill="#366b55")
y=517;d.rounded_rectangle((12,y,968,711),radius=12,outline="#ced9df",fill="#ffffff",width=2)
d.text((22,y+11),"VIBRAVA BACK • latest improved connected wing-linework retained",font=font(16),fill="#263846")
S.paste(panel(vimg,138),(22,y+39))
S.paste(panel(vimg,64),(182,y+75))
d.text((268,y+72),"No new edits. More legible pale wing membrane and antenna contours.",font=font(13),fill="#526475")
d.text((268,y+99),"Other four family views remain exactly as before.",font=font(13),fill="#526475")
d.text((22,y+165),"No artwork approval or game insertion. Native 64px readability remains subject to visual review.",font=font(12),fill="#9a4a43")
path=OUT/"orpheus_ds64_low_noise_comparison.png";S.save(path,optimize=True)
report={
"schema":"mercury-orpheus-ds64-visual-noise-reduction-v1",
"view":"flygon_front","sourceTileSHA256":F_SHA,"candidateTileSHA256":sha(tile),
"changedPixels":len(changes),"tinyComponentsBefore":tiny_before,"tinyComponentsAfter":tiny_after,
"smallComponentsBefore":small_before,"smallComponentsAfter":small_after,
"eyeProtected":True,"wingRimProtected":True,"silhouetteAndOutlinePreserved":True,"palettePreserved":True,
"vibravaTileSHA256Unchanged":V_SHA,"approved":False,"romIntegrated":False,
"changeLog":changes,
"caveat":"Pixel-cluster metrics cannot replace visual appraisal; a genuinely clear head/forewing may still require a deliberate 64px manual artist redraw."
}
(OUT/"cluster_qa.json").write_text(json.dumps(report,indent=2)+"\n")
print("CLUSTER_SUMMARY",json.dumps({k:report[k] for k in ("changedPixels","tinyComponentsBefore","tinyComponentsAfter","smallComponentsBefore","smallComponentsAfter","approved","romIntegrated")}))
for filename in ["orpheus_ds64_low_noise_comparison.png","cluster_qa.json",
 "flygon_front_cluster_clean64.png","flygon_front_cluster_clean_4bpp_tiles.bin","flygon_front_cluster_clean_bgr555_palette.bin",
 "vibrava_back_linework64.png","vibrava_back_linework_4bpp_tiles.bin","vibrava_back_linework_bgr555_palette.bin"]:
 p=OUT/filename
 print("CLUSTER_FILE_START",filename)
 print(base64.b64encode(p.read_bytes()).decode("ascii"))
 print("CLUSTER_FILE_END",filename)
