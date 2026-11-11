#!/usr/bin/env python3
"""Unapproved Delta Desert Scarab party icons -> real Platinum shared icon palette.

PRECONDITION: upstream pret/pokeplatinum checkout + built NitroGFX binary.
Not a ROM patch or user artwork approval. Compare each of 3 available populated
palette banks; preserve existing shared palette exactly and use the real icon
asset encoder (-clobbersize -version101) and pixel-index readback.
"""
from __future__ import annotations
import argparse, hashlib, json, math, struct, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT=Path("report/orpheus_delta_native80_preflight")
SOURCE=Path("review/candidates/orpheus-2026-11-09-UNAPPROVED/delta-icon32-candidates")
OUT=ROOT/"shared-icon-palette"
OUT.mkdir(parents=True,exist_ok=True)
PARSER=argparse.ArgumentParser()
PARSER.add_argument("--upstream",required=True,type=Path)
PARSER.add_argument("--nitrogfx",required=True,type=Path)
ARGS=PARSER.parse_args()
SHARED=ARGS.upstream/"res/pokemon/.shared/pl_poke_icon.pal"
BUILDSCRIPT=ARGS.upstream/"tools/scripts/make_pl_poke_icon.py"
assert SHARED.is_file() and BUILDSCRIPT.is_file()
source_script=BUILDSCRIPT.read_text()
assert '"-clobbersize"' in source_script and '"-version101"' in source_script
assert "shared_pals.NCLR" in source_script and '"-bitdepth", "4"' in source_script
assert ARGS.nitrogfx.is_file()
def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
def run(*args):
    p=subprocess.run([str(x) for x in args],text=True,capture_output=True,timeout=80)
    if p.returncode:raise RuntimeError(f"{args}\n{p.stdout[-1700:]}\n{p.stderr[-2000:]}")
    return p
raw=SHARED.read_bytes()
# Parse without rewriting or reordering the shared palette.
lines=raw.decode("ascii").splitlines()
assert lines[0]=="JASC-PAL" and lines[1]=="0100" and lines[2]=="256"
assert len(lines[3:])==256
ALLCOLORS=[tuple(map(int,l.split())) for l in lines[3:]]
assert all(len(c)==3 and all(0<=v<=255 for v in c) for c in ALLCOLORS)
# Only three 16-color banks are populated. Entries 48..255 are reserve zeros.
assert all(c==(0,0,0) for c in ALLCOLORS[48:])
BANKS=[ALLCOLORS[i*16:(i+1)*16] for i in range(3)]
assert all(any(any(n for n in c) for c in bank) for bank in BANKS)
NCLR=OUT/"unaltered_upstream_shared_poke_icon_palette.NCLR"
run(ARGS.nitrogfx,SHARED,NCLR,"-bitdepth","4")
assert NCLR.read_bytes()[:4]==b"RLCN",NCLR.read_bytes()[:8]
def lab(c):
    """Standard sRGB -> CIE Lab D65 to compare choices perceptually."""
    def lin(x):
        f=x/255.
        return f/12.92 if f<=.04045 else ((f+.055)/1.055)**2.4
    r,g,b=map(lin,c)
    X=(.4124564*r+.3575761*g+.1804375*b)/.95047
    Y=(.2126729*r+.7151522*g+.0721750*b)
    Z=(.0193339*r+.1191920*g+.9503041*b)/1.08883
    def f(t):return t**(1/3) if t>(6/29)**3 else t/(3*(6/29)**2)+4/29
    x,y,z=map(f,(X,Y,Z))
    return (116*y-16,500*(x-y),200*(y-z))
def de(a,b):
    return math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))
BANK_LAB=[[lab(v) for v in colors] for colors in BANKS]
def pack(idx,w=32,h=64):
    assert len(idx)==w*h and w%8==h%8==0
    out=bytearray()
    for by in range(0,h,8):
        for bx in range(0,w,8):
            for y in range(8):
                for x in range(0,8,2):
                    k=(by+y)*w+bx+x
                    assert 0<=idx[k]<16 and 0<=idx[k+1]<16
                    out.append(idx[k]|idx[k+1]<<4)
    assert len(out)==w*h//2
    return bytes(out)
