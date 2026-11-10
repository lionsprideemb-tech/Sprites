#!/usr/bin/env python3
"""Research-only 64x64 indexed palette recolors of Orpheus Thracean family.

Uses existing tested DS64 pixels and original source PNGs. No source art changes,
no outline edits, no changes to any user's historical creative approvals, no ROM.
"""
from __future__ import annotations
import colorsys, hashlib, json, math, struct, base64
from collections import Counter
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

R=Path("report")
ORIG=Path("safepng")
BASE=R/"ds64_experiment"
REFINE=R/"ds64_refinement"
OUT=R/"ds64_individual_recolors"
OUT.mkdir(parents=True,exist_ok=True)
RAR=Path("orpheus-original-resources.rar")
ARCHIVE_SHA="72539b83b55a427c4adcdf2f3e5397cc28371875a720f687ffcf4e2a6d803ef9"
STAGES=[
 (328,"trapinch","Bug","Terracotta & sand",["#241D20","#54352C","#885039","#B86C45","#D69263","#EDBB80","#67523A","#A48250","#CFAB70","#E4C48C","#F5E1B4","#37595A","#5E7B77","#A5B7A8","#F4E5D3"]),
 (329,"vibrava","Bug/Dragon","Sage & turquoise",["#1C292B","#35483C","#556F4F","#718E62","#96AC85","#BFCEA5","#31525D","#4B7780","#70A5AD","#98C9CE","#D1EBE3","#826C4A","#A68E63","#D8C08C","#EFE0B6"]),
 (330,"flygon","Bug/Dragon","Umber, bronze & teal",["#211C1C","#3E302B","#614632","#805C42","#A07851","#C39A62","#2C545B","#447780","#649AA2","#8AB7BA","#C0D8CD","#6E512F","#967041","#C6A365","#E8D4A1"])
]
FONT=ImageFont.load_default()

