#!/usr/bin/env python3
"""Surgical Flygon FRONT 80px source-color 4bpp polish. Unapproved and isolated."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import hashlib,json,struct
P=Path("review/candidates/orpheus-2026-11-09-UNAPPROVED/native80-original-colors")
OUT=Path("report/orpheus_native80_final_polish")
OUT.mkdir(parents=True,exist_ok=True)
BASE="flygon_front_source_colors80"
PIN={"png":"9c140719fd0d39b79d80104962232636c7ca678717bc84ab062879f4ec725c0e",
     "tiles":"b36eb9ed804a680d8fed875b0b2c39884ad07cbd4361eac0b760d27e8cff127d",
     "palette":"3fbde56011adf0299653199cea2d93b948c6295e54494cabeac7542b2f3423d7",
     "vibrava_png":"670b7ada44953a294b796835833299ad27a537374d49d69dda16dc9c7da7b65f",
     "vibrava_tiles":"4111767be24ad2bda36141b8226c6323ca7a3c738190532e337857d3d40bb134",
     "vibrava_palette":"53dd238265d8909a3db69ee9cb3224eaf8261ac5b3b881f8d3afbbeb6f56c209"}
def sha(b):return hashlib.sha256(b).hexdigest()
p0=P/f"{BASE}.png";t0=P/f"{BASE}_4bpp_tiles.bin";c0=P/f"{BASE}_palette.bin"
assert sha(p0.read_bytes())==PIN["png"]
assert sha(t0.read_bytes())==PIN["tiles"]
assert sha(c0.read_bytes())==PIN["palette"]
vbase="vibrava_back_source_colors80"
for item,ext,tag in (("png",".png","vibrava_png"),
                     ("tiles","_4bpp_tiles.bin","vibrava_tiles"),
                     ("palette","_palette.bin","vibrava_palette")):
    assert sha((P/f"{vbase}{ext}").read_bytes())==PIN[tag]
palette=c0.read_bytes();words=struct.unpack("<16H",palette)
def col(word):
    return tuple(round(((word>>(5*i))&31)*255/31) for i in range(3))
def unpack(data):
    assert len(data)==3200
    arr=[0]*6400;k=0
    for by in range(0,80,8):
        for bx in range(0,80,8):
            for y in range(8):
                for x in range(0,8,2):
                    b=data[k];k+=1
                    arr[(by+y)*80+bx+x]=b&15
                    arr[(by+y)*80+bx+x+1]=b>>4
    return arr
def pack(arr):
    assert len(arr)==6400
    b=bytearray()
    for by in range(0,80,8):
        for bx in range(0,80,8):
            for y in range(8):
                for x in range(0,8,2):
                    a=arr[(by+y)*80+bx+x];c=arr[(by+y)*80+bx+x+1]
                    assert 0<=a<16 and 0<=c<16
                    b.append(a|(c<<4))
    assert len(b)==3200
    return bytes(b)
def render(arr):
    im=Image.new("RGBA",(80,80))
    im.putdata([(*col(words[k]),255) if k else (0,0,0,0) for k in arr])
    return im
before_index=unpack(t0.read_bytes())
before=Image.open(p0).convert("RGBA")
assert render(before_index).tobytes()==before.tobytes()
# Expected source-index values are pinned per coordinate. Every edit is opaque -> opaque.
# The tiny white 2x2 eye is reshaped with one distinct pupil and a softer lower glint.
# Dark olive under the muzzle separates two light jaw pixels from the cheek.
# Forewing intersection shade keeps the pale joint distinct from the yellow wing.
EDITS=[
    ("eye glint",37,21,7,9),
    ("eye pupil",38,21,7,1),
    ("muzzle contour",33,27,13,6),
    ("muzzle contour",33,28,13,6),
    ("forewing junction",42,34,9,4),
    ("forewing junction",42,35,7,9),
]
after_idx=before_index[:]
for label,x,y,old,new in EDITS:
    assert old!=0 and new!=0 and old!=new
    assert before_index[y*80+x]==old,(label,x,y,before_index[y*80+x],old)
    after_idx[y*80+x]=new
changed=[(i%80,i//80) for i,(a,b) in enumerate(zip(before_index,after_idx)) if a!=b]
assert set(changed)=={(x,y) for _,x,y,_,_ in EDITS}
assert len(changed)==6
after=render(after_idx)
assert before.getchannel("A").tobytes()==after.getchannel("A").tobytes()
assert before.getchannel("A").getbbox()==after.getchannel("A").getbbox()
tileout=pack(after_idx);assert unpack(tileout)==after_idx
assert render(unpack(tileout)).tobytes()==after.tobytes()
assert len(set(after_idx))<=16
pngout=OUT/"flygon_front_original_colors80_final_micro_polish.png"
tilepath=OUT/"flygon_front_original_colors80_final_micro_polish_4bpp_tiles.bin"
palpath=OUT/"flygon_front_original_colors80_final_micro_polish_palette.bin"
after.save(pngout,optimize=True);tilepath.write_bytes(tileout);palpath.write_bytes(palette)
assert palpath.read_bytes()==c0.read_bytes()
def font(n):
 for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf","/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"):
  if Path(p).exists():return ImageFont.truetype(p,n)
 return ImageFont.load_default()
def block(sheet,im,x,y,w,scale):
 bg=Image.new("RGBA",(w,w),"#ecf1f5")
 z=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST)
 assert z.width<=w and z.height<=w
 bg.alpha_composite(z,((w-z.width)//2,(w-z.height)//2))
 sheet.paste(bg.convert("RGB"),(x,y))
sheet=Image.new("RGB",(1160,830),"#f5f7f9")
d=ImageDraw.Draw(sheet)
d.text((23,13),"Mercury Redux  |  Flygon FRONT 80px FINAL LOCAL PIXEL STUDY",font=font(21),fill="#243746")
d.text((23,43),"Only 6 pixels changed • same 80×80 silhouette, 15-color palette, and 4bpp tiling",font=font(15),fill="#495b68")
d.text((23,67),"UNAPPROVED • Vibrava BACK untouched • No Platinum integration",font=font(14),fill="#a34637")
for x,label,im in ((25,"Before (source colors)",before),(600,"After (6 index edits)",after)):
 d.text((x,101),label,font=font(20),fill="#213548")
 block(sheet,im,x,139,520,6)
 d.text((x+5,669),"True native sprite: 80×80",font=font(13),fill="#3e5668")
 block(sheet,im,x+225,657,104,1)
d.text((23,785),"Eye: 2 pixels  |  Muzzle: 2 pixels  |  Forewing junction: 2 pixels",font=font(15),fill="#41596b")
full=OUT/"flygon_native80_final_polish_before_after.png"
sheet.save(full,optimize=True)
# enlarged close-up of exact regions, not anti-aliased, no geometry alterations
mini=Image.new("RGB",(1080,420),"#f5f7f9");dd=ImageDraw.Draw(mini)
dd.text((18,10),"Flygon FRONT: source-index anatomy clarity • before / after",font=font(18),fill="#233747")
regions=[("Eye", (31,16,43,27)),("Muzzle",(27,25,39,36)),("Forewing",(36,30,48,41))]
for i,(label,rect) in enumerate(regions):
 x=16+i*358
 dd.text((x,42),label,font=font(16),fill="#283e50")
 for j,(tag,im) in enumerate((("before",before),("after",after))):
  crop=im.crop(rect).resize((156,156),Image.Resampling.NEAREST)
  bg=Image.new("RGBA",(156,156),"#ecf1f5");bg.alpha_composite(crop)
  mini.paste(bg.convert("RGB"),(x+j*167,88))
  dd.text((x+j*167,67),tag,font=font(12),fill="#526475")
 dd.text((x,270),f"{len([1 for _,xx,yy,_,_ in EDITS if rect[0]<=xx<rect[2] and rect[1]<=yy<rect[3]])} indexed pixel edits",font=font(12),fill="#526475")
mini.save(OUT/"flygon_native80_face_regions_before_after.png",optimize=True)
result={
 "schema":"mercury-orpheus-native80-final-local-indexed-pixel-study-v1",
 "baselineFrom":"review/candidates/orpheus-2026-11-09-UNAPPROVED/native80-original-colors/",
 "source":BASE,
 "baselinePINs":PIN,
 "canvas":[80,80],"pixelEdits":[{"region":tag,"x":x,"y":y,"fromIndex":old,"toIndex":new} for tag,x,y,old,new in EDITS],
 "changedPixelCount":len(changed),"changedOpaquePixelCount":len(changed),
 "transparentToOpaque":0,"opaqueToTransparent":0,"allEditsInsideOriginalSilhouette":True,
 "samePaletteBytes":True,"samePaletteSHA256":sha(palette),
 "sameVibravaBackFiles":True,
 "tilesByteCount":len(tileout),"paletteByteCount":len(palette),
 "tileDecodeExactlyMatchesOutputPNG":True,
 "beforeSourceColorsPNGsha256":PIN["png"],
 "afterPNGsha256":sha(pngout.read_bytes()),
 "afterTileSHA256":sha(tileout),
 "noHistoricalVotesEdited":True,"allUnapproved":True,"noROMIntegration":True,
 "notCertifiedInGame":True,
 "note":"Six subjective clarity adjustments to pixel indices; requires visual review before selecting candidate."
}
(OUT/"qa_exact_native80_final_pixel_polish.json").write_text(json.dumps(result,indent=2)+"\n")
(OUT/"README.md").write_text("# Source-true Flygon native80 manual readability study (UNAPPROVED)\n\n"
 "[Full before/after](flygon_native80_final_polish_before_after.png) · "
 "[Eye / muzzle / forewing close-ups](flygon_native80_face_regions_before_after.png) · "
 "[Exact indexed 4bpp QA](qa_exact_native80_final_pixel_polish.json).\n\n"
 "Only six verified nontransparent pixels in **Flygon FRONT** were edited; eye (2), muzzle (2), forewing joint (2). "
 "Original 80px silhouette, source-color 16-entry BGR555 palette, front/back source files and Vibrava BACK are untouched. "
 "The candidate is not approved, integrated, sprite archive-ready or emulator-tested. "
 "Historical KEEP/CUT votes untouched.\n")
print("FLYGON_NATIVE80_4BPP_EXACT_QA",json.dumps({"edits":len(changed),"decodedMatchesPNG":True,
  "samePaletteBytes":True,"sameSilhouette":True,"vibravaUnchanged":True,
  "approved":False,"romIntegrated":False,"files":[pngout.name,tilepath.name,palpath.name]}))
