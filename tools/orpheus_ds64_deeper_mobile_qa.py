#!/usr/bin/env python3
"""Publishable final review candidate from real source 64px tiles; NO approvals.

Consumes and verifies the two already-created stronger DS64 trial assets.
Exports only unapproved candidate PNGs, tiled 4bpp and BGR555 palettes to
GitHub Actions for quarantined branch publishing. No ROM or source mutations.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import hashlib,struct,json,base64
OLD=Path("report/ds64_manual_microfix")
PROPOSAL=Path("report/ds64_deeper_candidates")
OUT=Path("report/ds64_deeper_mobile")
OUT.mkdir(parents=True,exist_ok=True)
STAGES=[
 ("vibrava_back","VIBRAVA","BACK • sage & turquoise",24,(39,10,61,43)),
 ("flygon_front","FLYGON","FRONT • umber, bronze & teal",30,(15,8,42,38))]
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
F20=ImageFont.truetype(FONT,20)
F15=ImageFont.truetype(FONT,15)
F12=ImageFont.truetype(FONT,12)
def sh(path):
 h=hashlib.sha256()
 with open(path,"rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def unpack(tiles):
 assert len(tiles)==2048
 a=[0]*4096;p=0
 for ty in range(0,64,8):
  for tx in range(0,64,8):
   for dy in range(8):
    for dx in range(0,8,2):
     v=tiles[p];p+=1
     a[(ty+dy)*64+tx+dx]=v&15
     a[(ty+dy)*64+tx+dx+1]=v>>4
 return a
def decode(idx,pal):
 words=struct.unpack("<16H",pal)
 assert words[0]==0
 im=Image.new("RGBA",(64,64),(0,0,0,0))
 im.putdata([tuple(round(255*((words[v]>>(5*k))&31)/31) for k in range(3))+(255,) if v else (0,0,0,0) for v in idx])
 return im
def display(img,d):
 bg=Image.new("RGBA",(d,d),(238,242,246,255))
 bg.alpha_composite(img.resize((d,d),Image.Resampling.NEAREST))
 return bg.convert("RGB")
W=790;ROW=472;H=120+2*ROW+25
sheet=Image.new("RGB",(W,H),"#f5f7fa")
d=ImageDraw.Draw(sheet)
d.text((22,13),"MERCURY REDUX • REAL PIXEL-ART CLEANUP",fill="#23313b",font=F20)
d.text((22,45),"Vibrava back + Flygon front • exact DS64 source files",fill="#536879",font=F15)
d.text((22,68),"STRONGER WORKING CANDIDATES • NOT APPROVED • NOT IN ROM",fill="#9a4a3d",font=F12)
records=[]
for i,(base,title,subtitle,nexpected,rect) in enumerate(STAGES):
 old_image=Image.open(OLD/f"{base}_manual_microfix64.png").convert("RGBA")
 new_file=PROPOSAL/f"{base}_stronger64.png"
 new_image=Image.open(new_file).convert("RGBA")
 old_tiles=(OLD/f"{base}_4bpp_tiles.bin").read_bytes()
 new_tiles=(PROPOSAL/f"{base}_stronger_4bpp_tiles.bin").read_bytes()
 old_pal=(OLD/f"{base}_bgr555_palette.bin").read_bytes()
 new_pal=(PROPOSAL/f"{base}_stronger_bgr555_palette.bin").read_bytes()
 assert old_image.size==new_image.size==(64,64)
 assert len(old_tiles)==len(new_tiles)==2048
 assert len(old_pal)==len(new_pal)==32 and old_pal==new_pal
 prior=unpack(old_tiles);post=unpack(new_tiles)
 assert decode(prior,old_pal).tobytes()==old_image.tobytes()
 assert decode(post,new_pal).tobytes()==new_image.tobytes()
 assert all((a==0)==(b==0) for a,b in zip(prior,post))
 assert all((b==a) for a,b in zip(prior,post) if a==1)
 edits=[dict(x=p%64,y=p//64,before=a,after=b) for p,(a,b) in enumerate(zip(prior,post)) if a!=b]
 assert len(edits)==nexpected,f"Expected {nexpected} controlled edits, got {len(edits)}"
 assert len(set(post)-{0})<=15
 out_png=OUT/f"{base}_refined64.png"
 out_bin=OUT/f"{base}_4bpp_tiles.bin"
 out_pal=OUT/f"{base}_bgr555_palette.bin"
 new_image.save(out_png,optimize=True)
 out_bin.write_bytes(new_tiles);out_pal.write_bytes(new_pal)
 row={"id":base,"originalSourceSize":"160x160",
  "revisedCanvas":[64,64],"changedPixelsVsPrior":len(edits),
  "alphaMaskIdentical":old_image.getchannel("A").tobytes()==new_image.getchannel("A").tobytes(),
  "outlinePixelsUnchanged":True,
  "paletteIdentical":sh(out_pal)==sh(OLD/f"{base}_bgr555_palette.bin"),
  "DS4bppPixelsBytes":out_bin.stat().st_size,"BGR555PaletteBytes":out_pal.stat().st_size,
  "priorPNGSHA256":sh(OLD/f"{base}_manual_microfix64.png"),
  "refinedPNGSHA256":sh(out_png),
  "priorTileSHA256":sh(OLD/f"{base}_4bpp_tiles.bin"),
  "refinedTileSHA256":sh(out_bin),
  "pixelChanges":edits,
  "sourceArtUnmodified":True,"historicalVotesUnmodified":True,
  "approved":False,"ROMIntegrated":False
 }
 records.append(row)
 y=110+i*ROW
 d.rounded_rectangle((10,y,W-10,y+ROW-18),radius=12,outline="#c9d5df",fill="#ffffff",width=2)
 d.text((22,y+12),f"{title} {subtitle}",fill="#213441",font=F20)
 d.text((22,y+42),"PREVIOUS • 64×64 (4×)",fill="#4a5c68",font=F12)
 d.text((295,y+42),"REFINED • 64×64 (4×)",fill="#4a5c68",font=F12)
 d.text((573,y+42),"DETAIL • native 1×",fill="#4a5c68",font=F12)
 sheet.paste(display(old_image,242),(22,y+61))
 sheet.paste(display(new_image,242),(295,y+61))
 sheet.paste(display(new_image,64),(602,y+71))
 x0,y0,x1,y1=rect
 crop=new_image.crop(rect)
 # 6x enlarged pixels, no smoothing, intended close-up of eye/antenna/wing join
 cw=(x1-x0)*5;ch=(y1-y0)*5
 detailed=Image.new("RGBA",(cw,ch),(238,242,246,255))
 detailed.alpha_composite(crop.resize((cw,ch),Image.Resampling.NEAREST))
 sheet.paste(detailed.convert("RGB"),(571,y+149))
 d.text((573,y+335),f"{len(edits)} actual sprite-pixel changes",fill="#934b3f",font=F12)
 d.text((573,y+356),f"Palette {len(set(post)-{0})}/15 opaque colors",fill="#51616c",font=F12)
 d.text((22,y+394),"Original anatomy, outline and transparency preserved • binary DS tile roundtrip PASS",fill="#536775",font=F12)
 d.text((22,y+416),"USER REVIEW STILL REQUIRED • no production sprite changes",fill="#974b3f",font=F12)
 print("MOBILE_CANDIDATE",json.dumps({k:v for k,v in row.items() if k!="pixelChanges"},sort_keys=True))
sheet_name="orpheus_two_sprite_deeper_mobile_review.png"
sheetfile=OUT/sheet_name
sheet.save(sheetfile,optimize=True)
manifest={"schema":"mercury-orpheus-ds64-stronger-working-candidates-v1",
 "stage":"isolated-design-QA-only",
 "sourceArchive":"Orpheus_Resources.rar pinned upstream by SHA256",
 "changesOnly":["vibrava_back","flygon_front"],"totalChangedPixels":sum(q["changedPixelsVsPrior"] for q in records),
 "untouchedViews":["trapinch_front","trapinch_back","vibrava_front","flygon_back"],
 "historicApprovalsUntouched":True,"sourceArtworkUntouched":True,
 "sourceArtistPermissionReportedByUser":True,
 "artistLicenseTermsIndependentlyVerified":False,
 "approved":False,"gameIntegration":False,
 "notes":["Pixel-aligned actual 64×64 source-anchored PNG and DS OBJ 4bpp tiles, not AI-generated illustration.","Edits remain color-index-only and preserve outer geometry; detailed readability still needs human review.","Original source Flygon Bug/Dragon, intended Delta Flygon in Mercury Bug/Ground not registered."],
 "results":records}
(OUT/"readability_qa_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
print("MOBILE_QA_SUMMARY",json.dumps(dict(views=len(records),edits=manifest["totalChangedPixels"],tileRoundTrip=True,paletteIdentical=True,approved=False,romIntegrated=False)))
for file in [sheet_name,"vibrava_back_refined64.png","vibrava_back_4bpp_tiles.bin","vibrava_back_bgr555_palette.bin",
"flygon_front_refined64.png","flygon_front_4bpp_tiles.bin","flygon_front_bgr555_palette.bin","readability_qa_manifest.json"]:
 p=OUT/file
 print("MOBILE_EXPORT_START "+file)
 print(base64.b64encode(p.read_bytes()).decode("ascii"))
 print("MOBILE_EXPORT_END "+file)
