#!/usr/bin/env python3
"""Isolated native Platinum icon palette-bank-3 technical experiment.

Models replacing ONLY the zero-filled fourth 16-color bank of the ORIGINAL
shared JASC-PAL (indices 48..63). Source palette and original three banks
are immutable. No proof that future species/form metadata can safely select
bank3 yet: run collision and runtime tests AFTER explicit visual approval.
Genuine upstream NitroGFX icon encoding/decoding and visual QA.
"""
from __future__ import annotations
import argparse, collections, hashlib, json, math, subprocess, struct
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
PA=argparse.ArgumentParser()
PA.add_argument("--upstream",required=True,type=Path)
PA.add_argument("--nitrogfx",required=True,type=Path)
A=PA.parse_args()
ROOT=Path("report/orpheus_delta_native80_preflight")
OUT=ROOT/"reserved-bank3-proposal"
OUT.mkdir(parents=True,exist_ok=True)
SOURCE=Path("review/candidates/orpheus-2026-11-09-UNAPPROVED/delta-icon32-candidates")
SHARED=A.upstream/"res/pokemon/.shared/pl_poke_icon.pal"
assert SHARED.is_file()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(*args):
 p=subprocess.run([str(x) for x in args],capture_output=True,text=True,timeout=80)
 if p.returncode:raise RuntimeError(f"Command {args} exit{p.returncode}\n{p.stdout[-800:]}\n{p.stderr[-1800:]}")
 return p
lines=SHARED.read_bytes().decode("ascii").splitlines()
assert lines[:3]==["JASC-PAL","0100","256"] and len(lines)==259
colors=[tuple(map(int,s.split())) for s in lines[3:]]
assert all(c==(0,0,0) for c in colors[48:])
assert any(c!=(0,0,0) for c in colors[:48])
def lab(c):
 def f(x):
  v=x/255
  return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
 r,g,b=map(f,c)
 x=(.4124564*r+.3575761*g+.1804375*b)/.95047
 y=.2126729*r+.7151522*g+.0721750*b
 z=(.0193339*r+.1191920*g+.9503041*b)/1.08883
 def g(t):return t**(1/3) if t>(6/29)**3 else t/(3*(6/29)**2)+4/29
 x,y,z=map(g,(x,y,z))
 return (116*y-16,500*(x-y),200*(y-z))
def d2(x,y):return sum((a-b)**2 for a,b in zip(x,y))
def norm(c):
 return tuple(round(round(v*31/255)*255/31) for v in c)
stages=("trapinch","vibrava","flygon")
data={}
weights=collections.defaultdict(float)
for st in stages:
 path=SOURCE/st/"desert_scarab_ICON_STACKED_32x64_INDEXED4.png"
 assert path.exists()
 im=Image.open(path)
 assert im.mode=="P" and im.size==(32,64)
 indexed=list(im.getdata())
 rgba=list(im.convert("RGBA").getdata())
 assert all((k==0)==(p[3]==0) for k,p in zip(indexed,rgba))
 observed=[norm(p[:3]) for p in rgba if p[3]]
 counts=collections.Counter(observed)
 total=len(observed)
 assert total>50
 # Equal total weight for all stages despite different pixel counts.
 for c,n in counts.items():weights[c]+=n/total
 data[st]={"indexed":indexed,"rgba":rgba,"trial":im.convert("RGBA"),"counts":counts}
# Include battle palettes as legal source-faithful candidate shades, even if a
# particular tiny icon currently omits them. Avoid inventing any new RGB color.
pool=set(weights)
for stage in stages:
 battle=Path("review/candidates/orpheus-2026-11-09-UNAPPROVED/desert-scarab-sixview-g4-preflight/family")/stage/"front_80_bgr555.pal.bin"
 words=struct.unpack("<16H",battle.read_bytes())
 for w in words[1:]:
  pool.add(tuple(round(((w>>(5*k))&31)*255/31) for k in range(3)))
