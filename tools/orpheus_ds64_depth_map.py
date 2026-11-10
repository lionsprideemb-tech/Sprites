#!/usr/bin/env python3
"""Read-only source-derived indexed pixel diagnostics for two DS64 views."""
from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import struct,json,base64
BASE=Path("review/candidates/orpheus-2026-11-09-UNAPPROVED/microfix-real-pixels")
OUT=Path("report/orpheus-depth")
OUT.mkdir(parents=True,exist_ok=True)
def decode(buf):
 a=[0]*4096;p=0
 for ty in range(0,64,8):
  for tx in range(0,64,8):
   for y in range(8):
    for x in range(0,8,2):
     b=buf[p];p+=1;a[(ty+y)*64+tx+x]=b&15;a[(ty+y)*64+tx+x+1]=b>>4
 return a
def palette(p):
 vals=struct.unpack("<16H",p)
 return {i:tuple(round(255*((v>>(5*c))&31)/31) for c in range(3)) for i,v in enumerate(vals)}
def zoom(im,roi,scale=12):
 x0,y0,x1,y1=roi
 src=im.crop(roi)
 im2=src.resize(((x1-x0)*scale,(y1-y0)*scale),Image.Resampling.NEAREST)
 bg=Image.new("RGBA",im2.size,(244,248,250,255));bg.alpha_composite(im2)
 return bg.convert("RGB")
regions={
 "vibrava_back":[("antennae",(37,3,59,29)),("head_and_wing",(21,20,59,51))],
 "flygon_front":[("head_and_face",(17,4,48,31)),("wing_overlap",(6,17,54,47))]
}
font=ImageFont.load_default()
for name in regions:
 png=Image.open(BASE/f"{name}_manual_microfix64.png").convert("RGBA")
 idx=decode((BASE/f"{name}_4bpp_tiles.bin").read_bytes())
 colors=palette((BASE/f"{name}_bgr555_palette.bin").read_bytes())
 print("DEPTH_PALETTE",json.dumps({"name":name,"colors":colors}))
 for key,(x0,y0,x1,y1) in regions[name]:
  print("DEPTH_MAP_BEGIN",name,key,{"x":x0,"y":y0,"width":x1-x0,"height":y1-y0})
  print("   "+" ".join(f"{x:02d}" for x in range(x0,x1)))
  for y in range(y0,y1):
   print(f"{y:02d} "+" ".join(f"{idx[y*64+x]:02X}" for x in range(x0,x1)))
  print("DEPTH_MAP_END",name,key)
  zz=zoom(png,(x0,y0,x1,y1),10)
  # Show faint coordinate grid and labels
  canvas=Image.new("RGB",(zz.width+68,zz.height+70),"#eef3f5")
  canvas.paste(zz,(56,48))
  d=ImageDraw.Draw(canvas)
  for x in range(x0,x1):
   pos=56+(x-x0)*10
   if x%4==0:
    d.line((pos,46,pos+0,48+zz.height),fill="#A7B7C1",width=1)
    d.text((pos,26),str(x),font=font,fill="#25313b")
  for y in range(y0,y1):
   pos=48+(y-y0)*10
   if y%4==0:
    d.line((54,pos,56+zz.width,pos),fill="#A7B7C1",width=1)
    d.text((12,pos),str(y),font=font,fill="#25313b")
  path=OUT/f"{name}_{key}_indexed_grid.png";canvas.save(path)
  print("DEPTH_IMAGE_START",path.name)
  print(base64.b64encode(path.read_bytes()).decode("ascii"))
  print("DEPTH_IMAGE_END",path.name)
