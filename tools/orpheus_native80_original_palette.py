#!/usr/bin/env python3
"""Original-color Orpheus native 80px recovery: isolated, unapproved, no ROM edits.

Convert the original 160px sprite, not the experimental brown/blue recolors.
Select 15 source-derived BGR555 colors per view with protected hue groups.
Pixels and 80px silhouette are source-locked; the palette is a candidate.
"""
from collections import Counter
from pathlib import Path
import colorsys
import hashlib
import json
import math
import struct
from PIL import Image, ImageDraw, ImageFont

SOURCE = Path("safepng")
PREVIOUS = Path("report/orpheus_native_platinum80")
OUT = Path("report/orpheus_native80_original_colors")
OUT.mkdir(parents=True, exist_ok=True)
PIN = "72539b83b55a427c4adcdf2f3e5397cc28371875a720f687ffcf4e2a6d803ef9"
ARCHIVE = Path("orpheus-original-resources.rar")
assert ARCHIVE.is_file() and hashlib.sha256(ARCHIVE.read_bytes()).hexdigest() == PIN
assert SOURCE.is_dir() and PREVIOUS.is_dir()

def sha(b):
    return hashlib.sha256(b).hexdigest()

def to_word(c):
    r, g, b = [round(v*31/255) for v in c]
    return r | (g<<5) | (b<<10)

def to_rgb(w):
    return tuple(round(255*((w>>(5*j)) & 31)/31) for j in range(3))

def category(c):
    r,g,b = c
    h,s,v = colorsys.rgb_to_hsv(r/255,g/255,b/255)
    if max(c) < 72 or s < .12:
        return "neutral"
    if .075 <= h < .18:
        return "yellow"
    if .18 <= h < .49:
        return "green"
    if .49 <= h < .78:
        return "blue"
    return "red-purple"

def distance(a,b):
    aa,bb=to_rgb(a),to_rgb(b)
    delta = sum((x-y)**2 for x,y in zip(aa,bb))
    ca,cb=category(aa),category(bb)
    # Protect tiny eye/antenna highlights from merging into the body.
    if ca != cb and "neutral" not in (ca,cb):
        delta += 23000
    return delta

def choose_colors(count):
    words=list(count)
    assert words and len(words)<=256
    if len(words)<=15:
        return sorted(words, key=lambda w:(-count[w],w))
    buckets={}
    for w in words:
        buckets.setdefault(category(to_rgb(w)), []).append(w)
    fixed=[]
    # Preserve dark outline and one prominent tone in every source hue family.
    darkest=min(words,key=lambda w:(sum(to_rgb(w)),w))
    fixed.append(darkest)
    for tag in ("green","yellow","blue","red-purple"):
        if tag in buckets:
            w=max(buckets[tag],key=lambda k:(count[k],-k))
            if w not in fixed:fixed.append(w)
    selected=fixed[:]
    weights={w:1+math.sqrt(count[w]) for w in words}
    def loss(chosen):
        return sum(weights[w]*min(distance(w,q) for q in chosen) for w in words)
    while len(selected)<min(15,len(words)):
        best=min((w for w in words if w not in selected),
                 key=lambda w:(loss(selected+[w]),-count[w],w))
        selected.append(best)
    # Refinement optimizes source fidelity without sacrificing protected hues.
    for _ in range(2):
        improved=False
        initial=loss(selected)
        for i in range(len(fixed),len(selected)):
            local=None
            best_cost=initial
            for word in words:
                if word in selected:continue
                candidate=selected[:];candidate[i]=word
                cost=loss(candidate)
                if cost+1e-8<best_cost:
                    local=word;best_cost=cost
            if local is not None:
                selected[i]=local;initial=best_cost;improved=True
        if not improved:break
    assert len(set(selected))==len(selected) and len(selected)<=15
    return selected

def pack(indices):
    assert len(indices)==6400 and all(0<=k<16 for k in indices)
    data=bytearray()
    for by in range(0,80,8):
        for bx in range(0,80,8):
            for dy in range(8):
                for dx in range(0,8,2):
                    y=by+dy
                    a=indices[y*80+bx+dx]
                    b=indices[y*80+bx+dx+1]
                    data.append(a|(b<<4))
    assert len(data)==3200
    return bytes(data)

