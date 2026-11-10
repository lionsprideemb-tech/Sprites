#!/usr/bin/env python3
"""Source-anchored microfix of ONLY Vibrava back and Flygon front 64px tile indices.

This is an unapproved QA candidate. Pixel changes are deterministic, explicitly
coordinate-listed with expected prior indices and neighbor support; original
Orpheus assets, previous 64px sprite candidates, palette, silhouette, votes, ROM
and the other four views are untouched. No AI image generation.
"""
from pathlib import Path
from collections import Counter
from PIL import Image, ImageDraw, ImageFont
import hashlib,base64,json,struct
ROOT=Path("report/ds64_readability")
OUT=Path("report/ds64_manual_microfix")
OUT.mkdir(parents=True,exist_ok=True)
SOURCES=Path("safepng")
ARCHIVE=Path("orpheus-original-resources.rar")
ARCHIVE_SHA="72539b83b55a427c4adcdf2f3e5397cc28371875a720f687ffcf4e2a6d803ef9"
assert hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()==ARCHIVE_SHA
# Each entry is x,y,expected old index,new index,label.
# Candidate positions verified on the source-locked DS64 pixel coordinate diagnostic.
# Protect silhouette by permitting only existing, nonzero internal color indices.
FIXES={
 "vibrava_back":[
   (45,15,5,2,"antenna-to-head color seam"),
   (34,36,4,2,"wing-root body outlier"),
   (35,37,4,2,"wing-root diagonal outlier"),
   (41,39,3,2,"underside shade speckle"),
   (48,41,3,2,"underside shade speckle"),
 ],
 "flygon_front":[
   (27,15,3,5,"head and crest color break"),
   (30,20,2,3,"face-to-neck single-pixel outlier"),
   (23,25,5,10,"face and forewing crossing"),
   (37,24,5,10,"forewing/body junction outlier"),
   (33,37,5,10,"inner wing/body crossing"),
   (43,15,5,11,"wing membrane noise"),
   (41,19,5,11,"inner wing membrane noise"),
   (51,24,5,11,"wing membrane noise"),
 ]
}
FONT=ImageFont.load_default()

