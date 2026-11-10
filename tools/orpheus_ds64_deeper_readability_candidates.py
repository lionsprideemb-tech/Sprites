#!/usr/bin/env python3
"""Real DS64 refinement candidate study, not approval/ROM/art-source mutation.

Only two already-recorded PNG/tile views are read. An experimental local-palette-
index clean-up yields two hand-guided choices with exact coordinate audits.
Outer silhouettes and original 16-color palettes remain byte-for-byte unchanged.
"""
from __future__ import annotations
from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
from collections import Counter
import base64,hashlib,json,struct
SRC=Path("report/ds64_manual_microfix")
OUT=Path("report/ds64_deeper_candidates")
OUT.mkdir(parents=True,exist_ok=True)
NAMES=("vibrava_back","flygon_front")
PINNED={"vibrava_back":"52b49dbd35a2cd9bcecc45dcd05cd48bdfb91225f11e439d46b986efd8748c19",
"flygon_front":"a1b7f2113077496407f9009f3821c413a6c5a4b94edd8275b143671da96119fc"}
def sha(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for c in iter(lambda:f.read(1048576),b""):h.update(c)
 return h.hexdigest()
def unpack(blob):
 assert len(blob)==2048
 a=[0]*4096;ii=0
 for ty in range(0,64,8):
  for tx in range(0,64,8):
   for dy in range(8):
    for dx in range(0,8,2):
     v=blob[ii];ii+=1
     a[(ty+dy)*64+tx+dx]=v&15
     a[(ty+dy)*64+tx+dx+1]=v>>4
 assert ii==2048
 return a
def pack(a):
 assert len(a)==4096 and all(0<=v<=15 for v in a)
 b=bytearray()
 for ty in range(0,64,8):
  for tx in range(0,64,8):
   for dy in range(8):
    for dx in range(0,8,2):
     b.append(a[(ty+dy)*64+tx+dx]|a[(ty+dy)*64+tx+dx+1]<<4)
 assert len(b)==2048 and unpack(b)==a
 return bytes(b)
def decode(a,words):
 colors=[tuple(round(((words[v]>>(5*k))&31)*255/31) for k in range(3))+(255,) if v else (0,0,0,0) for v in a]
 im=Image.new("RGBA",(64,64))
 im.putdata(colors)
 return im
def bg(im,scale=3):
 w=im.width*scale
 backdrop=Image.new("RGBA",(w,w),(236,241,245,255))
 backdrop.alpha_composite(im.resize((w,w),Image.Resampling.NEAREST))
 return backdrop.convert("RGB")
def klass(v,name):
 if v in (0,1):return "blocked"
 if name=="vibrava_back":
  return "green" if v in (2,3,4,5,6) else "cyan"
 return "brown" if v in (2,3,4,5,12,15) else "wing"
def inroi(name,x,y):
 if name=="vibrava_back":
  return (41<=x<=57 and 10<=y<=26) or (40<=x<=61 and 27<=y<=42) or (28<=x<=54 and 34<=y<=50)
 return (17<=x<=39 and 12<=y<=37) or (36<=x<=60 and 13<=y<=33) or (3<=x<=23 and 14<=y<=32)
def protect(name,x,y,v):
 if v in (0,1):return True
 if name=="vibrava_back":
  # Eye iris, eye rim, antenna outlines, wing outer edge are hand-protected.
  if 53<=x<=60 and 31<=y<=39:return True
  return False
 # Source face eye and highlight; outline and the main bronze wing veins.
 if 21<=x<=27 and 12<=y<=17:return True
 return False
def simplify(a,name,threshold,maxchanges):
 suggestions=[]
 for y in range(1,63):
  for x in range(1,63):
   if not inroi(name,x,y):continue
   p=y*64+x;c=a[p]
   if protect(name,x,y,c):continue
   near_card=[a[p-1],a[p+1],a[p-64],a[p+64]]
   # No change to boundary or one-pixel limbs.
   if any(z==0 for z in near_card):continue
   around=[a[(y+dy)*64+x+dx] for dy in (-1,0,1) for dx in (-1,0,1) if dx or dy]
   comp=[z for z in around if klass(z,name)==klass(c,name)]
   if len(comp)<6:continue
   sorted_counts=Counter(comp).most_common()
   target,n=sorted_counts[0]
   if target==c or n<threshold:continue
   if target==1 or target==0:continue
   # 3 color clusters of same material are safer than cross-material swaps.
   support=sum(z==target for z in near_card)
   if support<2:continue
   score=n+support*.35
   suggestions.append((score,x,y,c,target,n,support))
 suggestions.sort(key=lambda t:(-t[0],t[2],t[1]))
 take=suggestions[:maxchanges]
 result=a[:]
 changes=[]
 for _,x,y,c,new,n,card in take:
  p=y*64+x
  assert result[p]==c
  result[p]=new
  changes.append({"x":x,"y":y,"before":c,"after":new,"class":"within-material-smoothing","localMajority":n,"cardinalSupport":card})
 return result,changes
def apply_hand(a,name,strong):
 # Carefully selected eye/antenna/forewing color details derived from true
 # 64px pixel-index map. Remap only already-opaque non-outline pixels.
 changes=[]
 commands=[]
 if name=="vibrava_back":
  # Preserve existing aqua eye rim; deepen eye center (green -> teal) and a glint
  commands=[
   (56,34,3,7,"iris shadow",1),
   (56,35,3,7,"iris shadow",1),
   (57,35,3,7,"iris shadow",1),
   (57,34,3,11,"eye glint",1),
   (58,34,3,9,"iris rim highlight",2),
   (58,35,3,8,"iris shade",2),
   (47,13,2,3,"antenna curl interior warmer shade",2),
   (47,14,2,3,"antenna curl continuity",2),
   (54,15,2,3,"opposite antenna inner shade",2),
   (54,16,2,3,"opposite antenna inner shade",2),
  ]
 else:
  commands=[
   # Near-eye interface: strengthen depth around pupil rather than drawing new anatomy.
   (22,14,12,15,"bright eye highlight",1),
   (21,16,12,3,"eye boundary depth",1),
   (25,17,4,3,"face beneath pupil shadow",2),
   (29,16,5,3,"forehead/crest shading",2),
   (31,16,11,10,"teal wing transition near crest",2),
   (30,18,4,3,"neck plane separation",2),
   (32,18,0,0,"protected face hole no-op",0),
  ]
 for x,y,expected,target,reason,minstrong in commands:
  if minstrong>strong or expected==0:continue
  p=y*64+x
  if a[p]!=expected:
   # No guesswork: skip if source pixel doesn't match the inspected grid.
   print("HAND_EDIT_SKIP",json.dumps({"name":name,"x":x,"y":y,"expected":expected,"observed":a[p],"reason":reason}))
   continue
  a[p]=target
  changes.append({"x":x,"y":y,"before":expected,"after":target,"class":"hand-detailed-feature","reason":reason})
 return changes
def add_boundary(a,name,strong):
 changes=[]
 if name=="flygon_front":
  # Select only pale wing membrane pixels adjacent to actual brown torso,
  # with an interior wing neighbor. Teal outline 8 improves separation.
  regions=[(17,21,41,33),(31,12,52,34)]
  source_idx=a[:]
  for y in range(12,35):
   for x in range(17,53):
    if not any(lo<=x<=hi and low<=y<=high for lo,low,hi,high in regions):continue
    if 19<=x<=30 and 12<=y<=24:continue # protect eye and face highlights
    k=y*64+x;v=source_idx[k]
    if v not in (10,11):continue
    around=[source_idx[k-1],source_idx[k+1],source_idx[k-64],source_idx[k+64]]
    if any(q==0 for q in around):continue
    brown=sum(q in (2,3,4,12) for q in around)
    wing=sum(q in (8,10,11) for q in around)
    if brown>=2 and wing>=1:
     changes.append({"x":x,"y":y,"before":v,"after":8,"class":"wing-body-divider","supportBrown":brown,"supportWing":wing})
 elif name=="vibrava_back":
  # Darken the *internal* base of the main back wing at the point it attaches.
  source_idx=a[:]
  for y in range(34,49):
   for x in range(27,48):
    k=y*64+x;v=source_idx[k]
    if v not in (9,11):continue
    near=[source_idx[k-1],source_idx[k+1],source_idx[k-64],source_idx[k+64]]
    if any(z==0 for z in near):continue
    if sum(z in (2,3,4) for z in near)>=2 and sum(z in (7,8,9,11) for z in near)>=1:
     changes.append({"x":x,"y":y,"before":v,"after":8,"class":"wing-root-definition"})
 allowed=12 if strong==1 else 22
 changes=sorted(changes,key=lambda r:(r["y"],r["x"]))[:allowed]
 for pt in changes:
  p=pt["y"]*64+pt["x"]
  assert a[p]==pt["before"]
  a[p]=pt["after"]
 return changes
def quality(a,b,name):
 assert len(a)==len(b)==4096
 changed=sum(x!=y for x,y in zip(a,b))
 assert all((x>0)==(y>0) for x,y in zip(a,b))
 assert all(x==y for x,y in zip(a,b) if x in (0,1)), "Outline or transparency changed"
 assert all(not (x!=y and not inroi(name,k%64,k//64)) for k,(x,y) in enumerate(zip(a,b)))
 return changed
font=ImageFont.load_default()
W=1160;ROW=460;H=130+ROW*2
sheet=Image.new("RGB",(W,H),"#f5f6f8");d=ImageDraw.Draw(sheet)
d.text((20,15),"MERCURY REDUX | 64px DEEPER FACE, WING & ANTENNA CLEANUP — EXPERIMENTS",font=font,fill="#263342")
d.text((20,38),"Source-derived real DS4bpp pixels: current microfix vs gentle candidate vs stronger candidate",font=font,fill="#526274")
d.text((20,61),"OUTLINES and alpha geometry unchanged • 15 opaque colors max • ALL VIEWS UNAPPROVED",font=font,fill="#9A4C45")
for x,label in [(16,"Current DS64"),(245,"Conservative"),(473,"Stronger"),(700,"Changes and bounds")]:
 d.text((x,96),label,font=font,fill="#263342")
records=[]
for i,name in enumerate(NAMES):
 oldfile=SRC/f"{name}_4bpp_tiles.bin"
 palfile=SRC/f"{name}_bgr555_palette.bin"
 previous=Image.open(SRC/f"{name}_manual_microfix64.png").convert("RGBA")
 assert sha(oldfile)==PINNED[name]
 raw=oldfile.read_bytes();palette=palfile.read_bytes()
 assert len(raw)==2048 and len(palette)==32
 words=struct.unpack("<16H",palette)
 base=unpack(raw)
 assert decode(base,words).tobytes()==previous.tobytes()
 examples=[]
 for level in (1,2):
  threshold=6 if level==1 else 5
  cap=20 if level==1 else 52
  trial,smoothing=simplify(base,name,threshold,cap)
  hands=apply_hand(trial,name,level)
  boundaries=add_boundary(trial,name,level)
  # Deduplicate modifications by true before/after source, not intermediate work.
  allchanges=[{"x":k%64,"y":k//64,"before":v,"after":trial[k]} for k,v in enumerate(base) if v!=trial[k]]
  assert len({(p["x"],p["y"]) for p in allchanges})==len(allchanges)
  changed=quality(base,trial,name)
  assert changed==len(allchanges)
  assert changed<=100
  img=decode(trial,words)
  assert len(set(img.getdata()))<=16
  tiles=pack(trial)
  assert unpack(tiles)==trial
  prefix=name+("_gentle" if level==1 else "_stronger")
  (OUT/f"{prefix}64.png").write_bytes(b"")
  img.save(OUT/f"{prefix}64.png",optimize=True)
  (OUT/f"{prefix}_4bpp_tiles.bin").write_bytes(tiles)
  (OUT/f"{prefix}_bgr555_palette.bin").write_bytes(palette)
  assert Image.open(OUT/f"{prefix}64.png").convert("RGBA").tobytes()==img.tobytes()
  record={"name":name,"level":level,"file":f"{prefix}64.png","paletteSHA256Unchanged":sha(OUT/f"{prefix}_bgr555_palette.bin")==sha(palfile),"sourcePixelsModified":False,"alphaAndOutlinePreserved":True,"originalTileSHA256":sha(oldfile),"candidateTileSHA256":sha(OUT/f"{prefix}_4bpp_tiles.bin"),"changedCount":changed,"changes":allchanges,"smoothingProposals":len(smoothing),"handDetailEdits":len(hands),"boundaryEdits":len(boundaries),"sourcePNGReadOnly":True,"approved":False,"romIntegrated":False}
  print("DEEP_CANDIDATE",json.dumps({k:v for k,v in record.items() if k!="changes"},sort_keys=True))
  records.append(record)
  examples.append((img,changed,prefix))
 y=130+i*ROW
 d.rounded_rectangle((8,y,1152,y+ROW-13),radius=12,fill="white",outline="#ccd7df",width=2)
 d.text((17,y+14),name.upper().replace("_"," "),font=font,fill="#273440")
 def put(img,x,y,size):
  backdrop=Image.new("RGBA",(size,size),(238,243,247,255))
  backdrop.alpha_composite(img.resize((size,size),Image.Resampling.NEAREST))
  sheet.paste(backdrop.convert("RGB"),(x,y))
 put(previous,16,y+46,208)
 for (img,changed,prefix),x in zip(examples,(245,474)):
  put(img,x,y+46,208)
  d.text((x,y+270),f"{changed} genuine pixel edits",font=font,fill="#9a4d46")
  put(img,x+58,y+294,64)
 d.text((707,y+48),"Palette bytes: unchanged",font=font,fill="#4b5f6d")
 d.text((707,y+70),"Alpha & outer outline: unchanged",font=font,fill="#4b5f6d")
 d.text((707,y+92),"DS 4bpp exact tile roundtrip: PASS",font=font,fill="#4b5f6d")
 d.text((707,y+114),"Only selected head/wing internal colors",font=font,fill="#4b5f6d")
 d.text((707,y+147),"These are two research variants.",font=font,fill="#914d46")
 d.text((707,y+169),"No choice is automatically selected.",font=font,fill="#914d46")
 d.text((707,y+191),"Four other sprite views unchanged.",font=font,fill="#914d46")
out=OUT/"ds64_deeper_pixel_candidates.png";sheet.save(out,optimize=True)
(OUT/"candidates_metrics.json").write_text(json.dumps({"schema":"mercury-orpheus-64px-deeper-candidate-v1","source":"unapproved real prior microfix tile assets","sourceShaPinned":PINNED,"views":records,"mainBranchTouched":False,"allCandidatesUnapproved":True,"romIntegrated":False},indent=2)+"\n")
print("DEEP_SUMMARY",json.dumps({"total":len(records),"counts":[r["changedCount"] for r in records],"approved":False,"romIntegrated":False,"sheetSHA256":sha(out)}))
print("DEEP_IMAGE_START")
print(base64.b64encode(out.read_bytes()).decode("ascii"))
print("DEEP_IMAGE_END")
