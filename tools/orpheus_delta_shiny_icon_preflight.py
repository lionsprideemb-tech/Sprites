#!/usr/bin/env python3
"""Non-integrating Orpheus custom shiny color proposals and ORIGINAL icon-frame audit.

Runs only in the source-audit workflow after original RAR name-matched icon PNGs
have been extracted to safepng. No original art/votes/ROM files modified.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import hashlib,json,struct,colorsys
S=Path("review/candidates/orpheus-2026-11-09-UNAPPROVED/desert-scarab-sixview-g4-preflight")
SREF=Path("safepng")
OUT=Path("report/orpheus_delta_shiny_icon_preflight")
OUT.mkdir(parents=True,exist_ok=True)
SOURCEPIN="72539b83b55a427c4adcdf2f3e5397cc28371875a720f687ffcf4e2a6d803ef9"
ARCH=Path("orpheus-original-resources.rar")
assert ARCH.is_file() and hashlib.sha256(ARCH.read_bytes()).hexdigest()==SOURCEPIN
def sha(b):return hashlib.sha256(b if isinstance(b,bytes) else b.read_bytes()).hexdigest()
q=json.loads((S/"preflight_qa.json").read_text())
assert q["schema"]=="mercury-orpheus-sixview-pt-battle-source-preflight-v1" and q["allApproved"] is False
assert q["normalViewCount"]==6
BYVIEW={v["view"]:v for v in q["views"]}
# Every evolution stage's SHINY recolor is a new unapproved concept. The normal
# stage silhouettes, indices and scale work remain exactly as already checked.
SHINY_COLORS={
 "trapinch":[
 "#000000","#211E1A","#342D2A","#5C4B40","#826349","#AB8860",
 "#E0BF85","#604A35","#6E6152","#C3A67A","#E9D49E","#6DAFA7",
 "#3A5954","#6DAA94","#B6D8BC","#F6EFE0"],
 "vibrava":[
 "#000000","#271D18","#4B3026","#68402B","#956047","#BC8360",
 "#E0AF73","#F4D5A3","#5B4834","#9C6944","#D39757","#ECC582",
 "#F5DEA1","#F6EDCF","#67A9A0","#C1E4D9"],
 "flygon":[
 "#000000","#211E20","#3C3134","#594147","#80565A","#B57560",
 "#D99A77","#F2C8A0","#534133","#92613C","#C9844C","#E8AF63",
 "#F1D080","#F8EBD0","#55A89A","#B8E4DA"]
}
def to_word(h):
 v=[round(int(h[i:i+2],16)*31/255) for i in (1,3,5)]
 return v[0]|v[1]<<5|v[2]<<10
def rgb(w):return tuple(round(((w>>(5*k))&31)*255/31) for k in range(3))
def unpack(t):
 assert len(t)==3200
 idx=[0]*6400;i=0
 for by in range(0,80,8):
  for bx in range(0,80,8):
   for y in range(8):
    for x in range(0,8,2):
     a=t[i];i+=1
     idx[(by+y)*80+bx+x]=a&15
     idx[(by+y)*80+bx+x+1]=a>>4
 return idx
def pack(idx):
 assert len(idx)==6400
 out=bytearray()
 for by in range(0,80,8):
  for bx in range(0,80,8):
   for y in range(8):
    for x in range(0,8,2):
     a=idx[(by+y)*80+bx+x];b=idx[(by+y)*80+bx+x+1]
     assert 0<=a<16 and 0<=b<16
     out.append(a|(b<<4))
 assert len(out)==3200
 return bytes(out)
def render(idx,colors):
 img=Image.new("RGBA",(80,80))
 img.putdata([(*rgb(colors[z]),255) if z else (0,0,0,0) for z in idx])
 return img
def font(n,bold=False):
 files=("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf") if bold else ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",)
 for f in files:
  if Path(f).exists():return ImageFont.truetype(f,n)
 return ImageFont.load_default()
def paste(img,src,x,y,scale):
 z=src.convert("RGBA").resize((src.width*scale,src.height*scale),Image.Resampling.NEAREST)
 bg=Image.new("RGBA",z.size,"#ECF1F5");bg.alpha_composite(z)
 img.paste(bg.convert("RGB"),(x,y))
rows=[]
views={}
for name,r in BYVIEW.items():
 stage,face=name.split("_")
 words=[to_word(h) for h in SHINY_COLORS[stage]]
 assert len(words)==16 and len(set(words[1:]))==15 and words[0]==0
 sourceImg=S/r["nativeImage"];sourceTile=S/r["tiles"]
 assert sha(sourceImg)==r["imageSHA256"] and sha(sourceTile)==r["tilesSHA256"]
 old=Image.open(sourceImg).convert("RGBA")
 idx=unpack(sourceTile.read_bytes())
 palBytes=struct.pack("<16H",*words)
 shiny=render(idx,words)
 assert old.size==shiny.size==(80,80) and old.getchannel("A").tobytes()==shiny.getchannel("A").tobytes()
 assert pack(unpack(pack(idx)))==sourceTile.read_bytes()
 assert shiny.getchannel("A").tobytes()==old.getchannel("A").tobytes()
 d=OUT/"shinies"/stage
 d.mkdir(parents=True,exist_ok=True)
 png=d/f"{face}_shiny_PROPOSAL_80.png"
 tiles=d/f"{face}_shiny_PROPOSAL_80_4bpp_tiles.bin"
 palette=d/f"{face}_shiny_PROPOSAL_80_palette.bin"
 shiny.save(png,optimize=True);tiles.write_bytes(pack(idx));palette.write_bytes(palBytes)
 assert render(unpack(tiles.read_bytes()),words).tobytes()==Image.open(png).convert("RGBA").tobytes()
 rows.append({"view":name,"normalSHA256":r["imageSHA256"],"shiny":str(png.relative_to(OUT)),
              "tile":str(tiles.relative_to(OUT)),"palette":str(palette.relative_to(OUT)),
              "shinySHA256":sha(png),"tileSHA256":sha(tiles),"paletteSHA256":sha(palette),
              "normalIndicesPreservedExactly":True,"alphaPreserved":True,
              "4bppRoundTrip":True,"userApproved":False})
 views[name]=(old,shiny)
sheet=Image.new("RGB",(880,1680),"#F7F8FA");d=ImageDraw.Draw(sheet)
d.text((20,15),"DESERT SCARAB   /   OPTIONAL SHINY COLOR PROPOSALS",font=font(21,True),fill="#2C3F4E")
d.text((20,48),"UNAPPROVED / palette-only recolors of genuine indexed normal 80px frames",font=font(14),fill="#A54A39")
for i,name in enumerate(("trapinch_front","trapinch_back","vibrava_front","vibrava_back","flygon_front","flygon_back")):
 y=90+i*258
 d.rounded_rectangle((10,y,870,y+243),radius=11,outline="#CBD2D6",fill="#FFFFFF")
 d.text((25,y+9),name.replace("_"," ").upper(),font=font(18,True),fill="#304352")
 d.text((28,y+40),"Normal 80px ×2",font=font(13),fill="#546575")
 d.text((440,y+40),"Shiny proposal 80px ×2",font=font(13),fill="#546575")
 n,s=views[name]
 paste(sheet,n,30,y+67,2)
 paste(sheet,s,443,y+67,2)
d.text((18,1650),"These are COLOR OPTIONS only; final shinies and animation require a separate decision.",font=font(13),fill="#6B5960")
preview=OUT/"six_shiny_vs_normal_unapproved.png"
sheet.save(preview,optimize=True)
# Preserve source icon sprite sheets exactly; inventory 4 columns × 2 rows of
# original 32px cells only. Do not assert which cells are animation states.
icons=[]
for stage,number in (("trapinch",328),("vibrava",329),("flygon",330)):
 icon=SREF/f"icon{number}_1.png"
 assert icon.is_file(),f"Original Orpheus regional icon missing: {icon}"
 original=Image.open(icon).convert("RGBA")
 assert original.size==(128,64),(stage,original.size)
 dest=OUT/"original-icon-source"/stage
 dest.mkdir(parents=True,exist_ok=True)
 original.save(dest/"icon_original_128x64.png",optimize=True)
 summary=[]
 cells=[]
 for i in range(8):
  x=(i%4)*32;y=(i//4)*32
  cell=original.crop((x,y,x+32,y+32))
  file=dest/f"original_cell_{i:02}.png"
  cell.save(file,optimize=True)
  alpha=cell.getchannel("A")
  bbox=alpha.getbbox()
  count=sum(a!=0 for a in alpha.getdata())
  rec={"cell":i,"image":str(file.relative_to(OUT)),
       "sourceRect":[x,y,32,32],"opaquePixels":count,
       "alphaBounds":list(bbox) if bbox else None,"sha256":sha(file)}
  summary.append(rec);cells.append(cell)
 icons.append({"stage":stage,"originalSheet":str((dest/"icon_original_128x64.png").relative_to(OUT)),
               "sourceSHA256":sha(icon),"sourceDimensions":[128,64],
               "exact32x32Cells":summary,
               "chosenGameIconFrame":None,
               "iconAnimationFramesCertified":False,
               "DSIconPaletteCertified":False})
# Original 128x64 atlas source reconstructed exactly from 8 extracted cells.
for icon in icons:
 p=OUT/icon["originalSheet"]
 expected=Image.open(p).convert("RGBA")
 im=Image.new("RGBA",(128,64))
 for e in icon["exact32x32Cells"]:
  x,y,_,_=e["sourceRect"]
  cell=Image.open(OUT/e["image"]).convert("RGBA")
  im.alpha_composite(cell,(x,y))
 assert im.tobytes()==expected.tobytes(),icon["stage"]
icon_sheet=Image.new("RGB",(920,580),"#F7F8FA");draw=ImageDraw.Draw(icon_sheet)
draw.text((20,12),"ORPHEUS ORIGINAL REGIONAL ICON SOURCE FRAME INVENTORY",font=font(19,True),fill="#2B3E4F")
draw.text((20,43),"128x64 source sheet => eight 32x32 exact crops; animation/layout NOT certified",font=font(14),fill="#A64B3B")
for j,r in enumerate(icons):
 y=77+j*162
 draw.rounded_rectangle((14,y,903,y+148),radius=12,fill="white",outline="#CDD7DC")
 draw.text((28,y+6),r["stage"].upper(),font=font(17,True),fill="#344A58")
 for cell in r["exact32x32Cells"]:
  i=cell["cell"]
  x=168+i*85
  src=Image.open(OUT/cell["image"]).convert("RGBA")
  paste(icon_sheet,src,x,y+27,2)
  draw.text((x+5,y+100),f"cell {i}",font=font(11),fill="#657482")
icon_preview=OUT/"orpheus_source_icon_32px_frame_inventory.png"
icon_sheet.save(icon_preview,optimize=True)
report={"schema":"mercury-orpheus-shiny-icon-source-research-v1",
        "archiveSHA256":SOURCEPIN,
        "normalSixViewSHA256":sha(S/"preflight_qa.json"),
        "shinyColorProposals":rows,"proposalPreview":preview.name,
        "originalIconInventory":icons,"iconPreview":icon_preview.name,
        "normalSpriteFilesUntouched":True,"historicalVotesUntouched":True,
        "allUnapproved":True,"noPlatinumIntegration":True,
        "shinyDesignsNotYetApproved":True,"iconSelectionNotYetApproved":True,
        "noNitroIconArchive":True,"noROMEmulatorTest":True}
(OUT/"shiny_icon_research_qa.json").write_text(json.dumps(report,indent=2)+"\n")
(OUT/"README.md").write_text(
 "# Orpheus Delta shiny + icon proof-of-source (UNAPPROVED)\n\n"
 "[Six normal/shiny color **proposals**](six_shiny_vs_normal_unapproved.png) and "
 "[original source icon 32px frame inventory](orpheus_source_icon_32px_frame_inventory.png).\n\n"
 "These are derived from exact source-locked index arrays and Orpheus's public original RAR. "
 "Neither custom shiny color scheme nor icon animation frame grouping is user-approved. "
 "Do not present this folder as a complete game sprite pack. "
 "See [exact QA](shiny_icon_research_qa.json). All source content and votes remain untouched.\n")
print("ORPHEUS_SHINY_ICON_RESEARCH_QA",json.dumps({
    "shinyProposals":len(rows),"originalIconSheets":len(icons),
    "iconFrameCrops":sum(len(x["exact32x32Cells"]) for x in icons),
    "allSourceExact":True,"allUnapproved":True,"romIntegrated":False}))
