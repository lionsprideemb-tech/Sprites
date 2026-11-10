#!/usr/bin/env python3
"""Clarity-first, native-scale pixel-linework study for real Orpheus DS64 sprites.

Original source/tile geometry and artist's silhouettes are preserved. Unlike the
previous palette-microfix studies, this creates continuous source-referenced
wing/antenna and facial color planes at individual *existing opaque* pixels.
All changed color indices are listed in a QA report and nothing is approved.
"""
from pathlib import Path
from collections import Counter
from PIL import Image,ImageDraw,ImageFont
import hashlib,json,struct,base64

ROOT=Path("review/candidates/orpheus-2026-11-09-UNAPPROVED/targeted-final-local-pixels")
OUT=Path("report/linework_polish")
OUT.mkdir(parents=True,exist_ok=True)
CHECK={
 "flygon_front":("0d906469534f897c50813673ba3473c54173dc975cdaceb93a371e80f6df6d3d",
                 "4a6eb782f3db86decea8d0892a3e342fa8451a2932744b89a5d328a838e0efaf"),
 "vibrava_back":("5b58eb559e085e08e2da013c804b265a9ecdb8179b84b76e1bc097d8972b301b",
                 "02fa57e49ff490c8035368812c872b53b05c0bc1b439438bad307858369c83ce")
}
def sha(data):return hashlib.sha256(data).hexdigest()
def readpixels(buf):
 assert len(buf)==2048
 a=[0]*4096;p=0
 for by in range(0,64,8):
  for bx in range(0,64,8):
   for dy in range(8):
    for dx in range(0,8,2):
     v=buf[p];p+=1;a[(by+dy)*64+bx+dx]=v&15;a[(by+dy)*64+bx+dx+1]=v>>4
 assert p==2048
 return a
def pack(a):
 assert len(a)==4096 and all(0<=x<16 for x in a)
 out=bytearray()
 for by in range(0,64,8):
  for bx in range(0,64,8):
   for dy in range(8):
    for dx in range(0,8,2):
     lo=a[(by+dy)*64+bx+dx];hi=a[(by+dy)*64+bx+dx+1];out.append(lo|(hi<<4))
 assert len(out)==2048 and readpixels(bytes(out))==a
 return bytes(out)
def rgb(w):return tuple(round(255*((w>>(5*i))&31)/31) for i in range(3))
def render(a,p):
 words=struct.unpack("<16H",p)
 im=Image.new("RGBA",(64,64))
 im.putdata([(*rgb(words[k]),255) if k else (0,0,0,0) for k in a])
 return im
def bresenham(x1,y1,x2,y2):
 dx=abs(x2-x1);dy=-abs(y2-y1)
 sx=1 if x1<x2 else -1
 sy=1 if y1<y2 else -1
 err=dx+dy
 while True:
  yield (x1,y1)
  if x1==x2 and y1==y2:break
  twice=2*err
  if twice>=dy:err+=dy;x1+=sx
  if twice<=dx:err+=dx;y1+=sy
def classify(v):
 if v==0:return 0
 if v==1:return 1
 if v<=6:return 2
 if v<=11:return 3
 return 4
def bg(img,size):
 zoom=img.resize((size,size),Image.Resampling.NEAREST)
 b=Image.new("RGBA",(size,size),(238,243,247,255));b.alpha_composite(zoom)
 return b.convert("RGB")
