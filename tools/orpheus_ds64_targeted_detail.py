#!/usr/bin/env python3
"""One hand-targeted, source-derived, isolated DS64 correction pass.

Input: checked-in verified stronger Orpheus normal-view tiles, palette and PNG.
Output: exactly two new candidate sprites, indexed DS 4bpp tiles, untouched
palette copies, traceable 64px preview and QA JSON. Never updates original
artist sprites, Keep/Cut votes, game data, or production ROM.
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import hashlib, struct, json, base64

SOURCE = Path("review/candidates/orpheus-2026-11-09-UNAPPROVED/deeper-real-pixels")
OUT = Path("report/targeted64")
OUT.mkdir(parents=True,exist_ok=True)
BASELINES = {
    "flygon_front": {
        "tile_sha256":"6b0b955d002f13d0ddaaca20c3c84ddeefd97a2ea7fe5ce1c77ad86e3c1639dc",
        "palette_sha256":"4a6eb782f3db86decea8d0892a3e342fa8451a2932744b89a5d328a838e0efaf",
        "roi":(16,8,49,39),
        "description":"Pupil / muzzle / forewing crossing",
    },
    "vibrava_back": {
        "tile_sha256":"0e7ed7ea6c96e6884a3195fe4fc0186f69b9e0546e7be0cb75c8e9f949c2c261",
        "palette_sha256":"02fa57e49ff490c8035368812c872b53b05c0bc1b439438bad307858369c83ce",
        "roi":(36,10,59,44),
        "description":"Antenna stalks / wing-root shading",
    },
}
# x, y, expected palette index, target palette index, intentional reason.
FIXES = {"vibrava_back":[[47,21,5,3,"left antenna stalk contrast"],[47,22,5,3,"left antenna stalk contrast"],[47,23,5,3,"left antenna stalk contrast"],[53,21,5,3,"right antenna stalk contrast"],[53,22,6,4,"right antenna stalk shading"],[43,39,5,3,"wing root shade continuity"],[43,40,5,3,"wing root shade continuity"],[44,40,5,3,"wing root shade continuity"]],"flygon_front":[[23,14,15,2,"eye pupil within existing light highlight"],[24,19,4,3,"muzzle/neck shadow separation"],[25,19,4,3,"muzzle/neck shadow separation"],[25,18,4,3,"muzzle/neck shadow continuity"],[35,27,10,8,"forewing/body edge contrast"],[36,27,10,8,"forewing/body edge contrast"],[36,28,10,8,"forewing/body edge contrast"],[37,28,10,8,"forewing/body edge contrast"]]}
def digest(data:bytes)->str:return hashlib.sha256(data).hexdigest()
def unpack(tile):
    assert len(tile)==2048
    idx=[0]*4096;n=0
    for ty in range(0,64,8):
        for tx in range(0,64,8):
            for yy in range(8):
                for xx in range(0,8,2):
                    v=tile[n];n+=1
                    idx[(ty+yy)*64+tx+xx]=v&15
                    idx[(ty+yy)*64+tx+xx+1]=v>>4
    assert n==2048
    return idx
def pack(idx):
    assert len(idx)==4096 and all(0<=x<=15 for x in idx)
    buf=bytearray()
    for ty in range(0,64,8):
        for tx in range(0,64,8):
            for yy in range(8):
                for xx in range(0,8,2):
                    a=idx[(ty+yy)*64+tx+xx]; b=idx[(ty+yy)*64+tx+xx+1]
                    buf.append(a|(b<<4))
    assert len(buf)==2048 and unpack(bytes(buf))==idx
    return bytes(buf)
def fromword(v):
    return tuple(round(((v>>(5*i))&31)*255/31) for i in range(3))
def decode(idx,pal):
    words=struct.unpack("<16H",pal)
    pixels=[(*fromword(words[i]),255) if i else (0,0,0,0) for i in idx]
    out=Image.new("RGBA",(64,64))
    out.putdata(pixels)
    return out
def onbg(im,px):
    big=im.resize((px,px),Image.Resampling.NEAREST)
    back=Image.new("RGBA",(px,px),(237,242,246,255));back.alpha_composite(big)
    return back.convert("RGB")
def crop_onbg(im,rect,height_max=238):
    x0,y0,x1,y1=rect;crop=im.crop(rect)
    scale=max(1,min(9,height_max//crop.height))
    big=crop.resize((crop.width*scale,crop.height*scale),Image.Resampling.NEAREST)
    back=Image.new("RGBA",big.size,(237,242,246,255));back.alpha_composite(big)
    return back.convert("RGB"),scale
font_path=next((s for s in [
  "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
  "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"
] if Path(s).exists()),None)
def font(size):return ImageFont.truetype(font_path,size) if font_path else ImageFont.load_default()
W=845;ROW=404;H=114+ROW*2+17
sheet=Image.new("RGB",(W,H),"#f3f5f6")
draw=ImageDraw.Draw(sheet)
draw.text((20,14),"MERCURY REDUX | FINAL LOCAL DS64 DETAIL STUDY",font=font(23),fill="#253440")
draw.text((20,48),"Actual verified Orpheus tiles • two views only • indexed-pixel edits",font=font(15),fill="#556474")
draw.text((20,72),"UNAPPROVED • source art / silhouettes / palettes / ROM unchanged",font=font(15),fill="#98514b")
records=[]
for n,name in enumerate(["flygon_front","vibrava_back"]):
    info=BASELINES[name]
    old_tiles=(SOURCE/f"{name}_stronger_4bpp_tiles.bin").read_bytes()
    pal=(SOURCE/f"{name}_stronger_bgr555_palette.bin").read_bytes()
    source_png=Image.open(SOURCE/f"{name}_stronger64.png").convert("RGBA")
    assert digest(old_tiles)==info["tile_sha256"],f"source tile hash changed: {name}"
    assert digest(pal)==info["palette_sha256"],f"source palette hash changed: {name}"
    assert len(old_tiles)==2048 and len(pal)==32 and source_png.size==(64,64)
    original=unpack(old_tiles)
    assert decode(original,pal).tobytes()==source_png.tobytes(),f"source mismatch {name}"
    revised=original[:]
    changes=[]
    for x,y,expected,replacement,reason in FIXES[name]:
        k=y*64+x
        assert info["roi"][0]<=x<info["roi"][2] and info["roi"][1]<=y<info["roi"][3]
        assert original[k]==expected,(name,x,y,original[k],expected)
        assert 1<expected<16 and 1<replacement<16 and expected!=replacement
        assert revised[k]==expected,(name,x,y,"repeated correction")
        revised[k]=replacement
        changes.append(dict(x=x,y=y,before=expected,after=replacement,reason=reason))
    assert len(changes)==8
    assert sum(a!=b for a,b in zip(original,revised))==len(changes)
    assert all((a==0)==(b==0) for a,b in zip(original,revised))
    assert all((a==1)==(b==1) for a,b in zip(original,revised))
    fresh=decode(revised,pal)
    assert fresh.getchannel("A").tobytes()==source_png.getchannel("A").tobytes()
    assert len(set(fresh.getdata()))<=16
    assert len({v for v in revised if v!=0})<=15
    new_tile=pack(revised)
    assert decode(unpack(new_tile),pal).tobytes()==fresh.tobytes()
    png=OUT/f"{name}_targeted64.png";fresh.save(png,optimize=True)
    tilefile=OUT/f"{name}_4bpp_tiles.bin";tilefile.write_bytes(new_tile)
    palettefile=OUT/f"{name}_bgr555_palette.bin";palettefile.write_bytes(pal)
    assert palettefile.read_bytes()==pal
    qa=dict(view=name,edits=changes,count=len(changes),sourceTileSHA256=digest(old_tiles),
      revisedTileSHA256=digest(new_tile),sourcePaletteSHA256=digest(pal),
      sourcePNGIdenticalToIndexedInput=True,sourceAlphaIdentical=True,outlineIndex1Identical=True,
      tileBytes=len(new_tile),paletteBytes=len(pal),uniqueRGBAColors=len(set(fresh.getdata())),
      opaquePaletteSlotsUsed=len({v for v in revised if v}),sourceImageChanged=False,
      artApproved=False,romIntegrated=False)
    records.append(qa)
    y=110+n*ROW
    draw.rounded_rectangle((12,y,833,y+ROW-9),radius=14,fill="white",outline="#ccd5dc",width=2)
    draw.text((22,y+11),name.replace("_"," ").upper()+" — "+info["description"],font=font(17),fill="#293947")
    draw.text((22,y+44),"Previous strong version",font=font(13),fill="#4e6070")
    draw.text((235,y+44),"New local correction",font=font(13),fill="#4e6070")
    draw.text((462,y+44),"New native-detail crop",font=font(13),fill="#4e6070")
    sheet.paste(onbg(source_png,199),(22,y+69))
    sheet.paste(onbg(fresh,199),(236,y+69))
    cropped,scale=crop_onbg(fresh,info["roi"],226)
    sheet.paste(cropped,(462,y+69))
    sheet.paste(onbg(fresh,64),(746,y+82))
    draw.text((740,y+153),"Native 1x",font=font(13),fill="#516477")
    draw.text((25,y+291),f"{len(changes)} internal pixel edits • exact DS4bpp round-trip PASS",font=font(15),fill="#315f4d")
    draw.text((25,y+318),"No pose, outlines, alpha or palette change. Four other views untouched.",font=font(13),fill="#536673")
    draw.text((25,y+342),"Candidate for visual review only — NO KEEP/CUT vote",font=font(13),fill="#9a4a45")
    print("TARGETED64_VIEW",json.dumps(qa,sort_keys=True))
sheetfile=OUT/"orpheus_final_targeted_before_after.png"
sheet.save(sheetfile,optimize=True)
manifest=dict(schema="mercury-orpheus-ds64-final-local-detail-v1",
  upstream="pinned stronger real Orpheus indexed tile buffers from isolated research branch",
  scope=["flygon_front","vibrava_back"],sourceArtModified=False,palettesModified=False,
  silhouettesModified=False,existingVotesModified=False,romIntegrated=False,approved=False,
  otherViewsUntouched=["trapinch_front","trapinch_back","vibrava_front","flygon_back"],
  notes=["These are true DS64 index-pixel edits rather than synthesized replacement art.",
    "Original art geometry and outlines remain unchanged.",
    "Visual effectiveness remains subject to user judgment; DS4bpp QA proves format not aesthetics."],
  views=records)
(OUT/"targeted64_qa.json").write_text(json.dumps(manifest,indent=2)+"\n")
print("TARGETED64_SUMMARY",json.dumps(dict(views=2,changes=16,allDSChecksPassed=True,
  sourceUnchanged=True,outlineUnchanged=True,approved=False,romIntegrated=False,
  imageSHA256=digest(sheetfile.read_bytes()))))
# Publish only generated candidate files and report. No approved sprite assets or game resources.
for fn in ["orpheus_final_targeted_before_after.png","targeted64_qa.json",
   "flygon_front_targeted64.png","flygon_front_4bpp_tiles.bin","flygon_front_bgr555_palette.bin",
   "vibrava_back_targeted64.png","vibrava_back_4bpp_tiles.bin","vibrava_back_bgr555_palette.bin"]:
    path=OUT/fn
    print("TARGETED64_FILE_START",fn)
    print(base64.b64encode(path.read_bytes()).decode("ascii"))
    print("TARGETED64_FILE_END",fn)
