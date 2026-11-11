#!/usr/bin/env python3
"""Orpheus Delta 32px party-icon technical candidates (NOT game-certified).

Source Orpheus icon128x64 = two 64x64 image frames. Analyze 2x block
reversibility, adapt both frames to 32x32 without silhouette invention,
map source hue groups to stage-specific *existing* 15-color BGR555 palettes,
encode two-frame DS 4bpp tiles, verify every indexed-pixel roundtrip.
No approval, IDs, ROM or original source modifications.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import hashlib,colorsys,json,struct
BASE=Path("review/candidates/orpheus-2026-11-09-UNAPPROVED")
SOURCE=BASE/"delta-shiny-icon-research/original-icon-source"
BATTLE=BASE/"desert-scarab-sixview-g4-preflight/family"
OUT=Path("report/orpheus_delta_icon32")
OUT.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rgb(word):return tuple(round(((word>>(5*j))&31)*255/31) for j in range(3))
def pack(a,w,h):
 assert w%8==h%8==0 and len(a)==w*h
 b=bytearray()
 for by in range(0,h,8):
  for bx in range(0,w,8):
   for y in range(8):
    for x in range(0,8,2):
     i=(by+y)*w+bx+x
     assert 0<=a[i]<=15 and 0<=a[i+1]<=15
     b.append(a[i]|(a[i+1]<<4))
 return bytes(b)
def unpack(data,w,h):
 assert len(data)==w*h//2
 a=[0]*(w*h);k=0
 for by in range(0,h,8):
  for bx in range(0,w,8):
   for y in range(8):
    for x in range(0,8,2):
     p=data[k];k+=1
     i=(by+y)*w+bx+x
     a[i]=p&15;a[i+1]=p>>4
 return a
def argb_to_palette(x,st):
 r,g,b,a=x
 if a==0:return 0
 val=max(r,g,b);lum=.2126*r+.7152*g+.0722*b
 h,s,v=colorsys.rgb_to_hsv(r/255,g/255,b/255)
 if lum<54:return 1
 if lum<88 and s<.20:return 2
 # Yellow and lime source areas: horn in Trapinch, wing membrane otherwise.
 yellow=0.08<=h<.21
 if st=="trapinch":
  if yellow:
   indices=[8,9,10,15];return indices[min(3,max(0,round((lum-70)/175*3)))]
  ramp=[2,3,4,5,6];return ramp[min(4,max(0,round((lum-46)/190*4)))]
 if yellow:
  ramp=[8,9,10,11,12];return ramp[min(4,max(0,round((lum-50)/175*4)))]
 # Greens of original source become warm armored body/abdomen.
 # Small very bright green glints may be highlighted without changing mask.
 if 0.2<=h<.47 and s>.35 and lum>190:return 14
 ramp=[2,3,4,5,6,7]
 return ramp[min(5,max(0,round((lum-45)/200*5)))]
def index_rgba(a,words,w=64,h=32):
 im=Image.new("RGBA",(w,h))
 im.putdata([(*rgb(words[z]),255) if z else (0,0,0,0) for z in a])
 return im
def font(n,b=False):
 for f in (["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"] if b else ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]):
  if Path(f).exists():return ImageFont.truetype(f,n)
 return ImageFont.load_default()
records=[]
for st in ("trapinch","vibrava","flygon"):
 src=SOURCE/st/"icon_original_128x64.png"
 pal=BATTLE/st/"front_80_bgr555.pal.bin"
 assert src.exists() and pal.exists(),(st,src,pal)
 w=struct.unpack("<16H",pal.read_bytes())
 assert len(w)==16 and w[0]==0
 im=Image.open(src).convert("RGBA")
 assert im.size==(128,64)
 down=Image.new("RGBA",(64,32))
 exactBlocks=0;exactAlphaBlocks=0
 for y in range(32):
  for x in range(64):
   vals=[im.getpixel((2*x+dx,2*y+dy)) for dy in range(2) for dx in range(2)]
   if all(p==vals[0] for p in vals):exactBlocks+=1
   if all(p[3]==vals[0][3] for p in vals):exactAlphaBlocks+=1
   down.putpixel((x,y),vals[0])
 idx=[argb_to_palette(p,st) for p in down.getdata()]
 png=index_rgba(idx,w)
 assert png.size==(64,32)
 # Alpha must match the chosen 2x nearest source pixels.
 assert png.getchannel("A").tobytes()==down.getchannel("A").tobytes()
 tiles=pack(idx,64,32)
 assert len(tiles)==1024 and unpack(tiles,64,32)==idx
 assert index_rgba(unpack(tiles,64,32),w).tobytes()==png.tobytes()
 assert len(set(idx)-{0})<=15
 out=OUT/st;out.mkdir(parents=True,exist_ok=True)
 origpath=out/"original_2xsample_64x32.png"
 outimg=out/"desert_scarab_ICON32x2_PROPOSAL.png"
 tilefile=out/"desert_scarab_ICON32x2_4bpp_tiles.bin"
 palfile=out/"desert_scarab_ICON32x2_palette.bin"
 down.save(origpath,optimize=True)
 png.save(outimg,optimize=True)
 tilefile.write_bytes(tiles);palfile.write_bytes(pal.read_bytes())
 # PNG game-input 64x32 two-frame 4bpp indexed palette no PNG alpha ambiguity.
 indexed=Image.new("P",(64,32))
 indexed.putdata(idx)
 table=[x for q in w for x in rgb(q)]+[0]*(768-48)
 indexed.putpalette(table)
 indexed.info["transparency"]=0
 nin=out/"desert_scarab_ICON32x2_indexed.png"
 indexed.save(nin,optimize=True,bits=4)
 assert list(Image.open(nin).getdata())==idx
 # Original pret/pokeplatinum icons are 32x64 indexed 4bpp: frame0 atop
 # frame1, NOT the horizontal 64x32 source layout used by Orpheus.
 vertical=[idx[y*64+x] for y in range(32) for x in range(32)]+[
     idx[y*64+32+x] for y in range(32) for x in range(32)]
 assert len(vertical)==2048 and len(pack(vertical,32,64))==1024
 assert unpack(pack(vertical,32,64),32,64)==vertical
 target=Image.new("P",(32,64))
 target.putdata(vertical)
 target.putpalette(table)
 target.info["transparency"]=0
 verticalPNG=out/"desert_scarab_ICON_STACKED_32x64_INDEXED4.png"
 target.save(verticalPNG,optimize=True,bits=4)
 assert Image.open(verticalPNG).size==(32,64)
 assert list(Image.open(verticalPNG).getdata())==vertical
 verticalTILES=out/"desert_scarab_ICON_STACKED_32x64_TILES4.bin"
 verticalTILES.write_bytes(pack(vertical,32,64))
 # These are *candidate* icons; restyling by pixels cannot be silently approved.
 info={"stage":st,"originalSource":str(src),"originalSHA256":sha(src),
    "sourceCanvas":[128,64],"assumedAnimationFrames":2,
    "sourceFrameEach":[64,64],"targetIconFrameEach":[32,32],
    "original2xExactBlockCount":exactBlocks,"original2xAlphaExactBlockCount":exactAlphaBlocks,
    "original2xBlockTotal":2048,"originalDownscaleIsLossless":exactBlocks==2048,
    "retone":"provisional stage-aware hue and shade remap",
    "sourcePaletteSHA256":sha(pal),"same16BGR555EntriesAsBattleFront":True,
    "indexedPixelRoundtrip":True,"alphaPreservedAfterNearestDownsample":True,
    "png":str(outimg.relative_to(OUT)),"indexedPNG":str(nin.relative_to(OUT)),
    "upstreamIconSourceCanvas":[32,64],"upstreamTwoFramesVertical":True,
    "upstreamIndexedPNG":str(verticalPNG.relative_to(OUT)),
    "upstreamIndexedPNGSHA256":sha(verticalPNG),
    "upstreamStackedTileBytes":verticalTILES.stat().st_size,
    "upstreamStackedTiles":str(verticalTILES.relative_to(OUT)),
    "upstreamStackedTilesRoundtrip":True,
    "sourceDownsample":str(origpath.relative_to(OUT)),
    "tiles":str(tilefile.relative_to(OUT)),"palette":str(palfile.relative_to(OUT)),
    "pngSHA256":sha(outimg),"tilesSHA256":sha(tilefile),
    "tileBytes":1024,"paletteBytes":32,"approved":False,"romIntegrated":False}
 records.append(info)
 print("DELTA_ICON32_CANDIDATE",json.dumps({"stage":st,"exact2x":exactBlocks,
       "alphaExact2x":exactAlphaBlocks,"tiles":1024,"gameCertified":False}))
# Three rows, original source sampled + new candidate, 4x and native.
sheet=Image.new("RGB",(900,730),"#F5F7F9")
d=ImageDraw.Draw(sheet)
d.text((20,10),"MERCURY REDUX — DESERT SCARAB DELTA ICON CONVERSION PROOFS",font=font(20,True),fill="#293B49")
d.text((20,40),"Original 2× sampled source → 32px indexed palette candidates (NOT approved)",font=font(14),fill="#A64C39")
for i,info in enumerate(records):
 y=75+205*i
 d.rounded_rectangle((10,y,890,y+194),radius=12,fill="white",outline="#CCD5DE")
 d.text((21,y+8),info["stage"].upper(),font=font(20,True),fill="#2D4557")
 d.text((30,y+42),"Original source 64×32",font=font(12),fill="#546777")
 d.text((360,y+42),"Desert Scarab candidate 64×32",font=font(12),fill="#546777")
 original=Image.open(OUT/info["sourceDownsample"]).convert("RGBA")
 candidate=Image.open(OUT/info["png"]).convert("RGBA")
 for pic,x in ((original,29),(candidate,357)):
  enlarged=pic.resize((256,128),Image.Resampling.NEAREST)
  back=Image.new("RGBA",enlarged.size,"#EDF1F4")
  back.alpha_composite(enlarged)
  sheet.paste(back.convert("RGB"),(x,y+62))
 d.text((666,y+70),"32px icon frames",font=font(13),fill="#516374")
 d.text((666,y+95),f"Exact 2× blocks: {info['original2xExactBlockCount']}/2048",font=font(12),fill="#516374")
 d.text((666,y+118),f"Alpha exact: {info['original2xAlphaExactBlockCount']}/2048",font=font(12),fill="#516374")
 d.text((666,y+147),"4bpp / not in game",font=font(12),fill="#9B483C")
preview=OUT/"all_three_icon32_technical_comparison.png"
sheet.save(preview,optimize=True)
qa={"schema":"mercury-orpheus-delta-source-icon32-technical-study-v1",
   "sourceArchive":"Original Orpheus regional icons, exact research branch source snapshots",
   "inputSheetsOriginal":[128,64],"derivedFrames":[32,32],"derivedSheet":[64,32],
   "notApproved":True,"noPlatinumChange":True,"notProductionIconArchive":True,
   "notGameAnimatedOrTested":True,"originalPixelsSourceLocked":True,
   "caveats":["2x nearest downsampling may be lossy when original 2x blocks differ; per-stage exact counts included.",
              "Recolor uses stage battle color palette, but is a visual draft not a selected icon.",
              "Icon animation sequence and actual upstream icon NARC processing unverified.",
              "Icons in Platinum use a shared 256-color JASC-PAL; these experimental individual stage palettes are not yet mapped to the real shared game icon palette."],
   "comparison":preview.name,"comparisonSHA256":sha(preview),"results":records}
(OUT/"icon32_qa.json").write_text(json.dumps(qa,indent=2)+"\n")
(OUT/"README.md").write_text(
 "# Delta family stage-matched 32px icon study (UNAPPROVED)\n\n"
 "[Original icon downsample vs stage-matched trial](all_three_icon32_technical_comparison.png) — "
 "two 32px frames for each three-stage custom Delta species, using the exact stage battle palette, "
 "with indexed graphics and raw tiled 4bpp exports. Original Orpheus source icon sheets are 128x64 "
 "and are sampled to 64x32 for this candidate; exact 2x reversibility is reported per stage. "
 "Upstream 32x64 vertical two-frame 4-bit indexed PNGs and matching tiled bytes are also prepared. "
 "The real Platinum menu uses a shared 256-color icon palette, so these individual stage palette trials "
 "are not yet game-palette compatible. **Not user-approved, not an implemented Platinum icon archive**, and no runtime animation tests. "
 "See [per-stage exact QA](icon32_qa.json).\n")
print("ORPHEUS_ICON32_TECHNICAL_QA",json.dumps({"stages":3,"frames":6,
  "allTileRoundTrip":True,"noNewArtApproved":True,"noROM":True}))
