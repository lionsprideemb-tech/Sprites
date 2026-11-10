#!/usr/bin/env python3
"""Original-Orpheus normal sprites -> experimental native Platinum 80x80 battle art.

The Gen-IV target is 80x80, *not* the prior experimental 64x64 QA canvas.
Source exact-check RAR; inspect 2x pixel replication before resizing; apply the
user's existing separate stage color schemes and strict 4bpp BGR555 palette.
DO NOT edit original source files, user votes, game metadata or Platinum ROM.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from collections import Counter,defaultdict
import colorsys,hashlib,base64,json,math,struct

RAR=Path("orpheus-original-resources.rar")
SOURCE=Path("safepng")
OUT=Path("report/orpheus_native_platinum80")
OUT.mkdir(parents=True,exist_ok=True)
PIN="72539b83b55a427c4adcdf2f3e5397cc28371875a720f687ffcf4e2a6d803ef9"
assert hashlib.sha256(RAR.read_bytes()).hexdigest()==PIN,"Unknown Orpheus source archive"
STAGES=[(328,"trapinch","BUG"),(329,"vibrava","BUG/DRAGON"),(330,"flygon","BUG/DRAGON")]
def sha(data):return hashlib.sha256(data).hexdigest()
def source_class(rgb):
 r,g,b=rgb
 _,sat,val=colorsys.rgb_to_hsv(r/255,g/255,b/255)
 h=colorsys.rgb_to_hsv(r/255,g/255,b/255)[0]*360
 lum=.2126*r+.7152*g+.0722*b
 if lum<42 or (val<.24 and sat<.28):return "outline"
 if 34<=h<76 and sat>.20:return "wing"
 if 76<=h<171 and sat>.15:return "body"
 if 171<=h<=275 and sat>.12:return "accent"
 if 0<=h<34 and sat>.22:return "accent"
 if lum>178:return "wing"
 return "body"
def lum(c):return .2126*c[0]+.7152*c[1]+.0722*c[2]
def fivecolor(v):return tuple(round(255*((v>>(5*j))&31)/31) for j in range(3))
def tiles(data,dim=80):
 assert len(data)==dim*dim and dim%8==0
 b=bytearray()
 for by in range(0,dim,8):
  for bx in range(0,dim,8):
   for dy in range(8):
    for dx in range(0,8,2):
     u=data[(by+dy)*dim+bx+dx]
     v=data[(by+dy)*dim+bx+dx+1]
     assert 0<=u<16 and 0<=v<16
     b.append(u|(v<<4))
 assert len(b)==dim*dim//2
 reconstruct=[0]*(dim*dim)
 off=0
 for by in range(0,dim,8):
  for bx in range(0,dim,8):
   for dy in range(8):
    for dx in range(0,8,2):
     q=b[off];off+=1
     reconstruct[(by+dy)*dim+bx+dx]=q&15
     reconstruct[(by+dy)*dim+bx+dx+1]=q>>4
 assert reconstruct==data
 return bytes(b)
def render(index,pal,dim):
 words=struct.unpack("<16H",pal)
 img=Image.new("RGBA",(dim,dim))
 img.putdata([(*fivecolor(words[i]),255) if i else (0,0,0,0) for i in index])
 return img
def exact2x_fraction(img):
 pixels=img.load()
 count=0;same=0
 for y in range(0,160,2):
  for x in range(0,160,2):
   a=pixels[x,y]
   count+=1
   if (a==pixels[x+1,y]==pixels[x,y+1]==pixels[x+1,y+1]):same+=1
 return same,count
def half(img):
 # one source pixel from each original 2x2 block, coordinates and canvas intact
 return img.resize((80,80),Image.Resampling.NEAREST)
def tightfit(img):
 bbox=img.getchannel("A").getbbox()
 assert bbox is not None
 crop=img.crop(bbox)
 scale=min(76/crop.width,76/crop.height)
 ww=max(1,round(crop.width*scale))
 hh=max(1,round(crop.height*scale))
 cur=crop.resize((ww,hh),Image.Resampling.NEAREST)
 result=Image.new("RGBA",(80,80),(0,0,0,0))
 result.alpha_composite(cur,((80-ww)//2,(80-hh)//2))
 return result
def panel(dst,im,x,y,sz):
 bg=Image.new("RGBA",(sz,sz),(238,243,247,255))
 z=im.resize((sz,sz),Image.Resampling.NEAREST)
 bg.alpha_composite(z)
 dst.paste(bg.convert("RGB"),(x,y))
fonts=["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf","/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"]
fpath=next((p for p in fonts if Path(p).exists()),None)
def font(sz):return ImageFont.truetype(fpath,sz) if fpath else ImageFont.load_default()
source_images={}
stage_palette={}
stage_ranges={}
for num,name,typ in STAGES:
 srcs=[SOURCE/f"{num}_1.png",SOURCE/f"{num}b_1.png"]
 assert all(p.exists() for p in srcs),(name,srcs)
 ims=[Image.open(p).convert("RGBA") for p in srcs]
 assert all(i.size==(160,160) for i in ims)
 assert all({p[3] for p in im.getdata()}.issubset({0,255}) for im in ims)
 for role,p,im in zip(("front","back"),srcs,ims):source_images[(name,role)]=(p,im)
 # Reuse the *exact* finalized-to-date individual stage color direction from the 64px QA,
 # but do not imply artistic approval.
 f=Path("report/ds64_readability")/f"{name}_front_bgr555_palette.bin"
 b=Path("report/ds64_readability")/f"{name}_back_bgr555_palette.bin"
 assert f.read_bytes()==b.read_bytes(),"stage palette must match front and back"
 palette=f.read_bytes();assert len(palette)==32 and struct.unpack("<H",palette[:2])[0]==0
 stage_palette[name]=palette
 values=defaultdict(list)
 for im in ims:
  for r,g,b,a in im.getdata():
   if not a:continue
   c=(r,g,b);values[source_class(c)].append(lum(c))
 stage_ranges[name]={key:(min(arr),max(arr)) for key,arr in values.items()}
for name,rangeinfo in stage_ranges.items():
 print("PLATINUM80_GROUP_RANGES",name,rangeinfo)
def recolor(im,name):
 ranges=stage_ranges[name]
 ramplist={"outline":[1],"body":[2,3,4,5,6],"wing":[7,8,9,10,11],"accent":[12,13,14,15]}
 entries=[]
 for rgb_a in im.getdata():
  if rgb_a[3]==0:entries.append(0);continue
  color=rgb_a[:3]
  group=source_class(color)
  options=ramplist[group]
  minimum,maximum=ranges[group]
  t=(lum(color)-minimum)/(maximum-minimum) if maximum>minimum else .5
  ind=max(0,min(len(options)-1,round(t*(len(options)-1))))
  entries.append(options[ind])
 return entries
recs=[]
for num,name,typ in STAGES:
 for role in ("front","back"):
  sp,src=source_images[(name,role)]
  matching,nblocks=exact2x_fraction(src)
  data={}
  for method,view in (("half",half(src)),("fit",tightfit(src))):
   indices=recolor(view,name)
   pal=stage_palette[name]
   tiledata=tiles(indices)
   preview=render(indices,pal,80)
   assert preview.getchannel("A").tobytes()==view.getchannel("A").tobytes()
   assert len(set(preview.getdata()))<=16
   basename=f"{name}_{role}_{method}_80"
   preview.save(OUT/f"{basename}.png",optimize=True)
   (OUT/f"{basename}_4bpp_tiles.bin").write_bytes(tiledata)
   (OUT/f"{basename}_palette.bin").write_bytes(pal)
   rect=view.getchannel("A").getbbox()
   rec=dict(pokemon=name,role=role,method=method,
      originalCanvas=[160,160],outputCanvas=[80,80],
      sourceFile=str(sp),sourceSHA256=hashlib.sha256(sp.read_bytes()).hexdigest(),
      exact2xBlocks=matching,total2xBlocks=nblocks,
      exact2xPercent=round(matching*100/nblocks,2),
      contentBoundingBox80=list(rect),
      opaquePixels=sum(1 for a in view.getchannel("A").getdata() if a),
      colorsUsed=len(set(indices)-{0}),
      tileBytes=len(tiledata),paletteBytes=len(pal),
      encoding="80x80 indexed DS OBJ 4bpp and 16 entry BGR555",
      tileSHA256=sha(tiledata),paletteSHA256=sha(pal),
      noSourceChanges=True,artApproved=False,romIntegrated=False)
   recs.append(rec)
   data[method]=preview
   print("PLATINUM80_VIEW",json.dumps(rec,sort_keys=True))
# one mobile portrait contact sheet focused on the two previously problematic views.
W=1120;H=920
sheet=Image.new("RGB",(W,H),"#f4f6f7")
d=ImageDraw.Draw(sheet)
d.text((18,14),"MERCURY REDUX / PLATINUM NATIVE 80×80 SPRITE TEST",font=font(23),fill="#253544")
d.text((18,47),"160×160 original Orpheus → native Platinum 80×80, compared with older 64×64 experimental QA",font=font(13),fill="#526474")
d.text((18,68),"Unapproved experiment • no source or historical vote edits • no ROM packaging",font=font(13),fill="#984b47")
for i,(name,role) in enumerate((("flygon","front"),("vibrava","back"))):
 num=next(n for n,s,t in STAGES if s==name)
 orig=source_images[(name,role)][1]
 old64_path=Path("report/ds64_readability")/f"{name}_{role}_contrast64.png"
 old64=Image.open(old64_path).convert("RGBA")
 rows={m:Image.open(OUT/f"{name}_{role}_{m}_80.png").convert("RGBA") for m in ("half","fit")}
 y=101+i*406
 d.rounded_rectangle((10,y,W-10,y+392),radius=12,fill="white",outline="#cbd8df",width=2)
 d.text((22,y+12),name.upper()+f" {role.upper()} • 160→80 vs previous DS64",font=font(17),fill="#253544")
 for x,title,im in [(18,"Original source",orig),(269,"Old 64×64",old64),(518,"80×80 half",rows["half"]),(775,"80×80 fitted",rows["fit"])]:
  d.text((x,y+40),title,font=font(13),fill="#526474")
  panel(sheet,im,x,y+63,230)
 d.text((20,y+306),"Original 2×2 exact blocks: "+str(next(r["exact2xPercent"] for r in recs if r["pokemon"]==name and r["role"]==role))+"%",font=font(13),fill="#486678")
 d.text((20,y+332),"All alternatives: 80×80 pixels / 3200-byte DS4bpp tiles / 32-byte palettes • 64px is not Platinum's native battle canvas",font=font(12),fill="#526474")
 d.text((20,y+355),"80×80 is a technical preview, not a playable ROM resource or user-approved design",font=font(12),fill="#9b5149")
sheet_path=OUT/"orpheus_platinum_native80_vs_ds64.png"
sheet.save(sheet_path,optimize=True)
report={"schema":"mercury-original-orpheus-native80-prototype-v1",
"sourceArchiveSHA256":PIN,
"nativePlatinumBattleSpriteCanvas":[80,80],
"priorExperimentalCanvas":[64,64],
"currentStagePaletteApplied":True,"sourceArtModified":False,"userVotesModified":False,
"ROMModified":False,"approved":False,
"method":"original 160 RGBA -> direct 2x nearest 80 or crop-to-76 80; stage-specific index palette BGR555; full 10x10 DS 4bpp 8x8 tile scan; decoded PNG matches indices",
"limitations":["Whether a given Mercury integration mod uses the game's original 80x80 resource path needs proof from engine archive build and emulator.",
"Stage-specific palette is an experiment and not approved or exact original source colors.",
"No regional shinies, icons, NCGR/NCLR/NARC resources or emulator rendering verified."],
"views":recs}
(OUT/"native80_qa.json").write_text(json.dumps(report,indent=2)+"\n")
print("PLATINUM80_SUMMARY",json.dumps({
"views":len(recs),"exact2x":{r["pokemon"]+"_"+r["role"]:r["exact2xPercent"] for r in recs if r["method"]=="half"},
"sourceUnchanged":True,"approved":False,"romIntegrated":False}))
print("PLATINUM80_PREVIEW_START orpheus_platinum_native80_vs_ds64.png")
print(base64.b64encode(sheet_path.read_bytes()).decode("ascii"))
print("PLATINUM80_PREVIEW_END orpheus_platinum_native80_vs_ds64.png")
