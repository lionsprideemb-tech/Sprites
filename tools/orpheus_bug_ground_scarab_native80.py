#!/usr/bin/env python3
"""Mercury Redux: actual source-locked 80x80 Orpheus Bug/Ground palette + scute study.

Four genuine indexed DS OBJ 4bpp frames (Vibrava/Flygon normal front/back).
No new anatomy, silhouette, alpha, evolution, decision, or ROM changes.
"""
from collections import Counter
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import colorsys,hashlib,json,math,struct

P=Path("review/candidates/orpheus-2026-11-09-UNAPPROVED")
ORIGINAL=P/"native80-original-colors"
FINAL=P/"native80-final-pixel-polish"
S=Path("safepng")
O=Path("report/orpheus_bug_ground_scarab_native80")
O.mkdir(parents=True,exist_ok=True)
RAR=Path("orpheus-original-resources.rar")
SOURCE_PIN="72539b83b55a427c4adcdf2f3e5397cc28371875a720f687ffcf4e2a6d803ef9"
assert RAR.exists() and hashlib.sha256(RAR.read_bytes()).hexdigest()==SOURCE_PIN
SRC_SHAS={
 "vibrava_front":"5a2d79d6707f35237d8bb7ec32990b9a0c9b799d5ddbf19fe972a8d6c10f7060",
 "vibrava_back":"1182bab5ff5feb9efc5afac02e9777d7298fcdba690b09082b6b567540f7c215",
 "flygon_front":"0648e090ab0a869bf452cab5e02d2d7da3bd9454b0b400bfcedb022dd72a321c",
 "flygon_back":"f9586b2b6504f0a4b2d79bd9597c6c59ea7df1be4e96ca1c2fb284dcaa42aa51",
}
# DS 4bpp palette entries, each 15 opaque colors + transparent #0.
# 1 outline; 2..7 brown exoskeleton and sandstone plates;
# 8..12 olive/sage wing veins and membranes; 13 ivory claw/contrast;
# 14 glossy jade eye; 15 pale lime eye glint.
HEX={
 "vibrava":[
 "#000000","#2D241A","#49382B","#664A32","#906845","#B58A59",
 "#D4AB77","#EDD4AA","#435239","#617648","#829B55","#AAC27D",
 "#D4E0A3","#F2E8CA","#639447","#E6F2AD"],
 "flygon":[
 "#000000","#251C17","#442F22","#61422B","#825939","#AF7E50",
 "#D0A16B","#E9C697","#394B32","#587345","#7D9B53","#AAC275",
 "#D1DF9A","#F3E7CA","#5F9E45","#E2F3B0"]
}
def rgb(w):return tuple(round(((w>>(5*i))&31)*255/31) for i in range(3))
def bgr555(hexcode):
    vals=[int(hexcode[i:i+2],16) for i in (1,3,5)]
    vv=[round(v*31/255) for v in vals]
    return vv[0]|vv[1]<<5|vv[2]<<10
PAL={k:[bgr555(c) for c in v] for k,v in HEX.items()}
assert all(len(v)==16 and v[0]==0 and len(set(v[1:]))==15 for v in PAL.values())
def sha(b):return hashlib.sha256(b).hexdigest()
def luminance(c):return .2126*c[0]+.7152*c[1]+.0722*c[2]
def classify(c):
    r,g,b=c;h,s,v=colorsys.rgb_to_hsv(r/255,g/255,b/255)
    l=luminance(c)
    if l < 41:return "outline"
    if s < .11 and l < 93:return "outline"
    if b > r*1.10 and b > g*1.06 and s>.12:return "claw"
    if s < .16 and l>160:return "claw"
    if 0.100<=h<=.200 and s>.14:return "wing"
    if 0.200 < h < .505 and s>.12:return "body"
    if .500<=h<.80 and s>.10:return "claw"
    if l>177:return "claw"
    return "body"