def unpack(raw,w=32,h=64):
    assert len(raw)==w*h//2
    vals=[0]*(w*h);k=0
    for by in range(0,h,8):
        for bx in range(0,w,8):
            for y in range(8):
                for x in range(0,8,2):
                    p=raw[k];k+=1
                    idx=(by+y)*w+bx+x
                    vals[idx]=p&15;vals[idx+1]=p>>4
    return vals
def font(n,bold=False):
    choices=("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf") if bold else ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",)
    for p in choices:
        if Path(p).exists():return ImageFont.truetype(p,n)
    return ImageFont.load_default()
def render_indices(idx,bank):
    im=Image.new("RGBA",(32,64))
    im.putdata([(0,0,0,0) if k==0 else (*BANKS[bank][k],255) for k in idx])
    return im
def display_frames(sheet,im,x,y):
    # 32x64 stacked source holds two 32px frames.
    for frame in range(2):
        cut=im.crop((0,frame*32,32,(frame+1)*32)).resize((96,96),Image.Resampling.NEAREST)
        bg=Image.new("RGBA",(96,96),"#E9EFF3")
        bg.alpha_composite(cut.convert("RGBA"))
        sheet.paste(bg.convert("RGB"),(x+frame*106,y))
recs=[]
dopt={}
for st in ("trapinch","vibrava","flygon"):
    inputPath=SOURCE/st/"desert_scarab_ICON_STACKED_32x64_INDEXED4.png"
    inputTile=SOURCE/st/"desert_scarab_ICON_STACKED_32x64_TILES4.bin"
    assert inputPath.is_file() and inputTile.is_file()
    trial=Image.open(inputPath)
    assert trial.size==(32,64) and trial.mode=="P"
    idx0=list(trial.getdata())
    assert pack(idx0)==inputTile.read_bytes(),(st,"source tiles mismatch")
    srcRGBA=trial.convert("RGBA")
    px=list(srcRGBA.getdata())
    assert len(px)==2048
    assert all((idx0[i]==0)==(px[i][3]==0) for i in range(2048)),(st,"alpha/index mismatch")
    # Full image uses <=15 actual colors plus index0.
    distinct=sorted(set(idx0)-{0})
    assert len(distinct)<=15
    desired={i:srcRGBA.getpixel((idx0.index(i)%32,idx0.index(i)//32))[:3] for i in distinct}
    labs={i:lab(rgb) for i,rgb in desired.items()}
    options=[]
    for bank,banklab in enumerate(BANK_LAB):
        choices={v:min(range(1,16),key=lambda n:(de(labs[v],banklab[n]),n)) for v in distinct}
        remapped=[0 if i==0 else choices[i] for i in idx0]
        assert all((a==0)==(b==0) for a,b in zip(idx0,remapped))
        assert unpack(pack(remapped))==remapped
        weighted_sq=sum(de(labs[k],banklab[choices[k]])**2 for k in idx0 if k!=0)
        count=sum(k!=0 for k in idx0)
        rms=math.sqrt(weighted_sq/count) if count else 0
        maxde=max((de(labs[v],banklab[choices[v]]) for v in distinct),default=0)
        options.append({"bank":bank,"paletteIndexInGame":bank,
                        "rmsLabDeltaE76":round(rms,4),
                        "maxUniqueColorDeltaE76":round(maxde,4),
                        "usedNontransparentColors":len(set(remapped)-{0}),
                        "sourceUsedColors":len(distinct),
                        "sourceColorToBankIndex":{str(k):v for k,v in choices.items()},
                        "pixels":remapped})
    chosen=min(options,key=lambda t:(t["rmsLabDeltaE76"],abs(t["bank"]-1),t["bank"]))
    bank=chosen["bank"];array=chosen["pixels"]
    assert len(array)==2048 and array.count(0)==idx0.count(0)
    d=OUT/st;d.mkdir(parents=True,exist_ok=True)
    pngPath=d/f"{st}_shared_bank{bank}_32x64_unapproved.png"
    indexed=Image.new("P",(32,64))
    indexed.putdata(array)
    palette=[v for color in BANKS[bank] for v in color]+[0]*(768-48)
    indexed.putpalette(palette)
    indexed.info["transparency"]=0
    indexed.save(pngPath,bits=4,optimize=True)
    reopened=Image.open(pngPath)
    assert reopened.mode=="P" and reopened.size==(32,64)
    assert list(reopened.getdata())==array
    tilePath=d/f"{st}_shared_bank{bank}_raw4bpp_tiles.bin"
    tilePath.write_bytes(pack(array))
    assert unpack(tilePath.read_bytes())==array
    ncgr=d/f"{st}_shared_bank{bank}.NCGR"
    decimg=d/f"{st}_shared_bank{bank}_decoded.png"
    # Exact command from upstream's make_pl_poke_icon.py
    run(ARGS.nitrogfx,pngPath,ncgr,"-clobbersize","-version101")
    assert ncgr.read_bytes()[:4]==b"RGCN",ncgr.read_bytes()[:8]
    # Decoder -width is in 8px tiles: 4 tiles = 32 pixels; -palindex is one-based.
    run(ARGS.nitrogfx,ncgr,decimg,"-palette",NCLR,
        "-palindex",str(bank+1),"-width","4","-object")
    decoded=Image.open(decimg)
    assert decoded.size==(32,64) and decoded.mode=="P",(st,decoded.size,decoded.mode)
    difference=sum(x!=y for x,y in zip(array,decoded.getdata()))
    assert difference==0,(st,"original game encoder index differences",difference)
    opaque_src=sum(k!=0 for k in idx0)
    rendered=render_indices(array,bank)
    assert sum(a!=0 for a in rendered.getchannel("A").getdata())==opaque_src
    # Compare with independent final bitmap actually encoded by NitroGFX.
    original_bank=Image.open(pngPath).convert("RGBA")
    assert original_bank.getchannel("A").tobytes()==rendered.getchannel("A").tobytes()
    rec={"stage":st,
         "sourceIndexed32x64SHA256":sha(inputPath),
         "sourceRawTileSHA256":sha(inputTile),
         "sourceAlphaPixelCount":opaque_src,
         "sharedSourcePaletteSHA256":sha(SHARED),
         "sharedSourcePaletteLength":256,
         "sharedPalettePreservedExact":True,
         "availableNonzeroPaletteBanks":3,
         "candidateBankChoices":[{k:v for k,v in opt.items() if k!="pixels"} for opt in options],
         "recommendedBank":bank,
         "recommendedPaletteIndexMetadata":bank,
         "recommendationIsArtworkApproval":False,
         "paletteBankIsNotNewOrAllocated":True,
         "indexPixelDifferenceAfterRealEncoderDecoder":difference,
         "alphaMaskPreserved":True,
         "4bppTileBytes":tilePath.stat().st_size,
         "encodedNCGRBytes":ncgr.stat().st_size,
         "ncgrSHA256":sha(ncgr),
         "indexedSourceSHA256":sha(pngPath),
         "decodedPNG_SHA256":sha(decimg),
         "unapprovedInputPNG":str(inputPath),
         "paletteCompatibleSourcePNG":str(pngPath.relative_to(OUT)),
         "tileFile":str(tilePath.relative_to(OUT)),
         "nativeNCGR":str(ncgr.relative_to(OUT)),
         "nativeNitroGfxDecode":str(decimg.relative_to(OUT)),
         "approved":False,"integrated":False}
    recs.append(rec)
    dopt[st]={"trial":srcRGBA,"opts":options}
    print("SHARED_ICON_QA_PASS",st,"bank",bank,"rmsDE",chosen["rmsLabDeltaE76"],"NCGR",ncgr.stat().st_size)
# Show the actual colors of all three unmodified shared banks and best choice.
W,H=1090,855
sheet=Image.new("RGB",(W,H),"#F4F7F9");draw=ImageDraw.Draw(sheet)
draw.text((20,13),"MERCURY REDUX / PLATINUM SHARED-PALETTE ICON TEST",font=font(22,True),fill="#263A4B")
draw.text((20,46),"Unapproved technical candidates — no shared palette changes, species IDs, or ROM edits",font=font(14),fill="#9C4439")
for i,st in enumerate(("trapinch","vibrava","flygon")):
    y=86+i*254
    draw.rounded_rectangle((12,y,W-12,y+244),radius=11,outline="#C9D5DC",fill="white")
    draw.text((23,y+10),st.upper(),font=font(18,True),fill="#30495B")
    draw.text((23,y+38),"Stage-color trial",font=font(12),fill="#536575")
    base=dopt[st]["trial"]
    display_frames(sheet,base,24,y+63)
    for bank in range(3):
        opt=dopt[st]["opts"][bank]
        x=280+bank*258
        draw.text((x,y+38),f"Shared bank {bank}",font=font(12),fill="#4C6170")
        draw.text((x,y+57),f"ΔE76 RMS {opt['rmsLabDeltaE76']:.1f}",font=font(11),fill="#657787")
        rendered=render_indices(opt["pixels"],bank)
        display_frames(sheet,rendered,x,y+83)
        if next(z["recommendedBank"] for z in recs if z["stage"]==st)==bank:
            draw.text((x,y+211),"Lowest color error",font=font(12,True),fill="#3F6D50")
        else:
            draw.text((x,y+211),"Alternate candidate",font=font(12),fill="#687B88")
preview=OUT/"all_three_shared_palette_choices_mobile.png"
sheet.save(preview,optimize=True)
report={"schema":"mercury-delta-orpheus-shared-icon-bank-pret-platinum-preflight-v1",
        "source":"Unmodified upstream pret/pokeplatinum shared 256-color icon palette",
        "upstreamPalPath":"res/pokemon/.shared/pl_poke_icon.pal",
        "sharedPaletteSHA256":sha(SHARED),"sharedPaletteEntryCount":256,
        "populated16ColorBanks":[0,1,2],"allReservedBanksUntouched":True,
        "originalSourceIcon32Views":6,"gameCanvas":[32,64],
        "nativeEncoderFlags":["-clobbersize","-version101"],
        "nativeDecoderPixelDifferencesAll":0,
        "sourceAlphaMasksAllPreserved":True,"unapproved":True,
        "notFormRegistered":True,"noROMModifications":True,"noNARCInjected":True,
        "gameRuntimeNotTested":True,
        "warnings":[
          "Visual choice based on CIE Lab color error, not an accepted artwork approval.",
          "A bank must be explicitly assigned in Delta form metadata; current vanilla species mappings are not modified.",
          "Platinum's shared icon palette remains intact. Other Pokémon assets retain their own original palette indices.",
          "Actual new form/ID collision-safe registration and NARC archive assembly are not complete."],
        "preview":str(preview.relative_to(ROOT)),
        "stageResults":recs}
q=ROOT/"shared_icon_palette_qa.json"
q.write_text(json.dumps(report,indent=2)+"\n")
(OUT/"README.md").write_text(
 "# Desert Scarab real Platinum shared-palette icons (UNAPPROVED)\n\n"
 "[Compare all three populated global icon banks](all_three_shared_palette_choices_mobile.png).\n\n"
 "Source target: original upstream **32x64** two-frame vertically stacked indexed4 PNG. "
 "All three candidates use only the three **already existing** global 16-color banks in "
 "Platinum's **unmodified** 256-entry \`pl_poke_icon.pal\`, not the separate battle palettes. "
 "Best color-matching bank per stage selected by CIE Lab RMS for QA only; bank choice still "
 "requires visual/user approval and later Delta form metadata. "
 "The exact upstream \`make_pl_poke_icon.py\` flags encoded each PNG to real NCGR, and "
 "the upstream decoder verified **0 palette-index differences** across 2048 pixels each. "
 "This is a native source compatibility proof, **not an NARC archive, registered form, "
 "runtime validation or permission to integrate**.\n\n"
 "See [machine QA](../shared_icon_palette_qa.json).\n")
print("SHARED_ICON_PALETTE_REAL_NITROGFX_PASS",json.dumps({
  "stages":3,"sha256":sha(SHARED),"banks":[r["recommendedBank"] for r in recs],
  "zeroPixelDifference":True,"noPlatinumChanges":True,"unapproved":True}))