keys=sorted(pool)
assert len(keys)>=15,len(keys)
labs={c:lab(c) for c in keys}
cost={(a,b):d2(labs[a],labs[b]) for a in keys for b in keys}
def obj(selected):
 return sum(w*min(cost[(p,c)] for c in selected) for p,w in weights.items())
# Deterministic weighted farthest-gain medoids, then 1-for-1 swap refinement.
first=min(keys,key=lambda c:(obj([c]),c))
selected=[first]
while len(selected)<15:
 next_c=min((k for k in keys if k not in selected),
   key=lambda c:(obj(selected+[c]),c))
 selected.append(next_c)
for iteration in range(3):
 updated=False
 for i,old in enumerate(list(selected)):
  best=selected[:];bestscore=obj(best)
  for c in keys:
   if c in selected:continue
   proposal=selected[:];proposal[i]=c
   score=obj(proposal)
   if score+1e-8<bestscore:
    bestscore=score;best=proposal
  if best!=selected:
   selected=best;updated=True
 if not updated:break
assert len(set(selected))==15
# Natural palette order: dark outlines to pale wing highlights.
selected.sort(key=lambda c:(.2126*c[0]+.7152*c[1]+.0722*c[2],c))
newbank=[(0,0,0)]+selected
assert len(newbank)==16
experiment=colors[:48]+newbank+colors[64:]
assert len(experiment)==256 and experiment[:48]==colors[:48] and experiment[64:]==colors[64:]
assert experiment[48]==colors[48]==(0,0,0)
assert all(experiment[i]!=colors[i] for i in range(49,64))
# **Never write back to the upstream shared palette file.**
pal=OUT/"PROPOSED_shared_icon_256color_palette_BANK3_ONLY.pal"
pal.write_bytes(("JASC-PAL\r\n0100\r\n256\r\n"+
 "\r\n".join(" ".join(str(v) for v in c) for c in experiment)+"\r\n").encode("ascii"))
assert sha(SHARED)!=sha(pal)
nclr=OUT/"PROPOSED_shared_icon_palette_BANK3_ONLY.NCLR"
run(A.nitrogfx,pal,nclr,"-bitdepth","4")
assert nclr.read_bytes().startswith(b"RLCN")
def pack(a):
 assert len(a)==2048
 out=bytearray()
 for by in range(0,64,8):
  for bx in range(0,32,8):
   for y in range(8):
    for x in range(0,8,2):
     i=(by+y)*32+bx+x
     assert 0<=a[i]<16 and 0<=a[i+1]<16
     out.append(a[i]|a[i+1]<<4)
 assert len(out)==1024
 return bytes(out)
def render(arr,palette16):
 o=Image.new("RGBA",(32,64))
 o.putdata([(0,0,0,0) if v==0 else (*palette16[v],255) for v in arr])
 return o
def font(n,bold=False):
 for f in (["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"] if bold else ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]):
  if Path(f).exists():return ImageFont.truetype(f,n)
 return ImageFont.load_default()
def display(sheet,im,x,y):
 for k in range(2):
  cut=im.crop((0,k*32,32,(k+1)*32)).resize((105,105),Image.Resampling.NEAREST)
  bg=Image.new("RGBA",cut.size,"#EDF1F4")
  bg.alpha_composite(cut.convert("RGBA"))
  sheet.paste(bg.convert("RGB"),(x+111*k,y))