def choose_index(c,stage,cls,lo,hi):
    y=luminance(c)
    t=max(0,min(1,(y-lo)/(hi-lo) if hi>lo else .5))
    # Preserve sharp source-index contours by bucketing per semantic color class.
    if cls=="outline":return 1 if y<61 else 2
    if cls=="body":return (2,3,4,5,6,7)[min(5,round(t*5))]
    if cls=="wing":return (8,9,10,11,12)[min(4,round(t*4))]
    if cls=="claw":return (2,3,7,13)[min(3,round(t*3))]
    raise AssertionError(cls)
def pack(idx):
    assert len(idx)==6400
    data=bytearray()
    for by in range(0,80,8):
        for bx in range(0,80,8):
            for y in range(8):
                for x in range(0,8,2):
                    a=idx[(by+y)*80+bx+x];b=idx[(by+y)*80+bx+x+1]
                    assert 0<=a<16 and 0<=b<16
                    data.append(a|(b<<4))
    assert len(data)==3200
    return bytes(data)
def unpack(data):
    assert len(data)==3200
    idx=[0]*6400;k=0
    for by in range(0,80,8):
        for bx in range(0,80,8):
            for y in range(8):
                for x in range(0,8,2):
                    t=data[k];k+=1
                    idx[(by+y)*80+bx+x]=t&15
                    idx[(by+y)*80+bx+x+1]=t>>4
    return idx
def render(idx,words):
    out=Image.new("RGBA",(80,80))
    out.putdata([(*rgb(words[v]),255) if v else (0,0,0,0) for v in idx])
    return out
def font(n):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf","/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"):
        if Path(p).exists():return ImageFont.truetype(p,n)
    return ImageFont.load_default()
def panel(dest,im,x,y,size):
    z=im.convert("RGBA").resize((size,size),Image.Resampling.NEAREST)
    bg=Image.new("RGBA",(size,size),"#EDF2F5")
    bg.alpha_composite(z)
    dest.paste(bg.convert("RGB"),(x,y))
def mask_eye(x,y,name,role,color,cls):
    # Eye is kept insect-green rather than being rendered as brown body armor.
    # The masks are narrow: preserve source black linework and white glints.
    boxes={
        "flygon_front":(34,18,42,26),
        "flygon_back":(67,37,80,45),
        "vibrava_front":(32,39,41,47),
        "vibrava_back":(69,47,80,63),
    }
    x0,y0,x1,y1=boxes[name+"_"+role]
    if not (x0<=x<x1 and y0<=y<y1):return None
    r,g,b=color
    h,s,v=colorsys.rgb_to_hsv(r/255,g/255,b/255)
    # Require a conspicuously saturated green highlight; not all face pixels.
    if cls=="body" and .205<=h<=.425 and s>.6 and max(color)>142 and g>r*1.25:
        return 14
    if cls=="claw" and min(color)>195 and x0+2<=x<x1-2:
        return 15
    return None
