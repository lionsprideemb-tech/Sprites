#!/usr/bin/env python3
"""Conservative native80 Desert Scarab wing-vein and scute visibility polish.

Only actual indexed 80x80 DS OBJ 4bpp tile indices are changed.
Reads pinned latest committed four-view baseline. Never edits historical
votes, original artwork, previous candidates, or Platinum.
"""
from collections import Counter
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import hashlib,json,struct

ROOT=Path("review/candidates/orpheus-2026-11-09-UNAPPROVED/desert-scarab-bug-ground-native80")
OUT=Path("report/desert_scarab_vein_scute_polish")
OUT.mkdir(parents=True,exist_ok=True)
QA=json.loads((ROOT/"desert_scarab_native80_qa.json").read_text())
assert QA["schema"]=="mercury-orpheus-bug-ground-desert-scarab-native80-v1"
assert QA["allUnapproved"] and QA["noPlatinumChanges"] and QA["noHistoricalVoteChanges"]
assert QA["noPreviousApprovedDesignChanges"] and QA["noSourcePNGChanges"]
RECORDS={r["view"]:r for r in QA["views"]}
ORDER=("vibrava_front","vibrava_back","flygon_front","flygon_back")
assert set(RECORDS)==set(ORDER)
# Each tuple: (x, y, PINNED original index, new index).
# Existing membrane #C is light sage; new #B is darker vein sage,
# with one #A stronger root pixel. All changes must be inside opaque wing.
WING={
    "vibrava_front":[
        (52,36,12,10),(53,35,12,11),(54,34,12,11),(55,33,12,11),
        (56,32,12,11),(57,31,12,11),(58,30,12,11)],
    "vibrava_back":[
        (44,64,12,10),(42,65,12,11),(40,66,12,11),(38,67,12,11),
        (36,68,12,11),(34,69,12,11),(32,70,12,11),(30,71,12,11),
        (28,72,12,11)],
    "flygon_front":[
        (55,34,12,10),(56,33,12,11),(57,32,12,11),(58,31,12,11),
        (59,30,12,11),(60,29,12,11),(61,28,12,11),(62,27,12,11),
        (63,26,12,11),
        (15,29,12,10),(14,28,12,11),(13,27,12,11),(12,26,12,11),
        (11,25,12,11)],
    "flygon_back":[
        (50,38,12,10),(51,37,12,11),(52,36,12,11),(53,35,12,11),
        (54,34,12,11),(55,33,12,11),(56,32,12,11),(57,31,12,11),
        (22,41,12,10),(21,40,12,11),(20,39,12,11),(19,38,12,11),
        (18,37,12,11),(17,36,12,11)]
}
# Two interior local plate/scute highlights per view, on pre-existing body
# surfaces, not wing geometry. All indices pinned to the committed sprites.
SCUTE={
    "vibrava_front":[(29,48,6,5),(34,48,3,4)],
    "vibrava_back":[(60,56,6,5),(51,60,4,5)],
    "flygon_front":[(21,43,5,4),(33,53,3,4)],
    "flygon_back":[(66,50,4,5),(54,60,4,3)]
}
def sha(obj):
    data=obj.read_bytes() if isinstance(obj,Path) else obj
    return hashlib.sha256(data).hexdigest()
def unpack(src):
    assert len(src)==3200
    idx=[0]*6400;off=0
    for by in range(0,80,8):
        for bx in range(0,80,8):
            for y in range(8):
                for x in range(0,8,2):
                    b=src[off];off+=1
                    idx[(by+y)*80+bx+x]=b&15
                    idx[(by+y)*80+bx+x+1]=b>>4
    assert off==3200
    return idx
def pack(idx):
    assert len(idx)==6400 and all(0<=v<=15 for v in idx)
    src=bytearray()
    for by in range(0,80,8):
        for bx in range(0,80,8):
            for y in range(8):
                for x in range(0,8,2):
                    a=idx[(by+y)*80+bx+x];b=idx[(by+y)*80+bx+x+1]
                    src.append(a|(b<<4))
    assert len(src)==3200
    return bytes(src)
def rgba(idx,palette):
    assert len(palette)==32
    words=struct.unpack("<16H",palette)
    rgb=lambda w:tuple(round(((w>>(5*i))&31)*255/31) for i in range(3))
    out=Image.new("RGBA",(80,80))
    out.putdata([(*rgb(words[k]),255) if k else (0,0,0,0) for k in idx])
    return out