font_file=next((x for x in ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf","/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"] if Path(x).exists()),None)
def font(n):return ImageFont.truetype(font_file,n) if font_file else ImageFont.load_default()

W,H=1060,1110
sheet=Image.new("RGB",(W,H),"#f5f7f8")
d=ImageDraw.Draw(sheet)
d.text((18,14),"MERCURY REDUX / SOURCE-TRUE DS64 NATIVE LINEWORK POLISH",font=font(21),fill="#253544")
d.text((18,45),"Existing Orpheus 64px sprite → continuous face/wing shading details → native 64px proof",font=font(14),fill="#4d6172")
d.text((18,67),"UNAPPROVED: No original asset, silhouette, palette, historical vote or ROM changed",font=font(13),fill="#a34949")
ALL=[]
for row,name in enumerate(("flygon_front","vibrava_back")):
    oldbuf=(ROOT/f"{name}_4bpp_tiles.bin").read_bytes()
    palette=(ROOT/f"{name}_bgr555_palette.bin").read_bytes()
    assert sha(oldbuf)==CHECK[name][0] and sha(palette)==CHECK[name][1], "Pinned input mismatch"
    orig=readpixels(oldbuf)
    original_png=Image.open(ROOT/f"{name}_targeted64.png").convert("RGBA")
    assert render(orig,palette).tobytes()==original_png.tobytes(), "Source index and PNG diverged"
    a=orig[:];ops=[];skipped=[]
    def recolor(x,y,to,reason,allowed=None):
        assert 1<=x<=62 and 1<=y<=62
        k=y*64+x;prev=a[k]
        if prev==to:return
        if prev<=1 or to<=1:
            skipped.append(dict(x=x,y=y,previous=prev,requested=to,reason=reason,guard="transparent/outline protected"))
            return
        if allowed is not None and prev not in allowed:
            skipped.append(dict(x=x,y=y,previous=prev,requested=to,reason=reason,guard="material class protected"))
            return
        a[k]=to;ops.append(dict(x=x,y=y,old=prev,new=to,reason=reason))
    if name=="flygon_front":
        # Strengthen pupil and eye-to-muzzle shading so the eye is the focal point.
        for x,y,z,why in [
          (24,14,2,"second dark eye/pupil pixel"),
          (24,16,4,"eye rim shading"),
          (24,17,4,"eye rim shading"),
          (26,19,3,"dark muzzle shading"),
          (26,18,3,"muzzle shadow continuity"),
          (27,19,3,"muzzle shadow continuity")
        ]: recolor(x,y,z,why,allowed=[2,3,4,5,6,12,13,14,15])
        # One continuous dark turquoise curve, across forewing/body contact.
        ridge=[(34,24),(34,25),(35,26),(35,27),(35,28),(36,28),(37,29),(38,30)]
        for i,(x,y) in enumerate(ridge):
            recolor(x,y,8 if i<6 else 9,"continuous forewing/body dividing edge",allowed=[7,8,9,10,11,5,6])
        # Group small shading flecks in the cheek/neck without touching dark line art.
        for yy in range(16,24):
            for xx in range(20,32):
                k=yy*64+xx
                if a[k] not in (5,6):continue
                near=[orig[(yy+dy)*64+xx+dx] for dy in (-1,0,1) for dx in (-1,0,1) if dx or dy]
                if sum(t in (2,3,4) for t in near)>=4:
                    recolor(xx,yy,4,"consolidate face/neck midtone")
        # Lightly consolidate high-frequency wing-root color spots; no cross-material blending.
        for yy in range(27,37):
            for xx in range(31,49):
                k=yy*64+xx;v=a[k]
                if classify(v)!=3:continue
                near=[a[(yy+dy)*64+xx+dx] for dy in (-1,0,1) for dx in (-1,0,1) if dx or dy]
                source=[t for t in near if classify(t)==3]
                if len(source)<6:continue
                tone,count=Counter(source).most_common(1)[0]
                if tone!=v and count>=5:
                    recolor(xx,yy,tone,"join wing-root shade clusters")
    else:
        # Antenna bases are narrow. Shade their existing colored pixels but do not thicken outline.
        for x,y,to in [(46,14,3),(45,14,3),(54,13,5),(54,14,5),
                       (47,20,7),(47,21,3),(47,22,3),(53,21,3),(53,22,4)]:
            recolor(x,y,to,"clarify antenna stalk/curl",allowed=[2,3,4,5,6,7,8,9,10,11])
        # Wing structure must be a *connected vein*, not isolated turquoise dots.
        # Each color is sampled only from the existing pale cyan wing membrane.
        drawn=0
        for seg,shade in [
            ((35,42,13,50),10),
            ((34,47,23,52),10),
        ]:
            for x,y in bresenham(*seg):
                old=a[y*64+x]
                if old in (9,10,11):
                    recolor(x,y,shade,"continuous membrane vein",allowed=[9,10,11]);drawn+=1
                else:
                    skipped.append(dict(x=x,y=y,previous=old,requested=shade,reason="wing vein segment",guard="outside wing membrane"))
        assert drawn>=22, f"Insufficient continuous wing vein coverage: {drawn}"
        for x,y,shade in [(34,42,9),(35,43,9),(33,44,9),(34,46,9)]:
            recolor(x,y,shade,"ground wing vein at body",allowed=[9,10,11])
        # Reconcile a few root colors without inventing a silhouette.
        for xx,yy in [(43,39),(43,40),(44,40),(44,41),(45,41)]:
            recolor(xx,yy,3,"body-wing root shadow",allowed=[4,5,6])
    # Validate physical correctness and keep the art-source untouched.
    assert all((p==0)==(q==0) and (p==1)==(q==1) for p,q in zip(orig,a))
    assert len({z for z in a if z})<=15
    assert len(ops)<=150
    bytebuf=pack(a);outpng=render(a,palette)
    assert outpng.getchannel("A").tobytes()==original_png.getchannel("A").tobytes()
    assert render(readpixels(bytebuf),palette).tobytes()==outpng.tobytes()
    root=OUT/f"{name}_linework64"
    pngfile=Path(str(root)+".png");pngfile.parent.mkdir(parents=True,exist_ok=True);outpng.save(pngfile,optimize=True)
    tile=OUT/f"{name}_linework_4bpp_tiles.bin";tile.write_bytes(bytebuf)
    pal=OUT/f"{name}_linework_bgr555_palette.bin";pal.write_bytes(palette)
    assert pal.read_bytes()==palette
    diff=sum(p!=q for p,q in zip(orig,a))
    assert diff==len({(p["x"],p["y"]) for p in ops}),"Duplicate edit coordinate: require transparent diff log"
    summary=dict(view=name,changedPixels=diff,changeLog=ops,skippedChanges=skipped,
       sourceTileSHA256=sha(oldbuf),newTileSHA256=sha(bytebuf),
       unchangedPaletteSHA256=sha(palette),nativePixels=[64,64],
       exactAlphaAndOutlinePreserved=True,
       paletteEntryCount=16,opaquePaletteColorsUsed=len({z for z in a if z}),
       tileBytes=2048,paletteBytes=32,
       approved=False,romIntegrated=False,sourceArtworkModified=False)
    ALL.append(summary)
    y=104+row*490
    d.rounded_rectangle((10,y,W-10,y+480),radius=12,fill="white",outline="#cfdae2",width=2)
    d.text((22,y+9),name.upper().replace("_","  ")+f"  •  {diff} real internal pixel edits",font=font(18),fill="#273847")
    d.text((22,y+44),"CURRENT (4×)",font=font(13),fill="#516474")
    d.text((302,y+44),"LINEWORK POLISH (4×)",font=font(13),fill="#516474")
    d.text((590,y+44),"ENLARGED LOCAL DETAIL",font=font(13),fill="#516474")
    sheet.paste(bg(original_png,256),(22,y+67))
    sheet.paste(bg(outpng,256),(302,y+67))
    roi=(17,11,45,40) if name=="flygon_front" else (10,30,57,54)
    src=outpng.crop(roi);scale=7 if name=="flygon_front" else 6
    crop=src.resize((src.width*scale,src.height*scale),Image.Resampling.NEAREST)
    cb=Image.new("RGBA",crop.size,(238,243,247,255));cb.alpha_composite(crop)
    sheet.paste(cb.convert("RGB"),(590,y+67))
    sheet.paste(bg(outpng,64),(590,y+321))
    d.text((666,y+328),"True native 64px",font=font(14),fill="#526574")
    d.text((22,y+361),"Face/wing or antenna/vein detail kept within existing shape",font=font(14),fill="#4d6271")
    d.text((22,y+391),"Hardware tile + unchanged BGR555 palette round-trip: PASS",font=font(13),fill="#32785b")
    d.text((22,y+428),"Not approved • Nothing imported into Platinum • Other four views untouched",font=font(13),fill="#98524b")
    print("LINEWORK_VIEW",json.dumps(summary,sort_keys=True))
sheetfile=OUT/"orpheus_ds64_linework_before_after.png"
sheet.save(sheetfile,optimize=True)
manifest={
 "schema":"mercury-orpheus-native-pixel-linework-v1",
 "selectedForApproval":False,"romIntegrated":False,
 "sourceDesignsModified":False,"silhouettesChanged":False,
 "stagePalettesChanged":False,"historicalVotesChanged":False,
 "otherFourViewsUnchanged":["trapinch_front","trapinch_back","vibrava_front","flygon_back"],
 "limitations":["Clearer linework is an experimental visual judgment, not a guarantee of approval.",
   "The Orpheus composition has dense head/wing anatomy at 64px, so an artist may need to rethink internal shapes if still unclear."],
 "views":ALL}
(OUT/"linework_qa.json").write_text(json.dumps(manifest,indent=2)+"\n")
print("LINEWORK_SUMMARY",json.dumps({r["view"]:r["changedPixels"] for r in ALL}))
for filename in ["orpheus_ds64_linework_before_after.png","linework_qa.json",
 "flygon_front_linework64.png","flygon_front_linework_4bpp_tiles.bin","flygon_front_linework_bgr555_palette.bin",
 "vibrava_back_linework64.png","vibrava_back_linework_4bpp_tiles.bin","vibrava_back_linework_bgr555_palette.bin"]:
 p=OUT/filename
 print("LINEWORK_FILE_START",filename)
 print(base64.b64encode(p.read_bytes()).decode("ascii"))
 print("LINEWORK_FILE_END",filename)
