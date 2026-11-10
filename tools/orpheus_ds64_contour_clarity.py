#!/usr/bin/env python3
"""Stronger contour-first DS64 cleanup from checked-in genuine Orpheus tile bytes.

Flygon's face/wing overlap is simplified at native size with material-separated
indexed-pixel clusters. Vibrava linework remains unchanged from prior verified
iteration. Original outlines, alpha, colors, anatomy, user decisions, ROM untouched.
"""
from pathlib import Path
from collections import Counter
from PIL import Image,ImageDraw,ImageFont
import hashlib, json, struct,base64,statistics
ROOT=Path("review/candidates/orpheus-2026-11-09-UNAPPROVED/linework-polish")
OUT=Path("report/flygon_contour")
OUT.mkdir(parents=True,exist_ok=True)
PINNED_FLYGON="72c4a618daa039603c547535cba3de0aa1d2a0492884942ed9064ed9b02a6fb8"
PINNED_VIBRAVA="f2e04270b13e6e97eae4e4488dce2e1cab7ec2576ff238ea8d0f2d6d93da01b9"
def sha(data):return hashlib.sha256(data).hexdigest()
def decode(buf):
 assert len(buf)==2048
 a=[0]*4096;p=0
 for by in range(0,64,8):
  for bx in range(0,64,8):
   for dy in range(8):
    for dx in range(0,8,2):
     val=buf[p];p+=1
     a[(by+dy)*64+bx+dx]=val&15;a[(by+dy)*64+bx+dx+1]=val>>4
 return a
def encode(a):
 buf=bytearray()
 for by in range(0,64,8):
  for bx in range(0,64,8):
   for dy in range(8):
    for dx in range(0,8,2):
     l=a[(by+dy)*64+bx+dx];r=a[(by+dy)*64+bx+dx+1]
     buf.append(l|(r<<4))
 assert len(buf)==2048 and decode(bytes(buf))==a
 return bytes(buf)
def display(a,pal):
 words=struct.unpack("<16H",pal)
 def rgb(n):return tuple(round((n>>(5*k)&31)*255/31) for k in range(3))
 im=Image.new("RGBA",(64,64))
 im.putdata([(*rgb(words[v]),255) if v else (0,0,0,0) for v in a])
 return im
def cls(x):
 if x<=1:return x
 if x<=6:return 2
 if x<=11:return 3
 return 4
def near(a,x,y):
 return [a[(y+dy)*64+x+dx] for dy in (-1,0,1) for dx in (-1,0,1) if dx or dy]
def isolated(a,box,category):
 x0,y0,x1,y1=box;c=0
 for y in range(max(y0,1),min(63,y1)):
  for x in range(max(x0,1),min(63,x1)):
   cur=a[y*64+x]
   if cls(cur)!=category:continue
   if sum(v==cur for v in near(a,x,y))==0:c+=1
 return c