base=json.loads((ROOT/"shared_icon_palette_qa.json").read_text())
assert base["nativeDecoderPixelDifferencesAll"]==0 and base["sharedPaletteSHA256"]==sha(SHARED)
results=[]
stageArt={}
for st in stages:
 source=data[st]
 sourceIdx=source["indexed"]
 srcColors=[norm(p[:3]) if p[3] else None for p in source["rgba"]]
 lut={c:min(range(1,16),key=lambda i:(cost[(c,selected[i-1])],i)) for c in set(srcColors) if c is not None}
 arr=[0 if p is None else lut[p] for p in srcColors]
 assert all((a==0)==(b==0) for a,b in zip(sourceIdx,arr))
 assert len(set(arr)-{0})<=15
 opaque=len([x for x in arr if x])
 sq=sum(cost[(c,selected[lut[c]-1])] for c in srcColors if c is not None)
 rms=math.sqrt(sq/opaque)
 prev=next(x for x in base["stageResults"] if x["stage"]==st)
 bestExisting=min(x["rmsLabDeltaE76"] for x in prev["candidateBankChoices"])
 stageDir=OUT/st
 stageDir.mkdir(exist_ok=True)
 image=Image.new("P",(32,64))
 image.putdata(arr)
 flat=[n for color in newbank for n in color]+[0]*720
 image.putpalette(flat)
 image.info["transparency"]=0
 png=stageDir/f"{st}_reservedbank3_indexed4_unapproved.png"
 image.save(png,bits=4,optimize=True)
 assert list(Image.open(png).getdata())==arr
 tile=stageDir/f"{st}_reservedbank3_raw4bpp.bin"
 tile.write_bytes(pack(arr))
 assert tile.stat().st_size==1024
 ncgr=stageDir/f"{st}_reservedbank3.NCGR"
 decode=stageDir/f"{st}_reservedbank3_decoded.png"
 run(A.nitrogfx,png,ncgr,"-clobbersize","-version101")
 assert ncgr.read_bytes().startswith(b"RGCN")
 run(A.nitrogfx,ncgr,decode,"-palette",nclr,"-palindex","4","-width","4","-object")
 decoded=Image.open(decode)
 assert decoded.size==(32,64) and decoded.mode=="P"
 diff=sum(a!=b for a,b in zip(decoded.getdata(),arr))
 assert diff==0,(st,diff)
 actual=render(arr,newbank)
 assert actual.getchannel("A").tobytes()==source["trial"].getchannel("A").tobytes()
 improvement=bestExisting-rms
 results.append({"stage":st,"source32pxTrialSHA256":prev["sourceIndexed32x64SHA256"],
    "sharedPaletteBank":3,"paletteAllocatedInGame":False,
    "sourceIconIndexTransparencyPreserved":True,
    "originalSharedPaletteBank0to2Exact":True,
    "originalReservedBanks4to15Exact":True,
    "existingGamePalettesUnmodified":True,
    "perStageBestExistingBank":prev["recommendedBank"],
    "existingBestRmsDeltaE76":bestExisting,
    "proposedBank3RmsDeltaE76":round(rms,4),
    "rmsDeltaE76Improvement":round(improvement,4),
    "raw4bppTileBytes":1024,"nativeNCGRBytes":ncgr.stat().st_size,
    "decodedPaletteIndicesDifferenceCount":diff,
    "PNG":str(png.relative_to(OUT)),
    "rawTiles":str(tile.relative_to(OUT)),
    "NCGR":str(ncgr.relative_to(OUT)),
    "NCGRsha256":sha(ncgr),
    "notApproved":True,"notIntegrated":True})
 stageArt[st]=actual
 print("ORPHEUS_RESERVED_BANK3_NITROGFX_PASS",st,"RMS",round(rms,3),
       "existingBest",bestExisting,"indexDiff",diff)
