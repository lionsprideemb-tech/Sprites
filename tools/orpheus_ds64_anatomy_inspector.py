#!/usr/bin/env python3
"""Read-only small pixel indexed map for strictly local 64px geometry editing."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from collections import Counter
import json,struct,base64
SRC=Path("report/ds64_manual_microfix")
OUT=Path("report/ds64_anatomy_inspection")
OUT.mkdir(parents=True,exist_ok=True)
REGIONS={
  "vibrava_back":{"antenna":(34,4,57,26),"eye":(37,19,61,42),"wing_root":(25,28,59,50)},
  "flygon_front":{"face":(17,9,38,36),"face_wing":(10,20,50,46),"right_wing":(30,8,62,38)}
}
def arr(buf):
 out=[0]*4096;k=0
 for ty in range(0,64,8):
  for tx in range(0,64,8):
   for dy in range(8):
    for dx in range(0,8,2):
     b=buf[k];k+=1
     out[(ty+dy)*64+tx+dx]=b&15
     out[(ty+dy)*64+tx+dx+1]=b>>4
 return out
fonts=[Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf")]
fp=next((p for p in fonts if p.exists()),None)
font=ImageFont.truetype(str(fp),13) if fp else ImageFont.load_default()
fontsmall=ImageFont.truetype(str(fp),9) if fp else ImageFont.load_default()
meta=[]
panels=[]
for name,parts in REGIONS.items():
 image=Image.open(SRC/f"{name}_manual_microfix64.png").convert("RGBA")
 idx=arr((SRC/f"{name}_4bpp_tiles.bin").read_bytes())
 words=struct.unpack("<16H",(SRC/f"{name}_bgr555_palette.bin").read_bytes())
 used=sorted(set(idx))
 rgb={i:tuple(round(255*((words[i]>>(5*k))&31)/31) for k in range(3)) for i in used}
 print("INDEX_PALETTE",json.dumps({"name":name,"colors":{str(i):rgb[i] for i in used}}))
 for label,rect in parts.items():
  x0,y0,x1,y1=rect
  print(f"ROI_GRID {name} {label} x={x0}-{x1-1} y={y0}-{y1-1}")
  print("   "+ "".join(f"{x%16:X}" for x in range(x0,x1)))
  for y in range(y0,y1):
   vals="".join(f"{idx[y*64+x]:X}" for x in range(x0,x1))
   print(f"{y:02d} {vals}")
  # Pixel-perfect labeled region at 10x, dark graph for human review only
  cropped=image.crop(rect)
  scale=12
  bg=Image.new("RGBA",cropped.size,(235,240,245,255))
  bg.alpha_composite(cropped)
  zoom=bg.convert("RGB").resize((cropped.width*scale,cropped.height*scale),Image.Resampling.NEAREST)
  w=zoom.width+74;h=zoom.height+64
  card=Image.new("RGB",(w,h),"#fafafa");d=ImageDraw.Draw(card)
  d.text((7,8),f"{name}: {label} | x{x0}..{x1-1}, y{y0}..{y1-1}",font=font,fill="#2c3440")
  card.paste(zoom,(55,42))
  for xx in range(x0,x1):
   if xx%4==0:
    X=55+(xx-x0)*scale
    d.line((X,41,X,42+zoom.height),fill="#c4d0d8")
    d.text((X,26),str(xx),font=fontsmall,fill="#3e454c")
  for yy in range(y0,y1):
   if yy%4==0:
    Y=42+(yy-y0)*scale
    d.line((54,Y,55+zoom.width,Y),fill="#c4d0d8")
    d.text((6,Y),str(yy),font=fontsmall,fill="#3e454c")
  panels.append((name,label,card))
  meta.append(dict(name=name,region=label,coords=rect,sourceWidth=64,sourceHeight=64))
# Wide overview for two sprites, four panels with valid actual pixel source data
cols=2
cellw=max(p[2].width for p in panels)+20
cellh=max(p[2].height for p in panels)+20
overview=Image.new("RGB",(cellw*cols,cellh*3),"#edf1f5")
for i,(name,label,card) in enumerate(panels):
 x=(i%cols)*cellw+10;y=(i//cols)*cellh+10
 overview.paste(card,(x,y))
fp=OUT/"source64_regions_pixelmap.png"
overview.save(fp,optimize=True)
(OUT/"pixelmap_metadata.json").write_text(json.dumps(meta,indent=2)+"\n")
print("PIXELMAP_IMAGE_START")
print(base64.b64encode(fp.read_bytes()).decode("ascii"))
print("PIXELMAP_IMAGE_END")
