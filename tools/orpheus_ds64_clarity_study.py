#!/usr/bin/env python3
"""Two controlled, source-tile-authentic DS64 readability studies.

Both use the previously verified exact native DS4bpp index buffers; all edits are
on existing opaque interior pixels and preserve source form, geometry, palette,
outlines and all approvals. No external art, generative images or ROM work.
"""
from __future__ import annotations
from collections import Counter
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import hashlib, json, struct, base64, math

ROOT=Path("review/candidates/orpheus-2026-11-09-UNAPPROVED/targeted-final-local-pixels")
OUT=Path("report/clarity_pass")
OUT.mkdir(parents=True,exist_ok=True)
BASELINES={
 "flygon_front":{"sha":"0d906469534f897c50813673ba3473c54173dc975cdaceb93a371e80f6df6d3d","palette":"4a6eb782f3db86decea8d0892a3e342fa8451a2932744b89a5d328a838e0efaf","roi":(16,9,49,38)},
 "vibrava_back":{"sha":"5b58eb559e085e08e2da013c804b265a9ecdb8179b84b76e1bc097d8972b301b","palette":"02fa57e49ff490c8035368812c872b53b05c0bc1b439438bad307858369c83ce","roi":(29,10,60,48)}
}
# Controlled source-aware tweaks; these are intentionally interior palette pixels.
# x,y, target palette index, eligible source index set, reason.
FIX={
"flygon_front":[
 (24,14,2,[15],"Eye pupil: 2px coherent dark focal point"),
 (24,16,4,[5],"Eye-to-muzzle shadow plane"),
 (24,17,4,[5],"Eye-to-muzzle shadow plane"),
 (26,19,3,[4],"Join muzzle shadow into stable dark cluster"),
 (35,26,8,[5],"Clear front-wing attachment from brown neck"),
 (36,26,8,[10],"Darken wing border at attachment"),
 (37,26,9,[10],"Bridge dark rim to pale membrane"),
 (35,28,8,[11],"Join forewing outline to wing attachment"),
 (34,24,8,[10],"Clean wing leading-edge start"),
 (34,25,8,[10],"Clean wing leading-edge continuation"),
],
"vibrava_back":[
 (46,14,3,[2],"Left antenna curl stem shadow"),
 (47,14,3,[2],"Left antenna curl stem shadow"),
 (53,14,5,[6],"Right antenna curl light-to-mid shading"),
 (54,13,4,[5],"Right antenna curl darker midtone"),
 # pale cyan wing: preserve membrane silhouette while adding light in-wing veins
 (32,43,9,[11],"Wing-root vein anchor"),
 (30,44,10,[11],"Wing vein 1"),
 (28,45,10,[11],"Wing vein 1"),
 (26,46,10,[11],"Wing vein 1"),
 (24,46,10,[11],"Wing vein 1"),
 (22,47,10,[11],"Wing vein 1"),
 (20,48,10,[11],"Wing vein 1"),
 (18,48,10,[11],"Wing vein 1"),
 (16,49,10,[11],"Wing vein 1"),
 (31,49,9,[11],"Wing vein 2 root"),
 (28,50,10,[11],"Wing vein 2"),
 (25,50,10,[11],"Wing vein 2"),
 (22,51,10,[11],"Wing vein 2"),
 (19,51,10,[11],"Wing vein 2"),
 ]}