original_f=(ROOT/"flygon_front_linework_4bpp_tiles.bin").read_bytes()
original_v=(ROOT/"vibrava_back_linework_4bpp_tiles.bin").read_bytes()
pal_f=(ROOT/"flygon_front_linework_bgr555_palette.bin").read_bytes()
pal_v=(ROOT/"vibrava_back_linework_bgr555_palette.bin").read_bytes()
assert sha(original_f)==PINNED_FLYGON and sha(original_v)==PINNED_VIBRAVA
assert len(pal_f)==len(pal_v)==32
a=decode(original_f);b=a[:]
protected={(x,y) for y in range(12,17) for x in range(21,27)}
# Each pass reads the unchanged baseline to avoid feedback/over-smoothing.
fixed=[]
for box,kind in [((19,15,33,31),"face"),
                  ((31,22,49,39),"wing_root"),
                  ((29,33,49,51),"lower_wing_crossing")]:
 x0,y0,x1,y1=box
 for y in range(max(1,y0),min(63,y1)):
  for x in range(max(1,x0),min(63,x1)):
   if (x,y) in protected:continue
   idx=y*64+x;v=a[idx]
   if v<=1:continue
   # no change if a pixel touches the transparent edge (protect external details)
   cardinal=[a[(y+dy)*64+x+dx] for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))]
   if 0 in cardinal or 1 in cardinal:continue
   neighbors=near(a,x,y)
   family=[t for t in neighbors if cls(t)==cls(v)]
   if kind=="face":
    if cls(v)!=2 or len(family)<6:continue
    preferred=Counter(family).most_common(1)[0]
    if preferred[0]==v or preferred[1]<4:continue
    target=preferred[0]
   elif kind=="wing_root":
    if cls(v)==3 and len(family)>=6:
     # Let dark original wing membrane remain a contrast border; simplify
     # interior shades to existing blue midtone or pale wing membrane.
     target=8 if v in (7,8,9) else 11
     if target==v:continue
     if sum(t in (7,8,9) for t in family)>=5:target=8
     elif sum(t in (10,11) for t in family)>=5:target=11
     else:continue
    elif cls(v)==4 and sum(cls(t)==3 for t in neighbors)>=7:
     target=11
    else:continue
   else:
    if cls(v)!=3 or len(family)<7:continue
    tone,cnt=Counter(family).most_common(1)[0]
    if tone==v or cnt<5:continue
    target=tone
   if target in (0,1) or target==v:continue
   b[idx]=target
   fixed.append(dict(x=x,y=y,before=v,after=target,section=kind))
# Explicit preserve pupil and the dark boundary lines of previous pass.
assert b[14*64+23]==a[14*64+23]==2
assert b[14*64+24]==a[14*64+24]==2
assert all((u==0)==(v==0) and (u==1)==(v==1) for u,v in zip(a,b))
changed=sum(x!=y for x,y in zip(a,b))
assert 0<=changed<=130 and changed==len(fixed)
outbuf=encode(b)
out=display(b,pal_f)
old=display(a,pal_f)
assert out.getchannel("A").tobytes()==old.getchannel("A").tobytes()
assert len(set(out.getdata()))<=16
assert display(decode(outbuf),pal_f).tobytes()==out.tobytes()
(OUT/"flygon_front_contour64.png").write_bytes(b"") if False else None
out.save(OUT/"flygon_front_contour64.png",optimize=True)
(OUT/"flygon_front_contour_4bpp_tiles.bin").write_bytes(outbuf)
(OUT/"flygon_front_contour_bgr555_palette.bin").write_bytes(pal_f)
# The latest Vibrava needs no extra pixel manipulation; copy exact source-authentic linework files.
v=decode(original_v)
assert display(v,pal_v).tobytes()==Image.open(ROOT/"vibrava_back_linework64.png").convert("RGBA").tobytes()
vimg=display(v,pal_v)
vimg.save(OUT/"vibrava_back_linework64.png",optimize=True)
(OUT/"vibrava_back_linework_4bpp_tiles.bin").write_bytes(original_v)
(OUT/"vibrava_back_linework_bgr555_palette.bin").write_bytes(pal_v)