def font(sz,bold=False):
    opts=(("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
           "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf") if bold else
          ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",))
    for p in opts:
        if Path(p).exists():return ImageFont.truetype(p,sz)
    return ImageFont.load_default()
def draw_sprite(sheet,im,x,y,scale,bg="#E9F0F2"):
    dim=im.width*scale
    box=Image.new("RGBA",(dim,dim),bg)
    box.alpha_composite(im.resize((dim,dim),Image.Resampling.NEAREST))
    sheet.paste(box.convert("RGB"),(x,y))
def label_text(d,x,y,text_,sz=15,color="#465a69",bold=False):
    d.text((x,y),text_,font=font(sz,bold),fill=color)

rows=[];images={}
for key in ORDER:
    r=RECORDS[key]
    base=ROOT/r["png"];tiles=ROOT/r["tiles"];palf=ROOT/r["palette"]
    assert sha(base)==r["pngSHA256"],("baseline png drift",key)
    assert sha(tiles)==r["tileSHA256"],("baseline tiles drift",key)
    assert sha(palf)==r["paletteSHA256"],("baseline palette drift",key)
    before=Image.open(base).convert("RGBA")
    assert before.size==(80,80)
    old_indices=unpack(tiles.read_bytes())
    palette=palf.read_bytes()
    assert rgba(old_indices,palette).tobytes()==before.tobytes()
    after_indices=old_indices[:]
    history=[]
    for category,group in (("wing-vein",WING[key]),("body-scute",SCUTE[key])):
        for x,y,expected,new in group:
            assert 0<=x<80 and 0<=y<80
            n=y*80+x
            assert old_indices[n]==expected,(key,category,x,y,old_indices[n],expected)
            assert expected>0 and new>0 and expected!=new
            assert after_indices[n]==expected,("duplicate edit coordinate",key,x,y)
            # Never overwrite outlines, claws, eye or transparent edge;
            # wing edits allowed only within soft pale membrane (index C).
            if category=="wing-vein":assert expected==12 and new in (10,11)
            else:assert expected in (3,4,5,6) and new in (3,4,5)
            after_indices[n]=new
            history.append(dict(kind=category,x=x,y=y,fromIndex=expected,toIndex=new))
    assert len(history)==len(WING[key])+len(SCUTE[key])
    modified=[(i%80,i//80) for i,(a,b) in enumerate(zip(old_indices,after_indices)) if a!=b]
    assert set(modified)==set((e["x"],e["y"]) for e in history)
    assert len(modified)==len(history)
    # Exact native DS 4bpp tiles and unchanged palette BGR555 bytes.
    newtiles=pack(after_indices)
    assert unpack(newtiles)==after_indices
    after=rgba(unpack(newtiles),palette)
    assert before.getchannel("A").tobytes()==after.getchannel("A").tobytes()
    assert len(set(after_indices)-{0})<=15
    assert after.size==before.size==(80,80)
    namestem=f"{key}_desert_scarab_vein_scale80"
    pngout=OUT/f"{namestem}.png"
    tileout=OUT/f"{namestem}_4bpp_tiles.bin"
    palout=OUT/f"{namestem}_palette.bin"
    after.save(pngout,optimize=True)
    tileout.write_bytes(newtiles)
    palout.write_bytes(palette)
    assert sha(palout)==sha(palf)
    assert rgba(unpack(tileout.read_bytes()),palout.read_bytes()).tobytes()==Image.open(pngout).convert("RGBA").tobytes()
    images[key]=(before,after)
    rows.append(dict(view=key,sourcePNG=r["png"],sourceSHA256=r["pngSHA256"],
         sourceTileSHA256=r["tileSHA256"],sourcePaletteSHA256=r["paletteSHA256"],
         normalFrontBackOnly=True,canvas=[80,80],paletteEntries=16,
         colorPaletteBytesIdentical=True,alphaMaskIdentical=True,
         sourceSilhouetteIdentical=True,transparentPixelsTouched=0,
         changedPixelCount=len(history),wingPixelEdits=len(WING[key]),
         scutePixelEdits=len(SCUTE[key]),edits=history,
         png=pngout.name,tiles=tileout.name,palette=palout.name,
         pngSHA256=sha(pngout),tileSHA256=sha(tileout),paletteSHA256=sha(palout),
         tileBytes=len(newtiles),paletteBytes=len(palette),
         decodeToPNGExact=True,approved=False,romIntegrated=False))
# Mobile-friendly vertical comparison, native pixels + high-resolution integer zoom.
W=900;H=1910
sheet=Image.new("RGB",(W,H),"#F6F8FA")
d=ImageDraw.Draw(sheet)
label_text(d,20,14,"MERCURY REDUX  /  DESERT SCARAB",25,"#273a49",True)
label_text(d,21,50,"Conservative vein + scute contrast, actual native80 index edits",14,"#566b7a")
label_text(d,21,74,"UNAPPROVED  •  NO PLATINUM CHANGES  •  SAME SILHOUETTES",13,"#A34B40")
for i,key in enumerate(ORDER):
    y=111+i*443
    d.rounded_rectangle((12,y,888,y+431),radius=12,fill="#FFFFFF",outline="#CFD8DD",width=2)
    label_text(d,25,y+10,key.replace("_"," ").upper(),20,"#273A48",True)
    label_text(d,36,y+44,"Before · 4×",15)
    label_text(d,381,y+44,"Refined · 4×",15)
    before,after=images[key]
    draw_sprite(sheet,before,30,y+75,4)
    draw_sprite(sheet,after,379,y+75,4)
    label_text(d,723,y+91,"Native",15)
    draw_sprite(sheet,746,y+130,1)
    label_text(d,717,y+225,f"{len(WING[key])} vein pixels",12)
    label_text(d,717,y+245,f"{len(SCUTE[key])} scute pixels",12)
    label_text(d,26,y+407,"Palette, alpha and sprite geometry unchanged  ·  Genuine 4bpp",13,"#566A78")
label_text(d,23,1893,"Verified Orpheus candidate; prior votes preserved. No assets approved.",12)
sheetpath=OUT/"desert_scarab_veins_scutes_before_after_mobile.png"
sheet.save(sheetpath,optimize=True)
report=dict(schema="mercury-orpheus-desert-scarab-wing-scale-final-polish-v1",
 baselineQAsha256=sha(ROOT/"desert_scarab_native80_qa.json"),
 baselineCommit="f62646d0c667269f9b110a83ee4996b257e24713",
 canvas=[80,80],output="unapproved experimental battle sprites",
 natureOfWork="explicit pinned nontransparent pixel-index edits to preserve anatomy",
 totalChangedPixels=sum(r["changedPixelCount"] for r in rows),
 totalWingPixels=sum(r["wingPixelEdits"] for r in rows),
 totalScutePixels=sum(r["scutePixelEdits"] for r in rows),
 allTransparentAndSilhouettesPreserved=True,stagePalettesUnchanged=True,
 noSourceChanges=True,noHistoricalVoteChanges=True,noProductionChanges=True,
 allUnapproved=True,noPlatinumIntegration=True,noROMBuildOrEmulatorTest=True,
 limitations=["Judgment of improved readability is subjective; review both native and enlarged sizes.",
              "No shinies, icons, or NARC/NCGR/NCLR ROM assets have been created or integrated."],
 mobileComparison=sheetpath.name,mobileComparisonSHA256=sha(sheetpath),
 views=rows)
(OUT/"veins_scutes_exact_QA.json").write_text(json.dumps(report,indent=2)+"\n")
(OUT/"README.md").write_text(
 "# Desert Scarab wing-vein and scale contrast (UNAPPROVED)\n\n"
 "[View 4-view phone-friendly before/after comparison](desert_scarab_veins_scutes_before_after_mobile.png)\n\n"
 "Four normal Orpheus Vibrava/Flygon 80×80 FRONT and BACK frames. "
 "Direct source-locked indexed DS 4bpp changes only; subtle sage-green wing-vein "
 "segments and two extra interior scute contrast pixels per view. "
 "No silhouette, palette, eye color, original archive, previous candidate, approval, "
 "historical vote, or Platinum change. No in-game validation or shiny/icon work.\n\n"
 "[Machine QA with exact original/new indices and SHA256 checks](veins_scutes_exact_QA.json).\n")
print("MERCURY_DESERT_SCARAB_QA",json.dumps({
 "frames":len(rows),"edits":report["totalChangedPixels"],
 "wing":report["totalWingPixels"],"scute":report["totalScutePixels"],
 "DS4bppDecodeExact":all(r["decodeToPNGExact"] for r in rows),
 "samePalette":True,"sameAlpha":True,"unapproved":True,"platinumUntouched":True
}))