def hashfile(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for part in iter(lambda:f.read(1024*1024),b""):h.update(part)
 return h.hexdigest()
def idxdecode(buf):
 assert len(buf)==2048
 a=[0]*4096;n=0
 for ty in range(0,64,8):
  for tx in range(0,64,8):
   for dy in range(8):
    for dx in range(0,8,2):
     v=buf[n];n+=1
     a[(ty+dy)*64+tx+dx]=v&15
     a[(ty+dy)*64+tx+dx+1]=v>>4
 assert n==2048
 return a
def idxpack(a):
 assert len(a)==4096
 out=bytearray()
 for ty in range(0,64,8):
  for tx in range(0,64,8):
   for dy in range(8):
    for dx in range(0,8,2):
     v0=a[(ty+dy)*64+tx+dx];v1=a[(ty+dy)*64+tx+dx+1]
     assert 0<=v0<16 and 0<=v1<16
     out.append(v0|(v1<<4))
 assert len(out)==2048 and idxdecode(bytes(out))==a
 return bytes(out)
def fromword(v):
 return tuple(round(((v>>(5*j))&31)*255/31) for j in range(3))
def fromindex(a,palette):
 words=struct.unpack("<16H",palette)
 im=Image.new("RGBA",(64,64))
 im.putdata([(*fromword(words[v]),255) if v else (0,0,0,0) for v in a])
 return im
def classof(index):
 if index==0:return "transparent"
 if index==1:return "outline"
 if 2<=index<=6:return "body"
 if 7<=index<=11:return "wing"
 return "accent"
def cleanup_shade_clusters(a,roi,limit):
 # This is optional B candidate only; no outline or alpha pixels are touched.
 x0,y0,x1,y1=roi
 proposed=[]
 for y in range(max(1,y0),min(63,y1)):
  for x in range(max(1,x0),min(63,x1)):
   k=y*64+x;v=a[k]
   if v<=1:continue
   if any(a[y2*64+x2]==0 for x2,y2 in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]):continue
   if x<=27 and y<=21 and roi[0]<20:continue # preserve eye details in Flygon
   neighbors=[a[(y+dy)*64+x+dx] for dy in (-1,0,1) for dx in (-1,0,1) if dx or dy]
   # never cross class boundaries: one should not blur insect body into wing
   matching=[i for i in neighbors if classof(i)==classof(v)]
   if len(matching)<6:continue
   val,cnt=Counter(matching).most_common(1)[0]
   if val!=v and cnt>=4:
    proposed.append((cnt,x,y,v,val))
 # Only the strongest local speckles, deterministic order.
 proposed.sort(key=lambda z:(-z[0],z[2],z[1]))
 edits=[]
 for cnt,x,y,old,new in proposed[:limit]:
  k=y*64+x
  if a[k]!=old:continue
  a[k]=new
  edits.append(dict(x=x,y=y,before=old,after=new,neighbors=cnt,reason="Optional same-material shading-cluster cleanup"))
 return edits