font_path=next((p for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf","/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"] if Path(p).exists()),None)
def font(sz):return ImageFont.truetype(font_path,sz) if font_path else ImageFont.load_default()
def onbg(im,size):
 bg=Image.new("RGBA",(size,size),(238,242,246,255))
 bg.alpha_composite(im.resize((size,size),Image.Resampling.NEAREST))
 return bg.convert("RGB")
S=Image.new("RGB",(1060,850),"#f5f7f9");d=ImageDraw.Draw(S)
d.text((18,17),"MERCURY REDUX / FLYGON FACE + WING CONTOUR CLARITY TEST",font=font(21),fill="#273846")
d.text((18,47),"Bigger face/wing-internal cleanup from true Orpheus DS64 indexed tiles; one-pixel eye protected",font=font(13),fill="#516576")
d.text((18,70),"UNAPPROVED • no source silhouette or palette change • Vibrava unchanged from latest linework",font=font(13),fill="#984742")
y=111
d.rounded_rectangle((12,y,1048,550),radius=13,fill="#ffffff",outline="#cdd6de",width=2)
d.text((22,y+12),f"FLYGON FRONT — {changed} interior color-index changes",font=font(18),fill="#273846")
d.text((22,y+44),"Previous native 64px",font=font(13),fill="#4d6070")
d.text((297,y+44),"Contour-priority 64px",font=font(13),fill="#4d6070")
d.text((585,y+44),"Head/forewing detail",font=font(13),fill="#4d6070")
S.paste(onbg(old,256),(22,y+67))
S.paste(onbg(out,256),(295,y+67))
crop=out.crop((17,10,50,42)).resize((264,256),Image.Resampling.NEAREST)
bkg=Image.new("RGBA",crop.size,(238,242,246,255));bkg.alpha_composite(crop)
S.paste(bkg.convert("RGB"),(584,y+67))
S.paste(onbg(out,64),(870,y+119))
d.text((844,y+195),"True native 1×",font=font(13),fill="#526475")
d.text((22,y+350),"No transparent/outline changes. Dark eye remains intact, wing/body material groups preserved.",font=font(13),fill="#526879")
d.text((22,y+381),"All 64×64 4bpp pixels decoded from 2048-byte tile file; original 32-byte BGR555 palette",font=font(13),fill="#347c5b")
y=574
d.rounded_rectangle((12,y,1048,829),radius=13,fill="#ffffff",outline="#cdd6de",width=2)
d.text((22,y+13),"VIBRAVA BACK — retained last linework version (no additional edits)",font=font(17),fill="#273846")
S.paste(onbg(vimg,192),(22,y+46))
S.paste(onbg(vimg,64),(241,y+108))
d.text((327,y+95),"Connected turquoise wing veins and antenna shades remain.",font=font(14),fill="#526475")
d.text((327,y+122),"This version already has a clearer 64px wing than the earlier blank membrane.",font=font(13),fill="#526475")
d.text((22,y+224),"Original source art, other four views, historical votes, ROM and sprite approvals untouched.",font=font(13),fill="#9a5147")
preview=OUT/"orpheus_ds64_contour_before_after.png";S.save(preview,optimize=True)
metrics={
"schema":"mercury-orpheus-ds64-contour-clarity-v1",
"candidateStatus":"UNAPPROVED_RESEARCH",
"sourceFlygonTileSHA256":sha(original_f),
"revisedFlygonTileSHA256":sha(outbuf),
"sourceVibravaTileSHA256":sha(original_v),
"revisedVibravaTileSHA256":sha(original_v),
"flygonChangedPixels":changed,
"originalFlygonColorSpeckles":isolated(a,(18,12,50,50),3),
"newFlygonColorSpeckles":isolated(b,(18,12,50,50),3),
"originalAlphasAndOutlinesUnchanged":True,
"pupilTwoPixelsPreserved":True,
"paletteBytes":32,"tileBytes":2048,
"otherFourViewsUnchanged":True,"sourceArtUnchanged":True,
"approved":False,"romIntegrated":False,
"notes":["Deliberate simplification of existing indexed material colors in head, wing root and lower forewing. Not a reposed new sprite.",
"Readability is still a subjective criterion; 64px engine image must be approved by human reviewer."],
"perPixelEdits":fixed}
(OUT/"contour_qa.json").write_text(json.dumps(metrics,indent=2)+"\n")
print("CONTOUR_SUMMARY",json.dumps({"changedPixels":changed,"speckleCountBefore":metrics["originalFlygonColorSpeckles"],"speckleCountAfter":metrics["newFlygonColorSpeckles"],"vibravaViewsChanged":0,"approved":False,"romIntegrated":False}))
for filename in ["orpheus_ds64_contour_before_after.png","contour_qa.json","flygon_front_contour64.png","flygon_front_contour_4bpp_tiles.bin","flygon_front_contour_bgr555_palette.bin",
 "vibrava_back_linework64.png","vibrava_back_linework_4bpp_tiles.bin","vibrava_back_linework_bgr555_palette.bin"]:
 p=OUT/filename
 print("CONTOUR_FILE_START",filename)
 print(base64.b64encode(p.read_bytes()).decode("ascii"))
 print("CONTOUR_FILE_END",filename)
