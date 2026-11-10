#!/usr/bin/env python3
"""Final research-only pixel audit and mobile approval *comparison*, no votes.

All work occurs in the isolated GitHub Actions job. It never writes an approval,
sprite source, engine resource, or game file. PNGs and JSON go to report only.
"""
from __future__ import annotations
from collections import Counter, deque
from pathlib import Path
import base64
import hashlib
import json
import math
import struct
from PIL import Image, ImageDraw, ImageFont

R = Path("report")
ORIG = Path("safepng")
PRIOR = R/"ds64_individual_recolors"
FINAL = R/"ds64_readability"
OUT = R/"ds64_final_visual_review"
OUT.mkdir(parents=True,exist_ok=True)
RAR = Path("orpheus-original-resources.rar")
RAR_SHA = "72539b83b55a427c4adcdf2f3e5397cc28371875a720f687ffcf4e2a6d803ef9"
STAGES = [
 (328,"trapinch","Trapinch","Bug", "Terracotta / sand"),
 (329,"vibrava","Vibrava","Bug / Dragon", "Sage / turquoise"),
 (330,"flygon","Flygon","Bug / Dragon", "Umber / bronze / teal"),
]
KNOWN_SOURCES = {
 "328_1.png":"c63a5f3cdfc98ce4acbc618a17f4c3b52c1f8acb95b5804669fcbbdd2cc0bc3b",
 "328b_1.png":"c9aacd69ce5a0d5dfa0d56ac01be5336e7aa392026eda6c69e3e98029cf0f749",
 "329_1.png":"5a2d79d6707f35237d8bb7ec32990b9a0c9b799d5ddbf19fe972a8d6c10f7060",
 "329b_1.png":"1182bab5ff5feb9efc5afac02e9777d7298fcdba690b09082b6b567540f7c215",
 "330_1.png":"0648e090ab0a869bf452cab5e02d2d7da3bd9454b0b400bfcedb022dd72a321c",
 "330b_1.png":"f9586b2b6504f0a4b2d79bd9597c6c59ea7df1be4e96ca1c2fb284dcaa42aa51",
}
# Eye/face and forewing crop windows are broad visual regions, not certified eye coordinates.
ROIS={
 "trapinch_front":(18,15,50,47), "trapinch_back":(27,13,59,45),
 "vibrava_front":(15,10,47,42),"vibrava_back":(26,7,58,39),
 "flygon_front":(18,8,50,40),"flygon_back":(24,12,56,44),
}
font_candidates=["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
 "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"]
font_path=next((p for p in font_candidates if Path(p).exists()),None)
F22=ImageFont.truetype(font_path,22) if font_path else ImageFont.load_default()
F18=ImageFont.truetype(font_path,18) if font_path else ImageFont.load_default()
F14=ImageFont.truetype(font_path,14) if font_path else ImageFont.load_default()

def sha(file):
 h=hashlib.sha256()
 with file.open("rb") as f:
  for part in iter(lambda:f.read(1048576),b""): h.update(part)
 return h.hexdigest()
def pcolor(word):
 return tuple(round(255*((word>>(5*i))&31)/31) for i in range(3))
def indices(buf):
 assert len(buf)==2048
 out=[0]*4096;j=0
 for ty in range(0,64,8):
  for tx in range(0,64,8):
   for dy in range(8):
    for dx in range(0,8,2):
     v=buf[j];j+=1
     out[(ty+dy)*64+tx+dx]=v&15
     out[(ty+dy)*64+tx+dx+1]=v>>4
 assert j==2048
 return out
def components_alpha(mask,conn=8):
 """Total connected-alpha islands for conservative detail-gaps detection."""
 seen=set();found=[]
 for y in range(64):
  for x in range(64):
   if (x,y) in seen or not mask[y*64+x]:continue
   q=deque([(x,y)]);seen.add((x,y));pts=[]
   while q:
    a,b=q.popleft();pts.append((a,b))
    for dx in (-1,0,1):
     for dy in (-1,0,1):
      if dx==0 and dy==0:continue
      if conn==4 and abs(dx)+abs(dy)!=1:continue
      xx,yy=a+dx,b+dy
      if not (0<=xx<64 and 0<=yy<64):continue
      if mask[yy*64+xx] and (xx,yy) not in seen:
       seen.add((xx,yy));q.append((xx,yy))
   found.append(pts)
 return sorted(found,key=len,reverse=True)
def pairwise_rgba_error(a,b):
 assert a.size==b.size==(64,64)
 u=list(a.getdata());v=list(b.getdata())
 n=sum(px[3]>0 for px in u)
 assert n
 change=sum(aa[:3]!=bb[:3] for aa,bb in zip(u,v) if aa[3])
 return round(100*change/n,2)
