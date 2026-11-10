#!/usr/bin/env python3
"""Visual-only, reproducible mobile review of four already committed unapproved DS80 sprites.

No artwork edits; checks the exact committed PNG, indexed OBJ tiles, and BGR555 palettes.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import hashlib, json, struct

ROOT=Path("review/candidates/orpheus-2026-11-09-UNAPPROVED/desert-scarab-bug-ground-native80")
OUT=Path("report/desert_scarab_visual_review")
OUT.mkdir(parents=True,exist_ok=True)
QA=json.loads((ROOT/"desert_scarab_native80_qa.json").read_text())
assert QA["schema"]=="mercury-orpheus-bug-ground-desert-scarab-native80-v1"
assert QA["allUnapproved"] and QA["noPlatinumChanges"] and QA["noHistoricalVoteChanges"]
ORDER=("vibrava_front","vibrava_back","flygon_front","flygon_back")
RECORDS={r["view"]:r for r in QA["views"]}
assert set(ORDER)==set(RECORDS)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def decode(tile):
    assert len(tile)==3200
    a=[0]*6400;i=0
    for by in range(0,80,8):
        for bx in range(0,80,8):
            for y in range(8):
                for x in range(0,8,2):
                    q=tile[i];i+=1
                    a[(by+y)*80+bx+x]=q&15
                    a[(by+y)*80+bx+x+1]=q>>4
    return a
def rgba_from_index(idx,pal):
    words=struct.unpack("<16H",pal)
    def color(w):
        return tuple(round(((w>>(5*i))&31)*255/31) for i in range(3))
    im=Image.new("RGBA",(80,80))
    im.putdata([(*color(words[k]),255) if k else (0,0,0,0) for k in idx])
    return im
def font(sz,bold=False):
    paths=("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
           "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    for p in (paths if bold else paths[::-1]):
        if Path(p).exists():return ImageFont.truetype(p,sz)
    return ImageFont.load_default()
W=740;H=1740
sheet=Image.new("RGB",(W,H),"#f5f7f9")
d=ImageDraw.Draw(sheet)
d.text((22,17),"Mercury Redux / Desert Scarab",font=font(24,True),fill="#253746")
d.text((23,52),"Actual committed 80 px sprites + 4x nearest-neighbor views",font=font(14),fill="#526678")
d.text((23,73),"UNAPPROVED   ·   Four views   ·   No Platinum integration",font=font(13),fill="#9c4938")
summary=[]
for i,name in enumerate(ORDER):
    r=RECORDS[name]
    p=ROOT/r["png"];t=ROOT/r["tiles"];pal=ROOT/r["palette"]
    assert all(q.exists() for q in (p,t,pal)),name
    assert sha(p)==r["pngSHA256"] and sha(t)==r["tileSHA256"] and sha(pal)==r["paletteSHA256"]
    im=Image.open(p).convert("RGBA")
    assert im.size==(80,80)
    unpack=rgba_from_index(decode(t.read_bytes()),pal.read_bytes())
    assert unpack.tobytes()==im.tobytes()
    assert len(set(decode(t.read_bytes()))-{0})<=15
    assert len(pal.read_bytes())==32
    y=111+i*398
    d.rounded_rectangle((12,y,728,y+385),radius=12,fill="white",outline="#cad4dc",width=2)
    d.text((25,y+12),name.replace("_"," ").title(),font=font(21,True),fill="#263b46")
    d.text((27,y+47),"Native 80×80",font=font(16),fill="#526678")
    d.text((313,y+47),"4× zoom · unchanged pixels",font=font(16),fill="#526678")
    # Native image is rendered physically at 80px; enlarged is nearest-neighbor x4.
    d.rounded_rectangle((28,y+82,236,y+340),radius=9,fill="#eaf0f2")
    sheet.paste(im,(93,y+163),im)
    d.rounded_rectangle((313,y+82,690,y+351),radius=9,fill="#eaf0f2")
    scaled=im.resize((320,320),Image.Resampling.NEAREST)
    # preserve alpha on composite
    # position allowed within the 320px pane: enlarged panel needs 320px height.
    # panel is expanded to be 330 tall before compositing.
    d.rounded_rectangle((313,y+70,690,y+361),radius=9,fill="#eaf0f2")
    bg=Image.new("RGBA",(320,320),"#eaf0f2")
    bg.alpha_composite(scaled)
    sheet.paste(bg.convert("RGB"),(342,y+58))
    d.text((28,y+355),"DS OBJ 4bpp  ·  15 colors + transparency",font=font(13),fill="#576a76")
    summary.append({"view":name,"sha256":r["pngSHA256"],"native":[80,80],
                    "zoomFactor":4,"tileRoundtrip":True,"sourceGeometryPreserved":r["artworkSilhouettePreserved"]})
d.text((22,1717),"Source: Sprites / Orpheus isolated branch  ·  Pixels & previous approvals unchanged",font=font(12),fill="#5d6b78")
out=OUT/"desert_scarab_native80_and_4x_mobile_comparison.png"
sheet.save(out,optimize=True)
report={"schema":"mercury-desert-scarab-visual-review-v1",
        "sourceQAsha256":sha(ROOT/"desert_scarab_native80_qa.json"),
        "all4ImagesAndTilesVerified":True,
        "native80DisplayAt100PercentPixels":True,
        "4xNearestNeighborDisplay":True,
        "noSourceEdits":True,"allUnapproved":True,
        "noROMIntegration":True,"noHistoricalVoteChanges":True,
        "composite":out.name,"compositeSHA256":sha(out),"views":summary}
(OUT/"visual_review_qa.json").write_text(json.dumps(report,indent=2)+"\n")
print("VISUAL_REVIEW_QA",json.dumps({"views":len(summary),"composite":out.name,
                                      "sha256":sha(out),"allUnapproved":True,
                                      "noROMChanges":True,"roundTrips":True}))