W,H=1070,850
sheet=Image.new("RGB",(W,H),"#F6F8FA")
d=ImageDraw.Draw(sheet)
d.text((18,12),"DESERT SCARAB / RESERVED SHARED-PALETTE BANK 3 EXPERIMENT",font=font(20,True),fill="#2F4352")
d.text((18,44),"Unapproved — original banks 0-2 remain byte-identical; bank 3 is NOT allocated in the game",font=font(13),fill="#A94B3E")
for i,st in enumerate(stages):
 y=80+i*250
 d.rounded_rectangle((11,y,W-11,y+239),radius=12,outline="#CDD6DD",fill="white")
 d.text((22,y+9),st.upper(),font=font(19,True),fill="#2B4051")
 d.text((25,y+40),"Desired stage-color trial",font=font(12),fill="#536A79")
 d.text((352,y+40),"Best existing bank",font=font(12),fill="#536A79")
 d.text((683,y+40),"New bank 3 experiment",font=font(12),fill="#536A79")
 display(sheet,data[st]["trial"],25,y+66)
 prev=next(x for x in base["stageResults"] if x["stage"]==st)
 existingSource=ROOT/"shared-icon-palette"/prev["paletteCompatibleSourcePNG"]
 existingImage=Image.open(existingSource).convert("RGBA")
 display(sheet,existingImage,350,y+66)
 display(sheet,stageArt[st],681,y+66)
 r=next(x for x in results if x["stage"]==st)
 d.text((350,y+190),f"Existing ΔE RMS {r['existingBestRmsDeltaE76']:.1f}",font=font(12),fill="#6C7987")
 d.text((681,y+190),f"New ΔE RMS {r['proposedBank3RmsDeltaE76']:.1f}",font=font(12,True),fill="#4C7755")
 d.text((681,y+213),"Source pixels and alpha unchanged",font=font(11),fill="#647687")
preview=OUT/"three_stage_existing_vs_bank3_visual_study.png"
sheet.save(preview,optimize=True)
manifest={"schema":"mercury-orpheus-experimental-reserved-icon-bank3-v1",
 "originalSharedPaletteSHA256":sha(SHARED),
 "originalSourcePaletteNeverModified":True,
 "existingPaletteBank0to2ByteIdentical":True,
 "reservedBanks4to15ByteIdentical":True,
 "onlyEditedSharedPaletteEntries":[i for i in range(256) if experiment[i]!=colors[i]],
 "editedEntryCount":sum(a!=b for a,b in zip(colors,experiment)),
 "candidate15Colors":selected,
 "paletteSlot3MustBeVerifiedUnusedBeforeAnyActualAllocation":True,
 "customPaletteIsNotInstalled":True,"approvalIsPending":True,
 "gameBuildNotChanged":True,"gameNARCNotModified":True,
 "engineIconIndex3RuntimeSupportNotTested":True,
 "original8x2SourcePixelsAndSilhouetteUntouched":True,
 "method":"15 stage-balanced source icon palette-color medoids, CIELAB weighted error, one reserved bank only",
 "nativeEncoder":"pret/pokeplatinum/tools/nitrogfx -clobbersize -version101",
 "realNCGRCount":3,"allDecodeIndexDifferences":0,
 "preview":str(preview.relative_to(ROOT)),
 "candidatePalette":str(pal.relative_to(ROOT)),
 "candidateNCLR":str(nclr.relative_to(ROOT)),
 "stageResults":results}
(ROOT/"reserved_icon_bank3_qa.json").write_text(json.dumps(manifest,indent=2)+"\n")
(OUT/"README.md").write_text(
 "# Reserved shared icon palette bank 3 — **UNAPPROVED experiment**\n\n"
 "[Visual compare: stage trial / best vanilla bank / custom reserved bank 3](three_stage_existing_vs_bank3_visual_study.png).\n\n"
 "Source artwork, original Platinum's shared palette and all existing palettes are untouched. "
 "This separate experimental palette file **copies the original 256 entries exactly except color entries "
 "49..63 in previously blank bank 3**; transparent entry 48 remains unchanged. "
 "A stage-balanced perceptual palette fit uses 15 source-faithful colors. "
 "Each icon was converted through genuine upstream NitroGFX (32x64, 4bpp, version101) "
 "and decoded with zero indexed differences. **Bank 3 has NOT been allocated or verified collision-free in "
 "the engine and NO ROM or NARC patch exists.** A visual choice, rights/credits check, form-ID "
 "registration proof and full palette collision audit are prerequisites to game integration. "
 "See [technical QA](../reserved_icon_bank3_qa.json).\n")
print("ORPHEUS_RESERVED_BANK3_EXPERIMENT_PASS",json.dumps({
  "stages":3,"paletteSourceUnmodified":True,"modifiedBanks":[3],
  "zeroIndexDifferences":True,"notApproved":True,"noROM":True}))