def panel(sheet,im,x,y,dim,background=(238,242,246,255)):
 bg=Image.new("RGBA",(dim,dim),background)
 zoom=im.resize((dim,dim),Image.Resampling.NEAREST)
 bg.alpha_composite(zoom)
 sheet.paste(bg.convert("RGB"),(x,y))
def addtext(draw,at,message,font=F14,color="#243745"):
 draw.text(at,message,font=font,fill=color)

if sha(RAR)!=RAR_SHA: raise RuntimeError("Pinned Orpheus RAR checksum mismatch")
records=[]
for num,slug,title,typing,label in STAGES:
 for role,suffix in (("front","_1"),("back","b_1")):
  name=f"{slug}_{role}"
  src=ORIG/f"{num}{suffix}.png"
  before=PRIOR/f"{name}_delta_palette64.png"
  after=FINAL/f"{name}_contrast64.png"
  tile1=PRIOR/f"{name}_4bpp_tiles.bin"
  tile2=FINAL/f"{name}_4bpp_tiles.bin"
  pal=FINAL/f"{name}_bgr555_palette.bin"
  for f in (src,before,after,tile1,tile2,pal):
   assert f.exists(),f"Missing required source {f}"
  assert sha(src)==KNOWN_SOURCES[src.name], f"Source PNG hash changed {src.name}"
  original=Image.open(src).convert("RGBA")
  a=Image.open(before).convert("RGBA")
  b=Image.open(after).convert("RGBA")
  assert original.size==(160,160) and a.size==b.size==(64,64)
  assert a.getchannel("A").tobytes()==b.getchannel("A").tobytes()
  assert set(v[3] for v in b.getdata()).issubset({0,255})
  assert tile1.read_bytes()==tile2.read_bytes(), "Pixel index changed without approved pixel correction"
  idx=indices(tile2.read_bytes())
  words=struct.unpack("<16H",pal.read_bytes())
  assert len(words)==16 and words[0]==0
  recon=[(*pcolor(words[i]),255) if i else (0,0,0,0) for i in idx]
  assert recon==list(b.getdata()), "PNG not equal to DS4bpp indexed resource"
  used=len(set(idx)-{0})
  assert used<=15 and len(set(recon))<=16
  alpha=[bool(k) for k in idx]
  islands=components_alpha(alpha)
  p1=sum(len(v)==1 for v in islands)
  p2=sum(len(v)<=2 for v in islands[1:])
  min_border=min((x for x,y in islands[0]),default=-1)
  max_border=max((x for x,y in islands[0]),default=-1)
  w,h=b.getchannel("A").getbbox()[2:] if b.getchannel("A").getbbox() else (0,0)
  # If a source limb was lost in original nearest-neighbor reduction, color edits
  # cannot reconstruct it. Mark ambiguous isolated fragments for human review.
  notes=[]
  if len(islands)>1:
   notes.append(f"{len(islands)-1} alpha components separate from main silhouette; could be antenna/wing tip")
  if p1:notes.append(f"{p1} isolated 1px alpha islands; inspect against 160px source")
  if slug=="flygon" and role=="front":
   notes.append("Face, antenna and forewing converge at native 64px; user visual review advised")
  if slug=="flygon" and role=="back":
   notes.append("Large wing membranes dominate; inspect head silhouette at 1x")
  if slug=="vibrava" and role=="front":
   notes.append("Thin antenna and wing-tip outline: confirm legibility at 1x")
  if slug=="trapinch":
   notes.append("Eye currently visible in source-preserving contrast colors; no mandatory pixel edit proven")
  bbox=b.getchannel("A").getbbox()
  assert bbox is not None
  item=dict(
   id=name,name=title,view=role,typingSource=typing,paletteStyle=label,
   sourceOriginalSHA256=sha(src),beforeSHA256=sha(before),finalSHA256=sha(after),
   width=64,height=64,sourceCanvas=[160,160],
   alphaPixelCount=sum(alpha),alphaBoundingBox=list(bbox),
   connectedComponentCount8=len(islands),
   mainComponentPixels=len(islands[0]),
   outsideMainComponentPixels=sum(map(len,islands[1:])),
   singlePixelIslands=p1,tinyAdditionalComponentsLE2=p2,
   paletteOpaqueColorsUsed=used,tileBytes=2048,paletteBytes=32,
   unchangedTileSHA256=sha(tile2),unchangedAlphaMask=True,
   optionalManualReviewNotes=notes,
   pixelEditsPerformed=0,approved=False,romIntegrated=False,
   originalRGBAColorDifferencesPercent=pairwise_rgba_error(a,b)
  )
  records.append(item)
  print("FINAL64_AUDIT",json.dumps(item,sort_keys=True))
