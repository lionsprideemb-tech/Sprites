#!/usr/bin/env python3
"""Verify and export a single stronger real DS64 microcleanup candidate for review.

Runs AFTER orpheus_ds64_deeper_readability_candidates.py. This creates review
assets from actual tile bytes; does not approve or write to the production ROM.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import base64,json,struct,hashlib
BASE=Path("review/candidates/orpheus-2026-11-09-UNAPPROVED/microfix-real-pixels")
OUT=Path("report/ds64_deeper_candidates")
assert OUT.exists()
EXPECTED={"vibrava_back":(24,"52b49dbd35a2cd9bcecc45dcd05cd48bdfb91225f11e439d46b986efd8748c19"),
          "flygon_front":(30,"a1b7f2113077496407f9009f3821c413a6c5a4b94edd8275b143671da96119fc")}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def unpack(raw):
 assert len(raw)==2048
 a=[0]*4096;off=0
 for ty in range(0,64,8):
  for tx in range(0,64,8):
   for y in range(8):
    for x in range(0,8,2):
     b=raw[off];off+=1
     a[(ty+y)*64+tx+x]=b&15
     a[(ty+y)*64+tx+x+1]=b>>4
 return a
def fromidx(a,pal):
 words=struct.unpack("<16H",pal)
 colors=[(*[round(255*((words[k]>>(5*j))&31)/31) for j in range(3)],255) if k else (0,0,0,0) for k in a]
 im=Image.new("RGBA",(64,64));im.putdata(colors);return im
def paste(bg,img,x,y,scale):
 scaled=img.resize((64*scale,64*scale),Image.Resampling.NEAREST)
 back=Image.new("RGBA",scaled.size,(238,243,247,255));back.alpha_composite(scaled)
 bg.paste(back.convert("RGB"),(x,y))
def crop(img,roi,scale):
 source=img.crop(roi)
 s=source.resize((source.width*scale,source.height*scale),Image.Resampling.NEAREST)
 b=Image.new("RGBA",s.size,(238,243,247,255));b.alpha_composite(s)
 return b.convert("RGB")
records=json.loads((OUT/"candidates_metrics.json").read_text())["views"]
assert len(records)==4
W=1060;ROW=440;H=120+ROW*2
sheet=Image.new("RGB",(W,H),"#f6f8fa")
d=ImageDraw.Draw(sheet)
font=ImageFont.load_default()
d.text((18,14),"MERCURY REDUX / REAL 64px DETAIL CLEANUP — BEFORE & STRONGER CANDIDATE",fill="#263543",font=font)
d.text((18,36),"Only Vibrava BACK and Flygon FRONT; real indexed DS 4bpp tile edits, not generated artwork",fill="#506273",font=font)
d.text((18,57),"Source, silhouette, palette, previous decisions and ROM untouched. UNAPPROVED.",fill="#9a504a",font=font)
outrows=[]
for i,name in enumerate(("vibrava_back","flygon_front")):
 old=BASE/f"{name}_4bpp_tiles.bin";palette=BASE/f"{name}_bgr555_palette.bin"
 candidate=OUT/f"{name}_stronger_4bpp_tiles.bin";palnew=OUT/f"{name}_stronger_bgr555_palette.bin"
 orig=Image.open(BASE/f"{name}_manual_microfix64.png").convert("RGBA")
 new=Image.open(OUT/f"{name}_stronger64.png").convert("RGBA")
 assert orig.size==new.size==(64,64)
 oldidx=unpack(old.read_bytes());newidx=unpack(candidate.read_bytes())
 assert sha(old)==EXPECTED[name][1]
 assert palette.read_bytes()==palnew.read_bytes()
 assert fromidx(oldidx,palette.read_bytes()).tobytes()==orig.tobytes()
 assert fromidx(newidx,palnew.read_bytes()).tobytes()==new.tobytes()
 assert orig.getchannel("A").tobytes()==new.getchannel("A").tobytes()
 assert all((a==1)==(b==1) for a,b in zip(oldidx,newidx))
 edits=[(k%64,k//64,a,b) for k,(a,b) in enumerate(zip(oldidx,newidx)) if a!=b]
 assert len(edits)==EXPECTED[name][0]
 assert all(a not in (0,1) and b not in (0,1) for x,y,a,b in edits)
 assert len(set(new.getdata()))<=16
 roi=(36,5,61,41) if name=="vibrava_back" else (16,8,49,39)
 y=94+i*ROW
 d.rounded_rectangle((8,y,1052,y+ROW-10),radius=12,fill="white",outline="#ccd8df",width=2)
 d.text((20,y+13),name.replace("_"," ").upper()+f" | {len(edits)} exact indexed pixel changes",fill="#253441",font=font)
 d.text((22,y+38),"Current 64px x4",fill="#465768",font=font)
 d.text((295,y+38),"Stronger 64px x4",fill="#465768",font=font)
 d.text((590,y+38),f"Native detail zoom: {roi[0]}..{roi[2]-1} x {roi[1]}..{roi[3]-1}",fill="#465768",font=font)
 paste(sheet,orig,20,y+58,4)
 paste(sheet,new,295,y+58,4)
 detail=crop(new,roi,7)
 sheet.paste(detail,(590,y+58))
 d.text((24,y+338),"Before (native 64px):",fill="#465768",font=font)
 paste(sheet,orig,165,y+335,1)
 d.text((296,y+338),"After (native 64px):",fill="#465768",font=font)
 paste(sheet,new,425,y+335,1)
 d.text((590,y+355),"Eye/antenna/wing interior color clarity improved; original outline locked",fill="#516273",font=font)
 d.text((20,y+405),"No anatomy redraw • no new palette colors • no approvals • no ROM integration",fill="#965047",font=font)
 outrows.append({"view":name,"changedPixels":len(edits),"coords":[{"x":x,"y":y,"before":a,"after":b} for x,y,a,b in edits],
  "originalTileSHA256":sha(old),"candidateTileSHA256":sha(candidate),"paletteSHA256":sha(palette),
  "alphaIdentical":True,"outlineIndex1Identical":True,"tileBytes":2048,"paletteBytes":32,
  "approved":False,"romIntegrated":False})
preview=OUT/"ds64_stronger_two_view_mobile_review.png"
sheet.save(preview,optimize=True)
metadata={"schema":"mercury-orpheus-real-ds64-stronger-review-v1",
 "baseline":"previous verified microfix tiles committed on isolated branch",
 "candidateType":"stronger experimental palette-index detail cleanup",
 "noSourceEdits":True,"noHistoricalVoteChanges":True,"noProductionIntegration":True,
 "otherFourViewsUntouched":True,"allUnapproved":True,"records":outrows}
(OUT/"ds64_stronger_two_view_qa.json").write_text(json.dumps(metadata,indent=2)+"\n")
print("STRONGER64_SUMMARY",json.dumps({"views":2,"changes":[r["changedPixels"] for r in outrows],"alphaUnchanged":True,"paletteUnchanged":True,"sourceUnchanged":True,"romIntegrated":False,"approved":False,"previewSha":sha(preview)}))
for name in ["ds64_stronger_two_view_mobile_review.png","ds64_stronger_two_view_qa.json",
 "vibrava_back_stronger64.png","vibrava_back_stronger_4bpp_tiles.bin","vibrava_back_stronger_bgr555_palette.bin",
 "flygon_front_stronger64.png","flygon_front_stronger_4bpp_tiles.bin","flygon_front_stronger_bgr555_palette.bin"]:
 path=OUT/name
 assert path.exists() and path.stat().st_size>0
 print("STRONGER64_FILE_START",name)
 print(base64.b64encode(path.read_bytes()).decode("ascii"))
 print("STRONGER64_FILE_END",name)