fontpath=next((p for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf","/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"] if Path(p).exists()),None)
def font(sz):return ImageFont.truetype(fontpath,sz) if fontpath else ImageFont.load_default()
def display(img,size):
 b=Image.new("RGBA",(size,size),(237,243,247,255))
 b.alpha_composite(img.resize((size,size),Image.Resampling.NEAREST))
 return b.convert("RGB")
def zoomroi(img,rect,scale):
 region=img.crop(rect).resize(((rect[2]-rect[0])*scale,(rect[3]-rect[1])*scale),Image.Resampling.NEAREST)
 bg=Image.new("RGBA",region.size,(237,243,247,255));bg.alpha_composite(region)
 return bg.convert("RGB")
W=950;ROW=466;H=115+2*ROW
sheet=Image.new("RGB",(W,H),"#f5f7f9")
d=ImageDraw.Draw(sheet)
d.text((20,17),"MERCURY REDUX • REAL ORPHEUS DS64 CLARITY STUDY",font=font(22),fill="#263746")
d.text((20,49),"Original verified indexed pixels  →  feature-guided  →  optional microcluster cleanup",font=font(13),fill="#566879")
d.text((20,72),"Two normal views only • same silhouettes, original palettes and source anatomy • NO APPROVAL",font=font(13),fill="#a05248")
results=[]
for ri,name in enumerate(("flygon_front","vibrava_back")):
 info=BASELINES[name]
 path=ROOT/f"{name}_4bpp_tiles.bin"
 palpath=ROOT/f"{name}_bgr555_palette.bin"
 pngpath=ROOT/f"{name}_targeted64.png"
 assert path.exists() and palpath.exists() and pngpath.exists()
 assert hashfile(path)==info["sha"] and hashfile(palpath)==info["palette"]
 pal=palpath.read_bytes()
 original=idxdecode(path.read_bytes())
 baseline=Image.open(pngpath).convert("RGBA")
 assert fromindex(original,pal).tobytes()==baseline.tobytes(),f"Input sprite/binary mismatch for {name}"
 guided=original[:]
 hand=[]
 for x,y,new,allowed,reason in FIX[name]:
  k=y*64+x;before=guided[k]
  assert before in allowed,(name,x,y,before,allowed)
  assert before not in (0,1) and new not in (0,1) and new!=before
  assert (x,y) not in {(e['x'],e['y']) for e in hand}
  guided[k]=new
  hand.append(dict(x=x,y=y,before=before,after=new,reason=reason))
 cleaned=guided[:]
 cleanup=cleanup_shade_clusters(cleaned,info["roi"],22 if name=="flygon_front" else 13)
 # Enforce alpha/outline identity against original on both variants.
 row={"name":name,"handEdits":hand,"cleanupEdits":cleanup,"variants":{}}
 for label,arr in (("guided",guided),("clustered",cleaned)):
  assert all((a==0)==(b==0) and (a==1)==(b==1) for a,b in zip(original,arr))
  tile=idxpack(arr)
  art=fromindex(arr,pal)
  assert art.getchannel("A").tobytes()==baseline.getchannel("A").tobytes()
  assert len(set(art.getdata()))<=16
  assert fromindex(idxdecode(tile),pal).tobytes()==art.tobytes()
  p=OUT/f"{name}_{label}64.png";art.save(p,optimize=True)
  t=OUT/f"{name}_{label}_4bpp_tiles.bin";t.write_bytes(tile)
  c=OUT/f"{name}_{label}_bgr555_palette.bin";c.write_bytes(pal)
  assert c.read_bytes()==pal
  change=sum(a!=b for a,b in zip(original,arr))
  row["variants"][label]=dict(changedPixels=change,tileSHA256=hashfile(t),
    pngSHA256=hashfile(p),tilesBytes=2048,paletteBytes=32,alphaAndOutlineUnchanged=True,approved=False,romIntegrated=False)
 # Visual contact sheet, 64→4x panels and 1x native insets
 y=110+ri*ROW
 d.rounded_rectangle((10,y,W-10,y+ROW-11),radius=12,outline="#ced8e0",fill="white",width=2)
 d.text((21,y+12),name.replace("_"," ").upper(),font=font(18),fill="#263846")
 for ci,(label,arr) in enumerate([("CURRENT",original),("GUIDED",guided),("CLUSTERED",cleaned)]):
  xx=20+ci*300
  d.text((xx,y+45),label+" • native source-index art",font=font(13),fill="#566879")
  sheet.paste(display(fromindex(arr,pal),240),(xx,y+64))
  sheet.paste(display(fromindex(arr,pal),64),(xx+96,y+314))
  d.text((xx,y+391),f"{sum(a!=b for a,b in zip(original,arr))} pixels changed from current",font=font(12),fill="#536575")
 d.text((22,y+430),"ONLY colors changed • all 64×64 silhouettes / outlines / palettes unchanged",font=font(12),fill="#98524a")
 results.append(row)
 print("CLARITY_RESULT",json.dumps(row,sort_keys=True))
sheetpath=OUT/"orpheus_ds64_clarity_3way.png";sheet.save(sheetpath,optimize=True)
manifest=dict(schema="mercury-orpheus-clustered-clarity-study-v1",
  source="source-hash-pinned latest Orpheus corrected DS64 tile files",
  scope=["flygon_front","vibrava_back"],
  otherFourViewsUntouched=True,originalOrpheusArtUnchanged=True,
  historicalVotesUnchanged=True,ROMIntegrated=False,approved=False,
  rationale="guided eye/muzzle/wing and antenna/vein edits, plus optional hue-class-preserving cluster cleanup; inspect at native scale",
  warning="Technical validation does not guarantee human-readable eye/wing anatomy; if 64px still unreadable, redesign/re-pixel source at native resolution rather than repeatedly smoothing.",
  results=results)
(OUT/"clarity_study_metrics.json").write_text(json.dumps(manifest,indent=2)+"\n")
print("CLARITY_SUMMARY",json.dumps({name:{c:results[i]["variants"][c]["changedPixels"] for c in ("guided","clustered")} for i,name in enumerate(("flygon_front","vibrava_back"))}))
for filename in ["orpheus_ds64_clarity_3way.png","clarity_study_metrics.json",
   "flygon_front_guided64.png","flygon_front_clustered64.png",
   "flygon_front_guided_4bpp_tiles.bin","flygon_front_clustered_4bpp_tiles.bin",
   "flygon_front_guided_bgr555_palette.bin","flygon_front_clustered_bgr555_palette.bin",
   "vibrava_back_guided64.png","vibrava_back_clustered64.png",
   "vibrava_back_guided_4bpp_tiles.bin","vibrava_back_clustered_4bpp_tiles.bin",
   "vibrava_back_guided_bgr555_palette.bin","vibrava_back_clustered_bgr555_palette.bin"]:
 p=OUT/filename
 assert p.exists() and p.stat().st_size>0
 print("CLARITY_FILE_START",filename)
 print(base64.b64encode(p.read_bytes()).decode("ascii"))
 print("CLARITY_FILE_END",filename)