def unpack(data):
    assert len(data)==3200
    output=[0]*6400; k=0
    for by in range(0,80,8):
        for bx in range(0,80,8):
            for dy in range(8):
                for dx in range(0,8,2):
                    y=by+dy
                    byte=data[k];k+=1
                    output[y*80+bx+dx]=byte&15
                    output[y*80+bx+dx+1]=byte>>4
    return output

def image(indices,palette):
    out=Image.new("RGBA",(80,80))
    out.putdata([(*to_rgb(palette[k]),255) if k else (0,0,0,0) for k in indices])
    return out

def panel(sheet, im, x, y, sz, scale="zoom"):
    bg=Image.new("RGBA",(sz,sz),"#edf3f6")
    # Distinguish actual native canvas from integer-zoom pixel detail.
    if scale=="native":
        rendered=im.convert("RGBA")
    else:
        rendered=im.convert("RGBA").resize((im.width*3,im.height*3),Image.Resampling.NEAREST)
    assert rendered.width<=sz and rendered.height<=sz
    bg.alpha_composite(rendered,((sz-rendered.width)//2,(sz-rendered.height)//2))
    sheet.paste(bg.convert("RGB"),(x,y))

def font(size):
    for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
              "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"):
        if Path(f).exists():
            return ImageFont.truetype(f,size)
    return ImageFont.load_default()

views=[]
comparisons=[]
for name,kind,number in (("flygon","front",330),("vibrava","back",329)):
    orig_path=SOURCE/f"{number}{'b' if kind=='back' else ''}_1.png"
    orig=Image.open(orig_path).convert("RGBA")
    assert orig.size==(160,160)
    assert {p[3] for p in orig.getdata()} <= {0,255}
    half=orig.resize((80,80),Image.Resampling.NEAREST)
    before=Image.open(PREVIOUS/f"{name}_{kind}_half_80.png").convert("RGBA")
    assert before.size==(80,80) and before.getchannel("A").tobytes()==half.getchannel("A").tobytes()
    colors=Counter(to_word(px[:3]) for px in half.getdata() if px[3])
    keep=choose_colors(colors)
    palette=[0]+keep+[0]*(15-len(keep))
    assert len(palette)==16
    indexed=[0 if not px[3] else
             1+min(range(len(keep)),key=lambda j:(distance(to_word(px[:3]),keep[j]),j))
             for px in half.getdata()]
    tiles=pack(indexed)
    assert indexed==unpack(tiles)
    palette_bytes=struct.pack("<16H",*palette)
    assert len(palette_bytes)==32
    corrected=image(indexed,palette)
    assert corrected.getchannel("A").tobytes()==half.getchannel("A").tobytes()
    assert corrected.tobytes()==image(unpack(tiles),list(struct.unpack("<16H",palette_bytes))).tobytes()
    assert len(set(corrected.getdata()))<=16
    label=f"{name}_{kind}_source_colors80"
    png_path=OUT/f"{label}.png"
    tile_path=OUT/f"{label}_4bpp_tiles.bin"
    pal_path=OUT/f"{label}_palette.bin"
    corrected.save(png_path,optimize=True)
    tile_path.write_bytes(tiles)
    pal_path.write_bytes(palette_bytes)
    correct_pixels=sum(1 for a,b in zip(half.getdata(),corrected.getdata())
                       if a[3] and to_word(a[:3])==to_word(b[:3]))
    count_opaque=sum(px[3]!=0 for px in half.getdata())
    changed_vs_previous=sum(1 for a,b in zip(before.getdata(),corrected.getdata())
                            if a[3] and a[:3]!=b[:3])
    rec={"view":name+"_"+kind,"source":str(orig_path),
         "sourceSHA256":sha(orig_path.read_bytes()),
         "priorPaletteExperiment":"stage-specific unapproved brown/blue family recolor",
         "nativeCanvas":[80,80],
         "sourcePixel2xPreserved":name=="flygon",
         "sourcePaletteOpaqueColors":len(colors),
         "sourceDerivedBGR555PaletteEntries":len(keep),
         "sourceColorBGR555ExactPixels":correct_pixels,
         "opaquePixels":count_opaque,
         "changedColorsComparedToPriorNative80":changed_vs_previous,
         "originalAlphaExact":True,"sourceSilhouetteExact":True,
         "noManualSourcePixelEdits":True,
         "tileDecodePixelExact":True,
         "png":png_path.name,"tiles":tile_path.name,"palette":pal_path.name,
         "pngSHA256":sha(png_path.read_bytes()),
         "tilesSHA256":sha(tiles),"paletteSHA256":sha(palette_bytes),
         "tileBytes":3200,"paletteBytes":32,"approved":False,"integrated":False}
    views.append(rec)
    comparisons.append((name,kind,orig,before,corrected))

sheet=Image.new("RGB",(1120,940),"#f3f6f8")
draw=ImageDraw.Draw(sheet)
draw.text((20,14),"MERCURY REDUX  |  ORPHEUS ORIGINAL-COLOR RECOVERY",font=font(23),fill="#243748")
draw.text((20,47),"Two source-faithful native Platinum 80px candidates; UNAPPROVED / NOT IN ROM",font=font(15),fill="#a3423a")
for i,(name,kind,orig,before,corrected) in enumerate(comparisons):
    y=89+i*420
    draw.rounded_rectangle((10,y,1110,y+400),radius=12,fill="white",outline="#c2cbd3",width=2)
    draw.text((24,y+12),f"{name.upper()} {kind.upper()}",font=font(19),fill="#20394d")
    for x,heading,im in ((24,"Original 160px",orig),
                         (291,"Previous recolor 80px",before),
                         (558,"Source colors 80px",corrected),
                         (825,"Source colors at 3x",corrected)):
        draw.text((x,y+47),heading,font=font(14),fill="#3c596c")
        panel(sheet,im,x,y+77,244,
              scale="native" if heading in ("Original 160px","Source colors 80px") else "zoom")
    rec=views[i]
    draw.text((24,y+341),
              f"Alpha preserved; 15 opaque colors max; {rec['changedColorsComparedToPriorNative80']} source pixels recolored vs prior.",
              font=font(14),fill="#435e6f")
    draw.text((24,y+366),"DS OBJ 4bpp tiles: 3,200 bytes  |  Palette: 32 bytes  |  Pixel-exact tile decode",
              font=font(13),fill="#435e6f")
comparison=OUT/"orpheus_native80_original_colors_before_after.png"
sheet.save(comparison,optimize=True)
qa={"schema":"mercury-orpheus-original-color-native80-v1",
    "sourceArchiveSHA256":PIN,
    "method":"original full canvas 160px nearest 2x to native 80px; 15 BGR555 colors selected from source; transparency and layout locked",
    "colorSelection":"weighted source color medoids, preserve dark outline and available green/yellow/blue/red accent hue families",
    "noSourceArtModified":True,"noPreviousCandidateModified":True,
    "noVotesModified":True,"allUnapproved":True,"noROMIntegration":True,
    "limitations":["Palette reduction to 15 colors remains a reviewed approximation of full original 24/34-color artwork.",
                   "Vibrava BACK has nonuniform original 2x blocks, including alpha, so nearest half sampling is not fully lossless.",
                   "No subjective readability approval, no manual anatomy edit, no shiny/icon, no battle-engine archive or emulator test."],
    "comparison":comparison.name,"views":views}
(OUT/"original_colors_qa.json").write_text(json.dumps(qa,indent=2)+"\n")
(OUT/"README.md").write_text(
    "# Orpheus original-color native 80x80 candidates (UNAPPROVED)\n\n"
    "Restores the original source's green/yellow character rather than the experimental brown/teal palette. "
    "Two views only: Flygon FRONT and Vibrava BACK. The 80x80 source-derived geometry and alpha are unchanged. "
    "No older assets or approvals were overwritten.\n\n"
    "[Compare original / prior recolor / source-color candidate](orpheus_native80_original_colors_before_after.png)\n\n"
    "These are genuine 80x80 BGR555/4bpp **candidates**, not ROM-ready NARC assets. "
    "See [exact QA](original_colors_qa.json). They still require human readability review, "
    "and palette reduction must not be mistaken for exact source-color identity. "
    "Historical KEEP/CUT votes and Platinum integration remain untouched.\n")
print("ORPHEUS_ORIGINAL_COLOR_RECOVERY_QA",json.dumps({
    "twoViews":len(views),"allUnapproved":True,"romIntegrated":False,
    "alphaExact":all(v["originalAlphaExact"] for v in views),
    "roundTrips":all(v["tileDecodePixelExact"] for v in views),
    "changedFromRecolor":[[v["view"],v["changedColorsComparedToPriorNative80"]] for v in views]
}))
