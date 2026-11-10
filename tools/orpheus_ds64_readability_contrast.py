#!/usr/bin/env python3
"""Readability-targeted DS64 palette review for UNAPPROVED Orpheus family.

No sprite pixel positions, tile indices, original Orpheus art, approval votes,
species, or game assets change. Only DS BGR555 color words are revised on copies.
"""
from pathlib import Path
import hashlib
import json
import math
import struct
import base64
from PIL import Image, ImageDraw, ImageFont

ROOT=Path("report/ds64_individual_recolors")
SRC=Path("safepng")
OUT=Path("report/ds64_readability")
OUT.mkdir(parents=True,exist_ok=True)
ARCHIVE=Path("orpheus-original-resources.rar")
PINNED_ARCHIVE="72539b83b55a427c4adcdf2f3e5397cc28371875a720f687ffcf4e2a6d803ef9"
PALETTES={
 "trapinch": ["#19181C","#513027","#854733","#C0754C","#DC9562","#F0C48D","#614A33","#A38653","#D4B47A","#EBD09D","#F6E6BD","#2C5355","#628884","#B1C7B4","#F6EBDA"],
 "vibrava": ["#152227","#2D4435","#506E4A","#739566","#A1B892","#D1DBB8","#264954","#3D7285","#61A6B7","#A3DCE2","#DFF4ED","#785D3F","#AD8B60","#E0C28A","#F4E7C8"],
 "flygon": ["#18191D","#382820","#60412E","#895D40","#B0804E","#DAB173","#225664","#347487","#62A6B2","#A3D5D5","#DDF0E5","#6C4929","#9E7440","#D4AC69","#F1DCA9"]
}
SPECIES=[(328,"trapinch","Terracotta & sand"),(329,"vibrava","Sage & turquoise"),(330,"flygon","Umber, bronze & teal")]
FONT=ImageFont.load_default()