def hashf(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for part in iter(lambda:f.read(1024*1024),b""):h.update(part)
 return h.hexdigest()

def unpack(tiles):
 assert len(tiles)==2048
 idx=[0]*4096;p=0
 for ty in range(0,64,8):
  for tx in range(0,64,8):
   for y in range(8):
    for x in range(0,8,2):
     val=tiles[p];p+=1
     idx[(ty+y)*64+tx+x]=val&15
     idx[(ty+y)*64+tx+x+1]=val>>4
 assert p==2048
 return idx

def pack(idx):
 assert len(idx)==4096
 data=bytearray()
 for ty in range(0,64,8):
  for tx in range(0,64,8):
   for y in range(8):
    for x in range(0,8,2):
     a=idx[(ty+y)*64+tx+x];b=idx[(ty+y)*64+tx+x+1]
     assert 0<=a<16 and 0<=b<16
     data.append(a|(b<<4))
 assert len(data)==2048
 assert unpack(bytes(data))==idx
 return bytes(data)

def rgb555(v):
 return tuple(round(255*((v>>(5*i))&31)/31) for i in range(3))

def make_image(idx,words):
 im=Image.new("RGBA",(64,64),(0,0,0,0))
 im.putdata([(*rgb555(words[i]),255) if i else (0,0,0,0) for i in idx])
 return im

def onbg(img,size):
 bg=Image.new("RGBA",(size,size),(239,243,246,255))
 bg.alpha_composite(img.resize((size,size),Image.Resampling.NEAREST))
 return bg.convert("RGB")

checks=[]
sheet=Image.new("RGB",(1000,890),"#f6f8fa")
draw=ImageDraw.Draw(sheet)
draw.text((22,18),"MERCURY REDUX • REAL DS64 MICRO-PIXEL CORRECTION CANDIDATES",fill="#24313e",font=FONT)
draw.text((22,40),"Exact original tiles edited at explicit coordinates • NO generated substitute artwork",fill="#516170",font=FONT)
draw.text((22,60),"Vibrava BACK and Flygon FRONT only • No approval, ROM changes, or other views edited",fill="#9b4b43",font=FONT)
for i,key in enumerate(("vibrava_back","flygon_front")):
 before_png=ROOT/f"{key}_contrast64.png"
 tiles_file=ROOT/f"{key}_4bpp_tiles.bin"
 palette_file=ROOT/f"{key}_bgr555_palette.bin"
 before=Image.open(before_png).convert("RGBA")
 assert before.size==(64,64)
 original_tiles=tiles_file.read_bytes()
 palette=palette_file.read_bytes()
 assert len(original_tiles)==2048 and len(palette)==32
 words=struct.unpack("<16H",palette)
 old=unpack(original_tiles)
 assert make_image(old,words).tobytes()==before.tobytes(),"Baseline tiles+palette mismatch"
 edit=old[:]
 changed=[]
 old_hash=hashf(tiles_file)
 for x,y,expected,target,reason in FIXES[key]:
  assert 0<=x<64 and 0<=y<64 and 2<=expected<16 and 2<=target<16
  k=y*64+x
  assert old[k]==expected,f"Expected sprite pixel mismatch {key} ({x},{y}) got {old[k]}, expected {expected}"
  neighbors=[old[k-1],old[k+1],old[k-64],old[k+64]]
  support=sum(v==target for v in neighbors)
  assert support>=3,f"Not a supported 1px cluster cleanup {key} ({x},{y}) {support}"
  assert edit[k]==expected,"repeated edit conflict"
  edit[k]=target
  changed.append({"x":x,"y":y,"before":expected,"after":target,"support":support,"reason":reason})
 assert len(changed)==len(FIXES[key]) and len(changed)<=12
 after=make_image(edit,words)
 # Exactly the same location and outline/alpha silhouette, no source rewrite.
 assert before.getchannel("A").tobytes()==after.getchannel("A").tobytes()
 assert before.getchannel("A").getbbox()==after.getchannel("A").getbbox()
 assert sum(a!=b for a,b in zip(old,edit))==len(changed)
 assert len({px for px in after.getdata() if px[3]})<=15
 new_tiles=pack(edit)
 assert new_tiles!=original_tiles
 afterfile=OUT/f"{key}_manual_microfix64.png"
 after.save(afterfile,optimize=True)
 tilefile=OUT/f"{key}_4bpp_tiles.bin";tilefile.write_bytes(new_tiles)
 palfile=OUT/f"{key}_bgr555_palette.bin";palfile.write_bytes(palette)
 assert palfile.read_bytes()==palette
 assert make_image(unpack(new_tiles),words).tobytes()==after.tobytes()
 rec={"id":key,"width":64,"height":64,
  "changedPixels":len(changed),"changedCoords":changed,
  "originalSourceArtUnchanged":True,
  "originalTileSHA256":old_hash,"editedTileSHA256":hashf(tilefile),
  "paletteSHA256Unchanged":hashf(palette_file)==hashf(palfile),
  "pixelIndicesChanged":len(changed),"alphaMaskIdentical":True,
  "paletteColorsIncludingTransparency":16,
  "opaqueColorsUsed":len({edit[p] for p in range(4096) if edit[p]!=0}),
  "tileBytes":2048,"paletteBytes":32,
  "approved":False,"romIntegrated":False,
  "pngSHA256":hashf(afterfile)}
 checks.append(rec)
 y=90+i*390
 draw.rounded_rectangle((12,y,988,y+374),radius=12,outline="#ccd8df",fill="#ffffff",width=2)
 draw.text((24,y+14),key.replace("_"," ").upper(),font=FONT,fill="#24313e")
 draw.text((24,y+34),f"BEFORE (4x)       AFTER (4x)       PIXEL-ONLY DIFF / 64px INSET",font=FONT,fill="#536171")
 sheet.paste(onbg(before,240),(24,y+66))
 sheet.paste(onbg(after,240),(285,y+66))
 # Difference tile positions shown separately with warm dots, never inside sprite.
 overlay=onbg(after,240)
 od=ImageDraw.Draw(overlay)
 for pt in changed:
  sx=pt["x"]*240/64;sy=pt["y"]*240/64
  od.rectangle((int(sx),int(sy),int(sx)+3,int(sy)+3),outline="#ff5722",width=1)
 sheet.paste(overlay,(548,y+66))
 sheet.paste(onbg(after,64),(810,y+110))
 draw.text((805,y+187),f"{len(changed)} pixel edits",font=FONT,fill="#995144")
 draw.text((805,y+205),f"{rec['opaqueColorsUsed']}/15 DS colors",font=FONT,fill="#455664")
 draw.text((805,y+226),"64×64 native",font=FONT,fill="#455664")
 draw.text((24,y+320),"Exact alpha & silhouette unchanged. Palette unchanged. Tiles re-encoded & round-tripped.",font=FONT,fill="#536171")
 draw.text((24,y+339),"NOT APPROVED • Source PNGs preserved • No ROM or other sprite views touched",font=FONT,fill="#9b4b43")
 print("PIXEL_EDIT_RESULT",json.dumps(rec,sort_keys=True))
# Four untouched views are explicitly checked for no production outputs.
for other in ("trapinch_front","trapinch_back","vibrava_front","flygon_back"):
 assert (ROOT/f"{other}_4bpp_tiles.bin").exists()
 assert not (OUT/f"{other}_4bpp_tiles.bin").exists()
report={"schema":"mercury-orpheus-ds64-exact-manual-pixel-microfix-v1",
  "scope":"Only vibrava_back and flygon_front on isolated research branch",
  "sourceArchiveSHA256":ARCHIVE_SHA,
  "sourceArtUntouched":True,"historicalVotesUntouched":True,
  "unchangedViews":["trapinch_front","trapinch_back","vibrava_front","flygon_back"],
  "userArtApprovalRecorded":False,"romIntegrated":False,
  "method":"Explicit index coordinate edit of 3/4 cardinal-neighbor-supported interior pixels, no alpha or outline edits",
  "caveat":"Micro-fixes target provable color speckle/discontinuity in real source-derived 64px sprites. They do not recover fine resolution detail or fully certify aesthetics.",
  "edits":checks
}
sheetpath=OUT/"orpheus_exact_microfix_two_view_before_after.png"
sheet.save(sheetpath,optimize=True)
(OUT/"microfix_provenance_qa.json").write_text(json.dumps(report,indent=2)+"\n")
print("PIXEL_EDIT_SUMMARY",json.dumps({"viewsChanged":2,"pixelEdits":sum(x["changedPixels"] for x in checks),"paletteUnchanged":True,"originalsUnchanged":True,"approved":False,"romIntegrated":False,"sheetSha256":hashf(sheetpath)}))
print("PIXEL_EDIT_IMAGE_START")
print(base64.b64encode(sheetpath.read_bytes()).decode("ascii"))
print("PIXEL_EDIT_IMAGE_END")
