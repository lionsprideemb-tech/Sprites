#!/usr/bin/env python3
"""Read-only exact-color pixel inspector for the source-color Flygon 80px candidate."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import hashlib,struct
P=Path("review/candidates/orpheus-2026-11-09-UNAPPROVED/native80-original-colors")
O=Path("report/orpheus_native80_face_grid")
O.mkdir(parents=True,exist_ok=True)
src=P/"flygon_front_source_colors80.png"
tiles=P/"flygon_front_source_colors80_4bpp_tiles.bin"
pal=P/"flygon_front_source_colors80_palette.bin"
assert hashlib.sha256(src.read_bytes()).hexdigest()=="9c140719fd0d39b79d80104962232636c7ca678717bc84ab062879f4ec725c0e"
assert hashlib.sha256(tiles.read_bytes()).hexdigest()=="b36eb9ed804a680d8fed875b0b2c39884ad07cbd4361eac0b760d27e8cff127d"
assert hashlib.sha256(pal.read_bytes()).hexdigest()=="3fbde56011adf0299653199cea2d93b948c6295e54494cabeac7542b2f3423d7"
im=Image.open(src).convert("RGBA")
assert im.size==(80,80)
words=struct.unpack("<16H",pal.read_bytes())
def rgb(word):return tuple(round(((word>>(5*i))&31)*255/31) for i in range(3))
index=[0]*6400
data=tiles.read_bytes();j=0
for by in range(0,80,8):
 for bx in range(0,80,8):
  for dy in range(8):
   for dx in range(0,8,2):
    b=data[j];j+=1
    index[(by+dy)*80+bx+dx]=b&15
    index[(by+dy)*80+bx+dx+1]=b>>4
assert len(data)==3200 and j==3200
assert im.tobytes()==bytes(z for p in index for z in ((*rgb(words[p]),255) if p else (0,0,0,0)))
def font(size):
 for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
  if Path(p).exists():return ImageFont.truetype(p,size)
 return ImageFont.load_default()
def grid(x0,y0,x1,y1,label,cell):
 nw=x1-x0+1;nh=y1-y0+1
 marginx=48;marginy=70
 sheet=Image.new("RGB",(nw*cell+marginx+15,nh*cell+marginy+50),"#f5f7f9")
 d=ImageDraw.Draw(sheet)
 d.text((15,12),label,font=font(17),fill="#213344")
 for x in range(x0,x1+1):
  dx=marginx+(x-x0)*cell
  d.text((dx+2,45),str(x),font=font(11),fill="#31536b")
 for y in range(y0,y1+1):
  dy=marginy+(y-y0)*cell
  d.text((9,dy+3),str(y),font=font(11),fill="#31536b")
  for x in range(x0,x1+1):
   dx=marginx+(x-x0)*cell
   k=index[y*80+x]
   color=rgb(words[k]) if k else (231,240,243)
   d.rectangle((dx,dy,dx+cell-1,dy+cell-1),fill=color,outline="#bac6c8",width=1)
   if k:
    lum=(color[0]*.2126+color[1]*.7152+color[2]*.0722)
    fg="#ffffff" if lum<125 else "#222222"
    d.text((dx+cell//3,dy+3),f"{k:X}",font=font(11),fill=fg)
 return sheet
grid(22,8,56,45,"Flygon FRONT x22-56, y8-45 (indexed DS80)",23).save(O/"flygon_native80_grid_head_wing.png")
grid(25,16,48,38,"Flygon FRONT close-up face and body junction",32).save(O/"flygon_native80_grid_face_detail.png")
Image.open(src).resize((640,640),Image.Resampling.NEAREST).save(O/"flygon_native80_8x.png")
(O/"README.md").write_text("# Native 80px Flygon face indexed inspection (read only)\n\n"
 "This grid decodes the committed 3,200-byte DS 4bpp tile data, without editing it. "
 "Columns and rows show exact 0-based pixel coordinates. Palette digits in cells "
 "are exact 4bpp color indices; transparent cells are unlabeled.\n\n"
 "Nothing was approved or integrated.\n")
print("GRID_INSPECTION_PASSED baseline exact, alpha exact, palette exact")