def decorate_scutes(idx,stage,role):
    """Minimal interior scale arcs: no alpha edits, no outlines, no wing veins."""
    mask={2,3,4,5,6,7}
    previous=idx[:]
    max_motifs=8 if stage=="flygon" else 4
    candidates=[]
    # Keep face, antennae, wing roots and leg joints free of added texture.
    if stage=="flygon":
        y0,y1=(42,68) if role=="front" else (39,69)
    else:
        y0,y1=(29,66) if role=="front" else (35,67)
    for y in range(y0,y1,5):
        for x in range(13+(y//5%2)*3,72,6):
            if stage=="flygon" and role=="front" and x>49:continue
            if stage=="vibrava" and role=="back" and x>58:continue
            # candidate 3x3 must be inside a substantial midtone body patch
            patch=[idx[(y+dy)*80+x+dx] for dy in (-1,0,1) for dx in (-1,0,1)]
            if len(patch)!=9 or any(k not in mask for k in patch):continue
            if not (idx[y*80+x] in (4,5,6) and idx[y*80+x+1] in (4,5,6)):continue
            candidates.append((x,y))
    # Order by distance from borders, and spatial spacing; do not fill every flat pixel.
    # Vibrava FRONT has a very thin thorax: use two source-checked 2px plate
    # marks at actual solid body interior rather than inventing an outline.
    if stage=="vibrava" and role=="front":
        chosen=[(28,47),(33,47)]
        for xx,yy in chosen:
            assert all(idx[(yy+dy)*80+xx+dx] in mask
                       for dx,dy in ((0,0),(1,0),(0,1)))
    else:
        chosen=[]
    for x,y in ([] if stage=="vibrava" and role=="front" else candidates):
        if any(abs(x-xx)<9 and abs(y-yy)<8 for xx,yy in chosen):continue
        chosen.append((x,y))
        if len(chosen)>=max_motifs:break
    edits=[]
    for x,y in chosen:
        # Subtle warm outlines that echo beetle scales, one dark lip and one glint.
        for xx,yy,darker in ((x,y,True),(x+1,y,True),(x,y+1,False)):
            pos=yy*80+xx;old=idx[pos]
            assert old in mask
            new=max(2,old-1) if darker else min(7,old+1)
            if new!=old:
                idx[pos]=new;edits.append(dict(x=xx,y=yy,fromIndex=old,toIndex=new,feature="scale/scute"))
    return edits,chosen

records=[]
images={}
for stage,number in (("vibrava",329),("flygon",330)):
  for role in ("front","back"):
    key=stage+"_"+role
    src_path=S/f"{number}{'b' if role=='back' else ''}_1.png"
    assert sha(src_path.read_bytes())==SRC_SHAS[key],key
    big=Image.open(src_path).convert("RGBA")
    assert big.size==(160,160)
    half=big.resize((80,80),Image.Resampling.NEAREST)
    if key=="flygon_front":
        # Preserve the user's previously validated six-pixel readability cleanup.
        baseline=Image.open(FINAL/"flygon_front_original_colors80_final_micro_polish.png").convert("RGBA")
        assert sha((FINAL/"flygon_front_original_colors80_final_micro_polish.png").read_bytes())=="e8a987cf43b61bb2a16e669f941830f2b6e195ea37e8113426f64d9e4d6e88f4"
    elif key=="vibrava_back":
        baseline=Image.open(ORIGINAL/"vibrava_back_source_colors80.png").convert("RGBA")
        assert sha((ORIGINAL/"vibrava_back_source_colors80.png").read_bytes())=="670b7ada44953a294b796835833299ad27a537374d49d69dda16dc9c7da7b65f"
    else:
        baseline=half
    assert baseline.getchannel("A").tobytes()==half.getchannel("A").tobytes()
    # The original art groups define material identity. Blue-grey = pale claws.
    pixels=list(half.getdata())
    classes=[classify(p[:3]) if p[3] else "transparent" for p in pixels]
    ranges={}
    for cl in ("body","wing","claw"):
        ls=[luminance(p[:3]) for p,c in zip(pixels,classes) if c==cl]
        ranges[cl]=(min(ls),max(ls)) if ls else (0,255)
    idx=[]
    eye_count=0
    for i,(p,cl) in enumerate(zip(pixels,classes)):
        if not p[3]:idx.append(0);continue
        x,y=i%80,i//80
        eye=mask_eye(x,y,stage,role,p[:3],cl)
        if eye is not None:
            idx.append(eye);eye_count+=1
        else:
            lo,hi=ranges[cl] if cl!="outline" else (0,100)
            idx.append(choose_index(p[:3],stage,cl,lo,hi))
    # Reapply only the six previously QA'd Flygon-front eye/muzzle/junction edits,
    # preserving their relative visual intention within the new color palette.
    restored_detail=[]
    if key=="flygon_front":
        pin=[
            ("eye glint",37,21,15),("eye pupil",38,21,1),
            ("muzzle contour",33,27,3),("muzzle contour",33,28,3),
            ("forewing joint",42,34,2),("forewing joint",42,35,13)
        ]
        for feature,x,y,dest in pin:
            pos=y*80+x
            assert idx[pos]!=0
            old=idx[pos];idx[pos]=dest
            restored_detail.append(dict(feature=feature,x=x,y=y,oldIndex=old,newIndex=dest))
    predetail=idx[:]
    scutes,anchors=decorate_scutes(idx,stage,role)
    words=PAL[stage]
    rgba=render(idx,words)
    assert rgba.size==(80,80)
    assert rgba.getchannel("A").tobytes()==half.getchannel("A").tobytes()
    tiledata=pack(idx)
    assert unpack(tiledata)==idx and render(unpack(tiledata),words).tobytes()==rgba.tobytes()
    paldata=struct.pack("<16H",*words);assert len(paldata)==32
    png=O/f"{key}_desert_scarab_80.png"
    tiles=O/f"{key}_desert_scarab_80_4bpp_tiles.bin"
    pal=O/f"{key}_desert_scarab_80_palette.bin"
    rgba.save(png,optimize=True);tiles.write_bytes(tiledata);pal.write_bytes(paldata)
    assert len(tiledata)==3200 and len(paldata)==32 and len(set(idx)-{0})<=15
    changedvsbaseline=sum(1 for a,b in zip(baseline.getdata(),rgba.getdata()) if a[3] and a[:3]!=b[:3])
    nopaque=sum(p[3]>0 for p in pixels)
    record={
        "view":key,"sourceSHA256":SRC_SHAS[key],
        "sourceCanvas":[160,160],"outputCanvas":[80,80],
        "stagePalette":HEX[stage],"opaquePaletteEntries":15,
        "artworkSilhouettePreserved":True,"outputAlphaExact":True,
        "originalSourceUntouched":True,
        "baselineSource":"previous verified 6px polish" if key=="flygon_front" else ("original-color source80" if key=="vibrava_back" else "original Orpheus 2x half"),
        "baselineOpaquePixels":nopaque,"changedRGBApixelsVsBaseline":changedvsbaseline,
        "eyeAccents":eye_count,"preservedFlygonFaceEdits":restored_detail,
        "scuteMotifAnchors":anchors,"scutePixelEdits":scutes,"scuteChangedPixels":len(scutes),
        "tileBytes":len(tiledata),"paletteBytes":len(paldata),
        "tileExactDecode":True,"paletteBGR555":True,
        "pngSHA256":sha(png.read_bytes()),"tileSHA256":sha(tiledata),
        "paletteSHA256":sha(paldata),
        "png":png.name,"tiles":tiles.name,"palette":pal.name,
        "approved":False,"romIntegrated":False}
    records.append(record)
    images[key]=(baseline,rgba)
    print("SCARAB_VIEW",json.dumps({k:record[k] for k in (
        "view","baselineOpaquePixels","changedRGBApixelsVsBaseline",
        "eyeAccents","scuteChangedPixels","tileExactDecode","pngSHA256")},sort_keys=True))

w,h=1110,1610
sheet=Image.new("RGB",(w,h),"#F6F8F9")
d=ImageDraw.Draw(sheet)
d.text((18,14),"MERCURY REDUX  /  ORPHEUS DESERT-SCARAB COLOR STUDY",font=font(21),fill="#263645")
d.text((20,48),"Source-locked 80px pixel art • brown sandstone plates + olive-green wings",font=font(14),fill="#435567")
d.text((20,70),"Vibrava and Flygon FRONT/BACK  |  UNAPPROVED  |  NO ROM changes",font=font(13),fill="#A04C39")
for n,key in enumerate(("vibrava_front","vibrava_back","flygon_front","flygon_back")):
    y=103+n*362
    d.rounded_rectangle((10,y,w-12,y+346),radius=13,fill="#FFFFFF",outline="#CCD4D8",width=2)
    d.text((20,y+10),key.replace("_"," ").upper(),font=font(19),fill="#2A4151")
    before,after=images[key]
    d.text((24,y+42),"Original geometry / prior colors",font=font(13),fill="#5B6D7B")
    d.text((568,y+42),"Bug/Ground desert-scarab color + scutes",font=font(13),fill="#5B6D7B")
    panel(sheet,before,32,y+66,248)
    panel(sheet,after,578,y+66,248)
    rec=next(r for r in records if r["view"]==key)
    d.text((305,y+154),"→",font=font(32),fill="#4F6D50")
    d.text((846,y+98),"80×80\n4bpp / 15 colors",font=font(14),fill="#4D6274")
    d.text((844,y+166),f"{rec['scuteChangedPixels']} scute pixels",font=font(14),fill="#4D6274")
    d.text((20,y+322),"Original silhouette / alpha unchanged • actual DS-tiled data • not approved",font=font(12),fill="#526576")
for i,c in enumerate(HEX["flygon"][1:]):
    x=22+i*39
    d.rectangle((x,1566,x+32,1598),fill=c,outline="#929999")
sheetpath=O/"orpheus_desert_scarab_four_view_before_after.png"
sheet.save(sheetpath,optimize=True)
doc={
 "schema":"mercury-orpheus-bug-ground-desert-scarab-native80-v1",
 "sourceArchiveSHA256":SOURCE_PIN,
 "target":"Unapproved visual proposal for Bug/Ground evolved forms; no Dex or game-type data changed.",
 "method":"Real original Orpheus 160px to 80px source-locked RGBA -> semantic 15-color BGR555 palettes -> manual six-pixel Flygon detail map -> conservative interior scute shade edits -> DS OBJ 4bpp tile roundtrip",
 "allUnapproved":True,"noPlatinumChanges":True,"noHistoricalVoteChanges":True,
 "noPreviousApprovedDesignChanges":True,"noSourcePNGChanges":True,"noSpritesMainChanges":True,
 "limitations":["Color/material mapping is subjective and requires user visual review.",
                "Scute details are pixel-local shade variations, not new silhouettes or limbs.",
                "Vibrava back original 160px has some nonuniform 2x2 alpha blocks; no 160->80 lossless claim.",
                "No shiny, icon, NARC/NCGR/NCLR, animated or ROM/emulator QA is claimed."],
 "preview":sheetpath.name,"views":records}
(O/"desert_scarab_native80_qa.json").write_text(json.dumps(doc,indent=2)+"\n")
(O/"README.md").write_text(
 "# Orpheus Desert Scarab — Vibrava + Flygon genuine DS80 study (UNAPPROVED)\n\n"
 "[**Open 4-view original-versus-desert-scarab preview**](orpheus_desert_scarab_four_view_before_after.png).\n\n"
 "Preserves exact 80px alpha masks, anatomy, and original artwork positions. "
 "Brown/tan exoskeletal plates and olive insect-wing membranes evoke **Bug/Ground**. "
 "Tiny interior scute shades add surface segmentation; no new silhouette. "
 "Flygon FRONT uses the six prior eye/muzzle/wing-joint clarity coordinates. "
 "All four normal FRONT/BACK PNGs are paired with verified DS 4bpp tile and BGR555 palette files. "
 "Read [machine QA](desert_scarab_native80_qa.json) for exact hashes and edit counts.\n\n"
 "The image is not a final production resource: no alternate shiny/icon, no engine archive, "
 "no emulator test, no ROM integration, no approval, no historical KEEP/CUT changes. "
 "Source pack/artist rights documentation must remain respected.\n")
print("SCARAB_QA_SUMMARY",json.dumps({"views":len(records),"DS80":True,"tileRoundTrips":True,
    "allAlphaPreserved":True,"allUnapproved":True,"romIntegrated":False,
    "scuteEdits":sum(v["scuteChangedPixels"] for v in records)}))