def sha(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for part in iter(lambda:f.read(1048576),b""):h.update(part)
 return h.hexdigest()
def word(rgb):
 return sum(max(0,min(31,round(c*31/255)))<<(5*i) for i,c in enumerate(rgb))
def unword(w):
 return tuple(round(((w>>(5*i))&31)*255/31) for i in range(3))
def readhex(h):
 return tuple(int(h[i:i+2],16) for i in (1,3,5))
def lum(rgb):
 return .2126*rgb[0]+.7152*rgb[1]+.0722*rgb[2]
def unpack_idx(tiles):
 assert len(tiles)==2048
 idx=[0]*4096;off=0
 for ty in range(0,64,8):
  for tx in range(0,64,8):
   for dy in range(8):
    for dx in range(0,8,2):
     v=tiles[off];off+=1
     idx[(ty+dy)*64+tx+dx]=v&15
     idx[(ty+dy)*64+tx+dx+1]=v>>4
 assert off==2048
 return idx
def classof(i):
 if i==0:return "transparent"
 if i==1:return "outline"
 if 2<=i<=6:return "body"
 if 7<=i<=11:return "wing"
 return "accent"
def edge_values(indices,words):
 """Directly measurable class-boundary contrast, not a vision score."""
 cmap=[unword(w) for w in words]
 buckets={q:[] for q in ("wing_body","accent_body","outline_body","wing_internal","eye_proxy")}
 for y in range(64):
  for x in range(64):
   p=y*64+x
   i=indices[p]
   if not i:continue
   for neighbor in (p+1 if x<63 else -1, p+64 if y<63 else -1):
    if neighbor<0:continue
    j=indices[neighbor]
    if not j or i==j:continue
    pair={classof(i),classof(j)}
    contrast=abs(lum(cmap[i])-lum(cmap[j]))
    if pair=={"wing","body"}:buckets["wing_body"].append(contrast)
    elif pair=={"accent","body"}:
     buckets["accent_body"].append(contrast)
     # Accent-body boundaries are a face/eye detail proxy, not a verified eye mask.
     buckets["eye_proxy"].append(contrast)
    elif pair=={"outline","body"}:buckets["outline_body"].append(contrast)
    elif pair=={"wing"}:buckets["wing_internal"].append(contrast)
 return {k:{"edgeCount":len(v),"meanLumaSeparation":round(sum(v)/len(v),3) if v else None} for k,v in buckets.items()}
def compose(indices,words):
 assert len(indices)==4096 and len(words)==16
 colors=[(*unword(words[x]),255) if x else (0,0,0,0) for x in indices]
 image=Image.new("RGBA",(64,64))
 image.putdata(colors)
 assert len(set(colors))<=16
 return image
def panel(canvas,im,x,y,dim=192):
 bg=Image.new("RGBA",(dim,dim),(239,243,247,255))
 view=im.resize((dim,dim),Image.Resampling.NEAREST)
 bg.alpha_composite(view)
 canvas.paste(bg.convert("RGB"),(x,y))
if sha(ARCHIVE)!=PINNED_ARCHIVE:raise RuntimeError("Pinned source RAR mismatch")
W=1150;ROW=246;H=126+6*ROW+28
sheet=Image.new("RGB",(W,H),"#f6f5f2")
draw=ImageDraw.Draw(sheet)
draw.text((18,17),"MERCURY DELTA FAMILY / DS64 EYE + WING READABILITY PASS",font=FONT,fill="#24313a")
draw.text((18,39),"Original 160px / previous individual palette 64px / subtle DS-only color-contrast refinement",font=FONT,fill="#4e5a66")
draw.text((18,61),"Same indexed pixels, alpha mask and silhouette. Unapproved; no ROM or sprite-library integration.",font=FONT,fill="#995148")
for xpos,label in [(20,"Orpheus source 160px"),(231,"Previous 64px (3x)"),(439,"Contrast-refined 64px (3x)"),(658,"Feature-edge checks")]:
 draw.text((xpos,98),label,font=FONT,fill="#2e4250")
records=[]
for si,(num,name,label) in enumerate(SPECIES):
 new_words=[0]+[word(readhex(h)) for h in PALETTES[name]]
 assert len(new_words)==16 and len(set(new_words[1:]))==15
 for vi,(role,suffix) in enumerate((("front","_1"),("back","b_1"))):
  prefix=f"{name}_{role}"
  source=SRC/f"{num}{suffix}.png"
  before_path=ROOT/f"{prefix}_delta_palette64.png"
  tiles_path=ROOT/f"{prefix}_4bpp_tiles.bin"
  palette_path=ROOT/f"{prefix}_bgr555_palette.bin"
  assert all(p.exists() for p in (source,before_path,tiles_path,palette_path))
  original=Image.open(source).convert("RGBA")
  before=Image.open(before_path).convert("RGBA")
  assert original.size==(160,160) and before.size==(64,64)
  tiles=tiles_path.read_bytes()
  idx=unpack_idx(tiles)
  old_words=list(struct.unpack("<16H",palette_path.read_bytes()))
  assert len(old_words)==16
  assert list(compose(idx,old_words).getdata())==list(before.getdata()),"Old binary not same as current preview"
  after=compose(idx,new_words)
  assert before.getchannel("A").tobytes()==after.getchannel("A").tobytes()
  assert before.getchannel("A").getbbox()==after.getchannel("A").getbbox()
  assert len(set(after.getdata()))<=16
  # No pixels/tiles changed; use exactly the same DS 4bpp bytes.
  new_tile_file=OUT/f"{prefix}_4bpp_tiles.bin"
  new_tile_file.write_bytes(tiles)
  new_palette_file=OUT/f"{prefix}_bgr555_palette.bin"
  new_palette_file.write_bytes(struct.pack("<16H",*new_words))
  out_path=OUT/f"{prefix}_contrast64.png"
  after.save(out_path,optimize=True)
  edges_before=edge_values(idx,old_words)
  edges_after=edge_values(idx,new_words)
  # Track change in mean luminance contrast without presuming it represents approval.
  changes={}
  for feature in edges_before:
   a=edges_before[feature]["meanLumaSeparation"]
   b=edges_after[feature]["meanLumaSeparation"]
   changes[feature]=round(b-a,3) if a is not None and b is not None else None
  used=len(set(idx)-{0})
  assert 0<used<=15
  n_changed=sum(a!=b for a,b in zip(before.getdata(),after.getdata()) if a[3])
  row={
    "name":name,"view":role,"paletteDirection":label,
    "sourceSHA256":sha(source),"sourceCanvas":[160,160],
    "beforeSHA256":sha(before_path),"afterSHA256":sha(out_path),
    "sourceBGR555PaletteWords":old_words,"refinedBGR555PaletteWords":new_words,
    "paletteEntryChanges":sum(a!=b for a,b in zip(old_words,new_words)),
    "pixelIndicesChanged":0,"opaquePixelCount":sum(bool(v) for v in idx),
    "opaquePixelsWithDifferentColor":n_changed,
    "paletteSlotsUsed":used,"paletteSlotsMax":15,
    "transparentMaskIdentical":True,"sourceGeometryIdentical":True,
    "tileBytes":len(tiles),"tileSHA256":sha(tiles_path),"verifiedOutputTileSHA256":sha(new_tile_file),
    "paletteBytes":new_palette_file.stat().st_size,
    "baselineEdges":edges_before,"refinedEdges":edges_after,"lumaSeparationDelta":changes,
    "approved":False,"ROMIntegrated":False
  }
  assert row["tileBytes"]==2048 and row["paletteBytes"]==32
  assert row["tileSHA256"]==row["verifiedOutputTileSHA256"]
  records.append(row)
  y=124+(si*2+vi)*ROW
  draw.rounded_rectangle((13,y-4,W-13,y+ROW-14),radius=12,fill="#ffffff",outline="#cfd7de")
  draw.text((20,y+3),f"{name.title()} / {role.upper()} -- {label}",font=FONT,fill="#203140")
  panel(sheet,original,20,y+29,160)
  panel(sheet,before,228,y+29)
  panel(sheet,after,436,y+29)
  for k,key in enumerate(("wing_body","wing_internal","accent_body","outline_body")):
   a=edges_before[key]["meanLumaSeparation"]
   b=edges_after[key]["meanLumaSeparation"]
   na=edges_before[key]["edgeCount"]
   l=f"{key}: {a if a is not None else 'n/a'} -> {b if b is not None else 'n/a'}  (n={na})"
   draw.text((658,y+34+k*23),l,font=FONT,fill="#455461")
  draw.text((658,y+132),f"Used: {used}/15 opaque + transparency",font=FONT,fill="#455461")
  draw.text((658,y+154),"Pixel indices unchanged / identical 4bpp tiles",font=FONT,fill="#455461")
  draw.text((658,y+176),"Eye accuracy not individually certified (edge proxy only)",font=FONT,fill="#8c4b43")
  draw.text((658,y+198),"UNAPPROVED / NOT INTEGRATED",font=FONT,fill="#8c4b43")
  print("READABILITY_RESULT",json.dumps(row,sort_keys=True))
sheetfile=OUT/"orpheus_ds64_eye_wing_contrast_before_after.png"
sheet.save(sheetfile,optimize=True)
assert len(records)==6
manifest={
 "schema":"mercury-orpheus-ds64-readability-color-only-v1",
 "shaOriginalArchive":PINNED_ARCHIVE,
 "sourceRecolorExperiment":"report/ds64_individual_recolors",
 "approvalsChanged":False,"originalSourceFilesModified":False,"ROMIntegrated":False,
 "method":"same 4bpp index bytes and same 64x64 alpha silhouettes; replace only stage-specific DS BGR555 palette entries for eye/accent/wing/body separation",
 "limitations":["Color contrast measures are luminance differences across material-boundary pixel pairs, not a subjective eye-detection score.","Pixel positions remain identical; details lost in first downscale have not been restored.","All six alternative palettes are proposals only, no KEEP vote.","No shiny, NCGR/NCLR/NARC integration, or emulator rendering.","Artist permission reported by user; precise redistribution terms to be recorded."],
 "records":records}
(OUT/"readability_metrics.json").write_text(json.dumps(manifest,indent=2)+"\n")
print("READABILITY_SUMMARY",json.dumps({"views":len(records),"native4bppExactTileReuse":len(records),"approved":False,"romIntegrated":False,"sheetSHA256":sha(sheetfile)}))
print("READABILITY_BASE64_START orpheus_ds64_eye_wing_contrast_before_after.png")
print(base64.b64encode(sheetfile.read_bytes()).decode("ascii"))
print("READABILITY_BASE64_END orpheus_ds64_eye_wing_contrast_before_after.png")
