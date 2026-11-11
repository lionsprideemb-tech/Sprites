#!/usr/bin/env python3
"""Orpheus Delta Bug/Ground native Platinum 80px SIX normal views preflight.

Preserves existing approved decisions and the already QA-verified Vibrava/Flygon
pixels and palettes. Trapinch alone is given the cohesive terracotta / sandstone
palette plus restrained body scutes; all source silhouettes are immutable.

Outputs (UNAPPROVED) indexed PNG 80px, DS OBJ tile bytes, normal palette,
two-frame 160x80 *static-placeholder source* for pret/pokeplatinum nitrogfx,
and visually tagged lossy 64px comparison-only preview. No ROM insertion.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import hashlib,json,struct,shutil
P=Path("review/candidates/orpheus-2026-11-09-UNAPPROVED")
TR=P/"platinum-native80-source-faithful"
POL=P/"desert-scarab-vein-scute-polish-native80"
O=Path("report/orpheus_delta_native80_preflight")
O.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
src=json.loads((TR/"native80_selected_half_qa.json").read_text())
pol=json.loads((POL/"veins_scutes_exact_QA.json").read_text())
assert src["nativePlatinumCanvas"]==[80,80] and src["allUnapproved"] and src["noROMIntegration"]
assert pol["canvas"]==[80,80] and pol["allUnapproved"] and pol["noPlatinumIntegration"]
S={r["view"]:r for r in src["views"]};R={r["view"]:r for r in pol["views"]}
assert len(S)==6 and len(R)==4
ORDER=("trapinch_front","trapinch_back","vibrava_front","vibrava_back","flygon_front","flygon_back")
TRAPINCH_SOURCE={
"trapinch_front":{"png":"293c14e11428b949821a4304d11d282ff9e0eb6c3c89dac24719f12f9a3d53e3","tiles":"d46323e8a179bf1082e7161fa0b88cb23d5679ae7ae21808220c78942dc8756b","palette":"4066361154f4ba02306e45213c7377ddfe59a3e208a44737e45a8bea7970bfd3"},
"trapinch_back":{"png":"b6912313a3359d25aa80700d83ce85dd3ec6a0fb9529695a087c6769d4d04de7","tiles":"042852dca4887e1e5a62b21655357f9d1f067b46b29a42b4e82d79bd23e2ca1c","palette":"4066361154f4ba02306e45213c7377ddfe59a3e208a44737e45a8bea7970bfd3"}
}
# New age-specific juvenile colorway. Unlike mature Flygon's cocoa shell and
# sage wings, this earthy grub has russet clay armor and pale ochre mandibles.
# Index 11 is one single source-pinned FRONT central eye pixel, now sage-green.
TRAPINCH_COLORS=[
"#000000","#241f1a","#4b3528","#79452d","#af6747","#d88d5b",
"#edbf81","#644632","#8b734b","#c0a16b","#ead0a1","#739257",
"#344b36","#749b53","#b6c87e","#f5e9d2"]
def to_word(hexcode):
 vals=[int(hexcode[i:i+2],16) for i in (1,3,5)]
 q=[round(v*31/255) for v in vals]
 return q[0]|(q[1]<<5)|(q[2]<<10)
def rgb(word):return tuple(round(((word>>(5*i))&31)*255/31) for i in range(3))
COLORS=[to_word(c) for c in TRAPINCH_COLORS]
assert len(COLORS)==16 and len(set(COLORS[1:]))==15
def unpack(t):
 assert len(t)==3200
 a=[0]*6400;i=0
 for by in range(0,80,8):
  for bx in range(0,80,8):
   for y in range(8):
    for x in range(0,8,2):
     b=t[i];i+=1
     a[(by+y)*80+bx+x]=b&15
     a[(by+y)*80+bx+x+1]=b>>4
 return a
def pack(a):
 assert len(a)==6400 and all(0<=k<16 for k in a)
 z=bytearray()
 for by in range(0,80,8):
  for bx in range(0,80,8):
   for y in range(8):
    for x in range(0,8,2):
     z.append(a[(by+y)*80+bx+x] | (a[(by+y)*80+bx+x+1]<<4))
 assert len(z)==3200
 return bytes(z)
def to_rgba(idx,words):
 im=Image.new("RGBA",(80,80))
 im.putdata([(*rgb(words[z]),255) if z else (0,0,0,0) for z in idx])
 return im
def trapinch_scutes(idx,role):
 # Single-pixel/3-pixel scutes on existing wholly opaque body interiors,
 # never on outline, pale horns, mandibles or eye.
 target=(23,31,40,46) if role=="front" else (24,44,51,68)
 x0,y0,x1,y1=target
 selected=[]
 for y in range(y0,y1,4):
  for x in range(x0+((y//4)%2)*3,x1,5):
   if any(abs(x-xx)<7 and abs(y-yy)<6 for xx,yy in selected):continue
   cells=[idx[(y+dy)*80+x+dx] for dy in (-1,0,1) for dx in (-1,0,1)]
   if not all(p in (3,4,5,6) for p in cells):continue
   selected.append((x,y))
   if len(selected)>= (3 if role=="front" else 5):break
  if len(selected)>= (3 if role=="front" else 5):break
 assert len(selected)>0,(role,"no safe body interior positions")
 changes=[]
 for x,y in selected:
  for xx,yy,dark in ((x,y,True),(x+1,y,True),(x,y+1,False)):
   k=yy*80+xx;old=idx[k]
   assert old in (3,4,5,6)
   new=max(3,old-1) if dark else min(6,old+1)
   if new!=old:
    idx[k]=new
    changes.append({"x":xx,"y":yy,"oldIndex":old,"newIndex":new,"feature":"interior_scute"})
 return selected,changes
def pal_png(idx,w,h,words):
 im=Image.new("P",(w,h))
 im.putdata(idx)
 colors=[v for word in words for v in rgb(word)]
 im.putpalette(colors+[0]*(768-len(colors)))
 im.info["transparency"]=0
 return im
def font(size,bold=False):
 files=("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf") if bold else ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",)
 for f in files:
  if Path(f).exists():return ImageFont.truetype(f,size)
 return ImageFont.load_default()
def paste_bg(canvas,im,x,y,scale):
 w,h=im.size
 layer=Image.new("RGBA",(w*scale,h*scale),"#EDF1F3")
 layer.alpha_composite(im.resize((w*scale,h*scale),Image.Resampling.NEAREST))
 canvas.paste(layer.convert("RGB"),(x,y))
records=[]
renders={}
for name in ORDER:
 stage,face=name.split("_")
 if stage=="trapinch":
  rec=S[name];pins=TRAPINCH_SOURCE[name]
  b=TR/rec["png"];t=TR/rec["tiles"];p=TR/rec["palette"]
  assert sha(b)==pins["png"] and sha(t)==pins["tiles"] and sha(p)==pins["palette"]
  assert rec["pngTilesRoundTrip"] and rec["approved"] is False
  orig=Image.open(b).convert("RGBA")
  baseline_idx=unpack(t.read_bytes())
  baseline_palette=p.read_bytes()
  assert to_rgba(baseline_idx,struct.unpack("<16H",baseline_palette)).tobytes()==orig.tobytes()
  idx=baseline_idx[:]
  anchors,edits=trapinch_scutes(idx,face)
  # Index 11 is exactly the central source pixel in FRONT's eye and absent
  # from the BACK; changing its palette is intentional, not a geometry edit.
  assert (baseline_idx.count(11)==1 if face=="front" else baseline_idx.count(11)==0)
  assert (baseline_idx[36*80+43]==11 if face=="front" else True)
  palette=struct.pack("<16H",*COLORS)
  image=to_rgba(idx,COLORS)
  assert orig.getchannel("A").tobytes()==image.getchannel("A").tobytes()
  assert unpack(pack(idx))==idx
  assert image.tobytes()==to_rgba(unpack(pack(idx)),COLORS).tobytes()
  assert set(idx[i] for i in range(6400) if not baseline_idx[i])=={0}
  provenance={"baseline":rec["png"],"originalPNGsha256":rec["pngSHA256"],
       "sourceOriginal160SHA256":rec["sourceSHA256"],
       "paletteRetone":"juvenile terracotta/copper/sandstone with single sage green eye",
       "scuteAnchors":anchors,"specificInteriorChanges":edits,
       "changedPixelIndices":sum(a!=b for a,b in zip(baseline_idx,idx))}
 else:
  rec=R[name];b=POL/rec["png"];t=POL/rec["tiles"];p=POL/rec["palette"]
  assert sha(b)==rec["pngSHA256"] and sha(t)==rec["tileSHA256"] and sha(p)==rec["paletteSHA256"]
  assert rec["decodeToPNGExact"] and rec["approved"] is False
  palette=p.read_bytes()
  idx=unpack(t.read_bytes())
  image=Image.open(b).convert("RGBA")
  assert image.tobytes()==to_rgba(idx,struct.unpack("<16H",palette)).tobytes()
  provenance={"baseline":rec["png"],"sourcePNGsha256":rec["sourceSHA256"],
        "pixelChangesFromVerifiedBaseline":0,"identicalPixelIndices":True,
        "paletteBytesUnmodified":True}
  orig=image
 words=struct.unpack("<16H",palette)
 assert len(palette)==32 and len(set(idx)-{0})<=15
 assert image.size==(80,80) and to_rgba(unpack(pack(idx)),words).tobytes()==image.tobytes()
 outroot=O/"family"/stage
 outroot.mkdir(parents=True,exist_ok=True)
 pngpath=outroot/(face+"_80.png")
 tilepath=outroot/(face+"_80_4bpp_tiles.bin")
 palpath=outroot/(face+"_80_bgr555.pal.bin")
 image.save(pngpath,optimize=True);tilepath.write_bytes(pack(idx));palpath.write_bytes(palette)
 # G4 battle engine 160x80 two-frame sheet. Static second frame deliberately
 # duplicates the already-approved-as-candidate first frame (NO invented art).
 rows=[]
 for y in range(80):
  row=idx[y*80:(y+1)*80]
  rows.extend(row+row)
 assert len(rows)==12800 and all(rows[y*160:y*160+80]==rows[y*160+80:y*160+160] for y in range(80))
 inp=pal_png(rows,160,80,words)
 strip=outroot/(face+"_twoframe_STATIC_160x80.png")
 inp.save(strip,optimize=True,bits=4)
 reopened=Image.open(strip)
 assert reopened.size==(160,80) and reopened.mode=="P" and list(reopened.getdata())==rows
 # Stage specific JASC palette consumed by pokeplatinum nitrogfx.
 jasc="JASC-PAL\n0100\n16\n"+"\n".join(" ".join(map(str,rgb(word))) for word in words)+"\n"
 jascpath=outroot/(face+"_normal.pal")
 jascpath.write_text(jasc)
 # Fixed research key for deterministic game-like encrypted NCGR probe.
 # No ID allocation / ROM binding accompanies this package.
 keyfile=outroot/(face+"_twoframe_STATIC_160x80.png.key")
 keyfile.write_bytes(struct.pack("<I",0x52A04286))
 # 64x64 preview only; conversion is destructive, not a game source.
 compare=image.resize((64,64),Image.Resampling.NEAREST)
 preview=outroot/(face+"_64_LOSSY_NOT_FOR_PLATINUM.png")
 compare.save(preview,optimize=True)
 # Crude subsample loss: no claim of recovered reversible original.
 if stage=="trapinch":
  assert orig.getchannel("A").tobytes()==image.getchannel("A").tobytes()
 recout={"view":name,"native":[80,80],"nativeImage":str(pngpath.relative_to(O)),
    "tiles":str(tilepath.relative_to(O)),"palette":str(palpath.relative_to(O)),
    "ntr160Source":str(strip.relative_to(O)),"ntrJASCpalette":str(jascpath.relative_to(O)),
    "ntrKey":str(keyfile.relative_to(O)),"lossy64Preview":str(preview.relative_to(O)),
    "imageSHA256":sha(pngpath),"tilesSHA256":sha(tilepath),"paletteSHA256":sha(palpath),
    "stripSHA256":sha(strip),"tileBytes":len(pack(idx)),"paletteBytes":len(palette),
    "ntrSourceCanvas":[160,80],"ntrDuplicateAnimationFrame":True,
    "sourceAlphaExact":True,"paletteIndexMax":max(idx),"4bppTileDecodeExact":True,
    "source":provenance,"approved":False,"romIntegrated":False}
 records.append(recout)
 renders[name]=(orig,image,compare)
 print("G4_SPRITE_PREFLIGHT",json.dumps({"view":name,"tile":len(pack(idx)),
     "twoFrame":[160,80],"alpha":True,"sha256":sha(pngpath)}))
# Six-view readable side-by-side with native 80px and 3x source locked zoom.
W=1150;H=1640
sheet=Image.new("RGB",(W,H),"#F7F8F9");d=ImageDraw.Draw(sheet)
d.text((20,14),"MERCURY REDUX  /  DESERT SCARAB FAMILY  /  NATIVE PLATINUM 80px",font=font(22,True),fill="#2A3844")
d.text((20,45),"Trapinch terracotta finished; Vibrava/Flygon exact existing art retained. UNAPPROVED / NOT IN ROM",font=font(14),fill="#AD4935")
for i,name in enumerate(ORDER):
 y=85+i*255
 d.rounded_rectangle((12,y,W-14,y+242),radius=12,fill="#FFFFFF",outline="#CBD4DC",width=2)
 orig,im,preview=renders[name]
 d.text((26,y+10),name.replace("_"," ").upper(),font=font(20,True),fill="#304454")
 d.text((26,y+44),"Before" if name.startswith("trapinch") else "Same locked colors",font=font(12),fill="#536675")
 d.text((376,y+44),"Finished 80px ×2",font=font(13),fill="#536675")
 d.text((733,y+44),"Actual 80px",font=font(13),fill="#536675")
 d.text((950,y+44),"64px (lossy only)",font=font(12),fill="#87463F")
 paste_bg(sheet,orig,25,y+61,2)
 paste_bg(sheet,im,390,y+61,2)
 paste_bg(sheet,im,760,y+89,1)
 paste_bg(sheet,preview,982,y+97,1)
 d.text((20,y+223),"Source silhouette exact  •  80px battle frame  •  4bpp  •  STATIC second-frame placeholder",font=font(12),fill="#647582")
out=O/"desert_scarab_six_normal_native80_mobile.png"
sheet.save(out,optimize=True)
manifest={"schema":"mercury-orpheus-sixview-pt-battle-source-preflight-v1",
  "sourceRepo":"lionsprideemb-tech/Sprites","sourceBranch":"mercury/orpheus-resource-audit-20261109",
  "upstreamReference":"pret/pokeplatinum/include/constants/graphics.h, res/pokemon/meson.build, tools/scripts/make_pl_pokegra.py",
  "nativeBattleFrame":[80,80],"expectedTwoFrames":[160,80],
  "normalViewCount":6,"stageCount":3,"targetMaxPaletteEntries":16,"transparentIndex":0,
  "originalFamilySourceUnmodified":True,"vibravaFlygonPixelsUnchanged":True,
  "trapinchShapeUnchanged":True,"allApproved":False,"historicalVotesUnmodified":True,
  "notROMIntegrated":True,"notEmulatorTested":True,"shinyViewsCertified":0,
  "gameIconsCertified":0,"twoFrameStripsAreStaticPlaceholders":True,
  "64pxFilesAreOnlyLossyPreviews":True,"nativeNitrogfxBinaryTestNotYetRun":True,
  "remainingGates":["Explicit user artwork approval", "Normal/shiny front/back coverage and visual approval",
                    "Original icons adapted and verified", "True NTR NCGR/NCLR encoding + decompression roundtrip",
                    "Correct archive/species/form assignment and collision-safe build",
                    "In-game animation/summary/party/battle tests"],
  "comparison":out.name,"comparisonSHA256":sha(out),"views":records}
(O/"preflight_qa.json").write_text(json.dumps(manifest,indent=2)+"\n")
(O/"README.md").write_text(
"# Delta Desert Scarab six-view production-format preflight (UNAPPROVED)\n\n"
"[Six normal FRONT/BACK sprites at original 80px and enlarged zoom](desert_scarab_six_normal_native80_mobile.png)\n\n"
"All three stages now have normal front/back 80x80 indexed palette and 4bpp tiles. "
"Trapinch receives source-geometry-locked terracotta/ochre palette and a few subtle interior scutes; "
"Vibrava/Flygon retain their existing published pixels exactly. "
"Each view has an optional **160x80 STATIC repeated-frame PNG** and JASC palette suitable for testing "
"the upstream Platinum nitrogfx input path; a repeated static frame is *not* a finished battle animation. "
"64x64 previews are deliberately destructive and are **not** Platinum input.\n\n"
"Missing custom shiny views, game icons, artist attribution terms, user artwork approval, "
"engine archive/integration/emulator testing. No votes, game files, IDs or source art modified. "
"[Machine QA](preflight_qa.json).\n")
print("DELTA_SIX_VIEW_PREFLIGHT_PASS",json.dumps({"views":len(records),"trapinchNormal":2,
 "vibravaFlygonUntouched":True,"alphaPreserved":True,"nativeFrame":[80,80],
 "twoFrameStrip":[160,80],"noApproval":True,"noROM":True}))