def filehash(path):
 h=hashlib.sha256()
 with open(path,"rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()

def rgb(s):
 s=s.lstrip("#")
 return tuple(int(s[i:i+2],16) for i in (0,2,4))
def bgr555(c):
 return sum(max(0,min(31,round(c[i]*31/255)))<<(i*5) for i in range(3))
def un555(w):
 return tuple(round(((w>>(i*5))&31)*255/31) for i in range(3))
def ylum(c):
 return .2126*c[0]+.7152*c[1]+.0722*c[2]

def source_group(c):
 h,s,v=colorsys.rgb_to_hsv(*(a/255 for a in c))
 # Existing Orpheus black outlines stay dark outlines.
 if ylum(c)<42 or (v<.24 and s<.28):return "outline"
 deg=h*360
 if 34<=deg<76 and s>.20:return "wing" # Original pale yellow/green wing membrane
 if 76<=deg<171 and s>.15:return "body" # Original green insect carapace
 if 171<=deg<=275 and s>.12:return "accent" # Tiny blue/silver source accents
 if 0<=deg<34 and s>.22:return "accent"
 if ylum(c)>178:return "wing"
 return "body"

def nibble_tiles(values):
 assert len(values)==4096
 data=bytearray()
 for ty in range(0,64,8):
  for tx in range(0,64,8):
   for dy in range(8):
    for dx in range(0,8,2):
     a=values[(ty+dy)*64+tx+dx];b=values[(ty+dy)*64+tx+dx+1]
     assert 0<=a<=15 and 0<=b<=15
     data.append(a|(b<<4))
 assert len(data)==2048
 out=[0]*4096;pos=0
 for ty in range(0,64,8):
  for tx in range(0,64,8):
   for dy in range(8):
    for dx in range(0,8,2):
     v=data[pos];pos+=1
     out[(ty+dy)*64+tx+dx]=v&15
     out[(ty+dy)*64+tx+dx+1]=v>>4
 assert out==values,"DS OBJ nibble order round-trip failed"
 return bytes(data)

if filehash(RAR)!=ARCHIVE_SHA:
 raise RuntimeError("Source archive SHA does not match pinned Orpheus artwork")
font_color="#27303c"
W=1170;RH=226;H=130+6*RH
canvas=Image.new("RGB",(W,H),"#f6f6f3")
d=ImageDraw.Draw(canvas)
d.text((20,16),"MERCURY REDUX / ORPHEUS THRACEAN — THREE INDIVIDUAL DELTA PALETTES",font=FONT,fill=font_color)
d.text((20,38),"SOURCE 160px -> PRIOR TESTED 64px -> STAGE-SPECIFIC DS 4BPP PALETTE",font=FONT,fill="#4c5b66")
d.text((20,57),"Concept-only recolor; exact alpha silhouettes and coordinates unchanged. NOT APPROVED / NOT ROM-INTEGRATED.",font=FONT,fill="#8c4242")
for xx,label in [(24,"Unaltered Orpheus source"),(241,"Previous tested DS64"),(456,"Individual recolor"),(688,"Color design & compliance")]:
 d.text((xx,100),label,font=FONT,fill="#3d4f5c")
records=[]
for stage_i,(num,name,original_type,label,colors) in enumerate(STAGES):
 assert len(colors)==15
 words=[bgr555(rgb(x)) for x in colors]
 assert len(set(words))==15,f"Duplicate DS BGR555 colors in {name} palette"
 final_colors=[un555(w) for w in words]
 stage_imgs={}
 for view,suffix in [("front","_1"),("back","b_1")]:
  old=(BASE if name=="trapinch" else REFINE)/f"{name}_{view}_{'experimental_ds64' if name=='trapinch' else 'experimental_refinement64'}.png"
  original=ORIG/f"{num}{suffix}.png"
  assert original.exists() and old.exists(),(original,old)
  o=Image.open(original).convert("RGBA");p=Image.open(old).convert("RGBA")
  assert o.size==(160,160) and p.size==(64,64)
  assert set(v[3] for v in p.getdata()).issubset({0,255})
  stage_imgs[view]=(o,p)
 # Analyze stage-wide palette categories and value ranges: front and back map identically.
 stage_counts=Counter()
 for _,p in stage_imgs.values():
  stage_counts.update(px[:3] for px in p.getdata() if px[3])
 groups={}
 for color in stage_counts:
  groups.setdefault(source_group(color),[]).append(color)
 lut={}
 ramps={"outline":[0],"body":list(range(1,6)),"wing":list(range(6,11)),"accent":list(range(11,15))}
 for grp,items in groups.items():
  vals=[ylum(q) for q in items]
  lo,hi=min(vals),max(vals)
  opts=ramps[grp]
  for c in items:
   # Source brightness order is retained within each original color group.
   ratio=(ylum(c)-lo)/(hi-lo) if hi-lo>1e-5 else .52
   k=round(ratio*(len(opts)-1))
   lut[c]=opts[max(0,min(len(opts)-1,k))]
 for view,suffix in [("front","_1"),("back","b_1")]:
  o,p=stage_imgs[view]
  index=[]
  image_pixels=[]
  for px in p.getdata():
   if not px[3]:
    index.append(0);image_pixels.append((0,0,0,0))
   else:
    idx=lut[px[:3]]+1
    index.append(idx);image_pixels.append((*final_colors[idx-1],255))
  recolor=Image.new("RGBA",(64,64),(0,0,0,0))
  recolor.putdata(image_pixels)
  assert recolor.getchannel("A").tobytes()==p.getchannel("A").tobytes(),"Pixel silhouette/position altered"
  used={a for a in index if a}
  assert 5<=len(used)<=15,f"Insufficient color variation for {name} {view}: {len(used)}"
  assert len(set(recolor.getdata()))<=16
  tiles=nibble_tiles(index)
  pal_words=[0]+words
  palette=b"".join(struct.pack("<H",w) for w in pal_words)
  assert len(palette)==32
  decoded=[(*un555(pal_words[a]),255) if a else (0,0,0,0) for a in index]
  assert decoded==list(recolor.getdata()),"DS4bpp indexed tile and palette did not reproduce preview"
  fname=f"{name}_{view}_delta_palette64.png"
  recolor.save(OUT/fname,optimize=True)
  (OUT/f"{name}_{view}_4bpp_tiles.bin").write_bytes(tiles)
  (OUT/f"{name}_{view}_bgr555_palette.bin").write_bytes(palette)
  source_bgr={px[:3] for px in p.getdata() if px[3]}
  rec={
   "name":name,"view":view,"label":label,"originalType":original_type,
   "sourceImage":str(original),"sourceSHA256":filehash(original),
   "originalCanvas":[160,160],"dsCanvas":[64,64],
   "baselineSource":str(old),"baselineSHA256":filehash(old),
   "imageSHA256":filehash(OUT/fname),
   "changedOpaquePixels":sum(a[:3]!=b[:3] for a,b in zip(p.getdata(),recolor.getdata()) if a[3]),
   "opaquePixels":sum(bool(a[3]) for a in p.getdata()),
   "baselineColors":len(source_bgr),
   "outputOpaquePaletteColorsUsed":len(used),
   "outputPaletteEntriesWithTransparent":16,
   "DS4bppTilesBytes":len(tiles),"BGR555PaletteBytes":len(palette),
   "tilesSHA256":hashlib.sha256(tiles).hexdigest(),"paletteSHA256":hashlib.sha256(palette).hexdigest(),
   "samePixelPositions":True,"sameAlphaMask":True,
   "sourceArtworkUntouched":True,"approved":False,"romIntegrated":False,"licenseProofOnFile":False
  }
  records.append(rec)
  yy=126+(stage_i*2+(0 if view=="front" else 1))*RH
  d.rounded_rectangle((12,yy-5,W-12,yy+RH-10),radius=11,fill="#ffffff",outline="#d2dbe1",width=1)
  d.text((24,yy+5),f"{name.title()} | {view.upper()} | {original_type}",font=FONT,fill=font_color)
  def panel(im,x,sz):
   bg=Image.new("RGBA",(sz,sz),(239,243,247,255))
   disp=im.resize((sz,sz),Image.Resampling.NEAREST)
   bg.alpha_composite(disp)
   canvas.paste(bg.convert("RGB"),(x,yy+29))
  panel(o,24,170);panel(p,239,174);panel(recolor,456,174)
  d.text((690,yy+32),label,font=FONT,fill="#243243")
  d.text((690,yy+56),f"Original 64px color count: {len(source_bgr)}",font=FONT,fill="#455666")
  d.text((690,yy+78),f"New opaque DS colors: {len(used)} of maximum 15",font=FONT,fill="#455666")
  d.text((690,yy+100),"Canvas / alpha mask: pixel-exact match",font=FONT,fill="#455666")
  d.text((690,yy+122),"4bpp tiles: 2048 bytes / BGR555 palette: 32 bytes",font=FONT,fill="#455666")
  d.text((690,yy+144),"Palette-only redesign / no new body features",font=FONT,fill="#455666")
  d.text((690,yy+166),"UNAPPROVED — no ROM, shiny or Dex changes",font=FONT,fill="#974441")
  swatches=[colors[i] for i in (0,1,2,3,4,5,7,8,9,10,11,12,13,14)]
  for k,c in enumerate(swatches):
   x=690+28*k
   d.rectangle((x,yy+184,x+21,yy+205),fill=c,outline="#a3aab1",width=1)
  print("RECOLOR_RESULT",json.dumps(rec,sort_keys=True))
sheet=OUT/"orpheus_thracean_individual_delta_recolors.png"
canvas.save(sheet,optimize=True)
assert len(records)==6
summary={
 "schema":"mercury-thracean-individual-DS64-palette-concepts-v1",
 "originalArchiveSHA256":ARCHIVE_SHA,
 "description":"Source 160px and previous DS64 normal front/back compared with per-species distinct coordinated palettes; source anatomy and DS64 alpha masks unchanged",
 "sourcePNGChanged":False,"historicalCreativeVotesChanged":False,"approved":False,"ROMIntegrated":False,
 "shinyViewsCreated":False,"engineArchivesCreated":False,
 "individualPaletteSchemes":{stage[1]:{"style":stage[3],"swatches":stage[4]} for stage in STAGES},
 "notes":[
  "This is an intentional palette redesign, not a fidelity improvement over the original green/yellow art.",
  "Preview source rights are reported by user but independent artist-license terms still need recording before redistribution.",
  "Original Flygon Bug/Dragon; proposed Mercury target Bug/Ground remains a separate game-design approval.",
  "DS 64x64 pixel geometry and transparency remain exactly the same as earlier verified experimental PNGs.",
  "No visual approval has been requested or assumed."
 ],"records":records}
(OUT/"color_design_verification.json").write_text(json.dumps(summary,indent=2)+"\n")
print("RECOLOR_SUMMARY",json.dumps({"stages":3,"spriteViews":6,"checksPass":6,"artApproved":False,"romIntegrated":False,"imageSHA256":filehash(sheet)}))
print("RECOLOR_BASE64_START orpheus_thracean_individual_delta_recolors.png")
print(base64.b64encode(sheet.read_bytes()).decode("ascii"))
print("RECOLOR_BASE64_END orpheus_thracean_individual_delta_recolors.png")