assert len(records)==6
# Phone-oriented one-family stacked comparison sheet, no inert approval controls.
W=680; ROW=242; GAPH=33; TOP=160
H=TOP+3*(GAPH+2*ROW)+26
sheet=Image.new("RGB",(W,H),"#f3f5f6")
d=ImageDraw.Draw(sheet)
addtext(d,(18,15),"MERCURY REDUX • DELTA FLYGON",F22)
addtext(d,(18,49),"Final DS64 visual review — original family designs",F18)
addtext(d,(18,75),"Prior colors vs latest contrast refinement • front and back",F14,"#556776")
addtext(d,(18,98),"ALL UNAPPROVED • 64×64 views enlarged with nearest pixels",F14,"#9A4444")
addtext(d,(20,129),"BEFORE  (3×)",F14)
addtext(d,(238,129),"CURRENT  (3×)",F14)
addtext(d,(465,129),"DETAIL / 1× CHECK",F14)
base_y=TOP
for si,(num,slug,title,typing,label) in enumerate(STAGES):
 title_y=base_y+si*(GAPH+2*ROW)
 d.rounded_rectangle((12,title_y,W-12,title_y+GAPH+2*ROW-8),radius=12,fill="#ffffff",outline="#ced9e1",width=2)
 addtext(d,(22,title_y+7),f"{title.upper()}  •  {label}",F18)
 for vi,(role,suffix) in enumerate((("front","_1"),("back","b_1"))):
  y=title_y+GAPH+vi*ROW
  name=f"{slug}_{role}"
  before=Image.open(PRIOR/f"{name}_delta_palette64.png").convert("RGBA")
  current=Image.open(FINAL/f"{name}_contrast64.png").convert("RGBA")
  panel(sheet,before,19,y+8,190)
  panel(sheet,current,234,y+8,190)
  # Wide detail ROI of face/wing intersections, enlarged 3x; label as detail, not eye.
  crop=current.crop(ROIS[name]).resize((128,128),Image.Resampling.NEAREST)
  panel(sheet,crop,480,y+8,132)
  # Actual native resolution: insert exactly 64x64 without rescale.
  panel(sheet,current,514,y+151,64)
  addtext(d,(20,y+203),f"{role.upper()} • {records[si*2+vi]['paletteOpaqueColorsUsed']}/15 colors",F14)
  addtext(d,(442,y+203),"native 64px inset",F14,"#667686")
d.rectangle((0,H-24,W,H),fill="#e7ecf0")
addtext(d,(15,H-22),"Source/votes preserved • No KEEP/CUT recorded • No ROM changes",F14,"#843b3b")
sheet_path=OUT/"orpheus_delta_family_mobile_review.png"
sheet.save(sheet_path,optimize=True)

# Always save a machine-readable, individual-view drilldown as a candidate-only artifact.
report={
 "schema":"mercury-orpheus-DS64-final-readability-v1",
 "sourceArchiveSha256":RAR_SHA,
 "scope":"6 front/back normal unapproved sprites only",
 "nativeResolution":[64,64],
 "mobileReviewSheetSHA256":sha(sheet_path),
 "sourcePermissions":"User reported artist permission; exact attribution and scope not independently documented",
 "typingTreatment":"Source Flygon Bug/Dragon, intended Mercury Delta Flygon Bug/Ground; not altered",
 "reviewStatus":"PENDING_VISUAL_DESIGN_APPROVAL",
 "sourceArtPreserved":True,"historicalDecisionsPreserved":True,"romIntegrated":False,
 "pixelCorrectionsApplied":0,
 "correctionsRationale":"No objectively necessary pixel correction proven; existing stage-specific 4bpp tiles unchanged. Any ambiguous eye/wing detail is separately flagged for user visual judgment rather than guessed at.",
 "shinyOrIconCertified":False,
 "records":records
}
(OUT/"final_visual_audit.json").write_text(json.dumps(report,indent=2)+"\n")
print("FINAL64_SUMMARY",json.dumps({
 "views":len(records),"pixelEditsApplied":0,
 "withAlphaIslands":sum(x["connectedComponentCount8"]>1 for x in records),
 "nativeSpriteQualityChecked":6,"allHardwarePackingPassed":True,
 "mainSourceChanged":False,"userVotesChanged":False,"approved":False,"romIntegrated":False,
 "reviewSheetSHA256":sha(sheet_path)}))
print("FINAL64_BASE64_START orpheus_delta_family_mobile_review.png")
print(base64.b64encode(sheet_path.read_bytes()).decode("ascii"))
print("FINAL64_BASE64_END orpheus_delta_family_mobile_review.png")
