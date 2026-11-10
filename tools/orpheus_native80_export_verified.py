#!/usr/bin/env python3
"""Export verified native Platinum 80px Orpheus *unapproved* source-derived assets.

Runs only after the original archive SHA-checked 160→80 probe. Select the
canvas-preserving 2x half-scale path, not the alternate crop-to-fit version.
All outputs remain research-only; never touch votes, production or ROM.
"""
from pathlib import Path
from PIL import Image
import base64,hashlib,json,struct
ROOT=Path("report/orpheus_native_platinum80")
SRC=Path("safepng")
assert ROOT.is_dir() and SRC.is_dir()
manifest=json.loads((ROOT/"native80_qa.json").read_text())
assert manifest["sourceArchiveSHA256"]=="72539b83b55a427c4adcdf2f3e5397cc28371875a720f687ffcf4e2a6d803ef9"
assert manifest["nativePlatinumBattleSpriteCanvas"]==[80,80]
assert manifest["approved"] is False and manifest["ROMModified"] is False
def sha(data):return hashlib.sha256(data).hexdigest()
def unpack(buf):
    assert len(buf)==3200
    out=[0]*6400;k=0
    for by in range(0,80,8):
        for bx in range(0,80,8):
            for y in range(8):
                for x in range(0,8,2):
                    b=buf[k];k+=1
                    out[(by+y)*80+bx+x]=b&15
                    out[(by+y)*80+bx+x+1]=b>>4
    assert k==3200
    return out
def image(idx,pal):
    words=struct.unpack("<16H",pal)
    rgb=lambda w:tuple(round(((w>>(5*i))&31)*255/31) for i in range(3))
    im=Image.new("RGBA",(80,80))
    im.putdata([(*rgb(words[n]),255) if n else (0,0,0,0) for n in idx])
    return im
def pixel2x_blocks(src):
    p=src.load();total=0;same=0;alpha_same=0
    for y in range(0,160,2):
        for x in range(0,160,2):
            b=[p[x+dx,y+dy] for dy in (0,1) for dx in (0,1)]
            total+=1
            same+=int(len(set(b))==1)
            alpha_same+=int(len({q[3] for q in b})==1)
    return same,total,alpha_same
selected=[]
for name,num in (("trapinch",328),("vibrava",329),("flygon",330)):
    for role in ("front","back"):
        base=f"{name}_{role}_half_80"
        paths=[ROOT/f"{base}.png",ROOT/f"{base}_4bpp_tiles.bin",ROOT/f"{base}_palette.bin"]
        assert all(p.exists() for p in paths)
        original=Image.open(SRC/f"{num}{'b' if role=='back' else ''}_1.png").convert("RGBA")
        assert original.size==(160,160)
        png=Image.open(paths[0]).convert("RGBA")
        tiles=paths[1].read_bytes();pal=paths[2].read_bytes()
        rec=next(r for r in manifest["views"] if r["pokemon"]==name and r["role"]==role and r["method"]=="half")
        assert sha(tiles)==rec["tileSHA256"] and sha(pal)==rec["paletteSHA256"]
        assert sha((SRC/f"{num}{'b' if role=='back' else ''}_1.png").read_bytes())==rec["sourceSHA256"]
        assert len(pal)==32 and len(tiles)==3200 and png.size==(80,80)
        assert image(unpack(tiles),pal).tobytes()==png.tobytes()
        raw80=original.resize((80,80),Image.Resampling.NEAREST)
        assert raw80.getchannel("A").tobytes()==png.getchannel("A").tobytes()
        exact,total,alpha=pixel2x_blocks(original)
        assert round(100*exact/total,2)==rec["exact2xPercent"]
        # The Vibrava back has a small number of non-identical original 2x2 alpha blocks.
        # Report this honestly rather than claiming a fully lossless half-scale.
        assert alpha==total or (name,role)==("vibrava","back")
        assert len(set(png.getdata()))<=16
        selected.append(dict(view=f"{name}_{role}",png=paths[0].name,tiles=paths[1].name,
            palette=paths[2].name,sourceSHA256=rec["sourceSHA256"],
            source2xExactBlocks=exact,source2xTotalBlocks=total,
            source2xExactPercent=round(100*exact/total,2),
            source2xAlphaExactBlocks=alpha,
            source2xAlphaTotalBlocks=total,
            alpha2xBlocksExact=alpha==total,
            pngTilesRoundTrip=True,sourceAlphaPreserved=True,
            pngSHA256=sha(paths[0].read_bytes()),
            tileSHA256=sha(tiles),paletteSHA256=sha(pal),
            tileBytes=3200,paletteBytes=32,approved=False,romIntegrated=False))
output=dict(schema="mercury-orpheus-native80-source-fidelity-export-v1",
    originalArchiveSHA256=manifest["sourceArchiveSHA256"],
    previousExperimentalCanvas=[64,64],nativePlatinumCanvas=[80,80],
    selectedMethod="half: original 160px canvas halved to native 80px, no crop",
    exact2xAllExceptVibravaBack=True,
    noSourceArtEdits=True,noHistoricalVoteEdits=True,
    noProductionChanges=True,allUnapproved=True,noROMIntegration=True,
    limitations=["The 80px battle engine resource insertion has not been tested in Mercury's ROM.",
    "Stage-specific palettes are unapproved recolor experiments.",
    "Shiny, icon and battle-engine NARC resources are not generated.",
    "The 99.5%-exact Vibrava back original includes a few nonidentical 2x2 blocks, some in alpha; the 80px preview matches the chosen nearest-sample alpha but is not fully lossless to 160px."],
    views=selected)
manifest_file=ROOT/"native80_selected_half_qa.json"
manifest_file.write_text(json.dumps(output,indent=2)+"\n")
print("NATIVE80_EXPORT_SUMMARY",json.dumps({"views":len(selected),
    "allRoundTrips":all(v["pngTilesRoundTrip"] for v in selected),
    "allSourceAlpha":all(v["sourceAlphaPreserved"] for v in selected),
    "exact2x":[v["source2xExactPercent"] for v in selected],
    "allUnapproved":True,"romIntegrated":False}))
names=["orpheus_platinum_native80_vs_ds64.png","native80_selected_half_qa.json"]
for view in selected:
    names.extend([view["png"],view["tiles"],view["palette"]])
for name in names:
    path=ROOT/name
    print("NATIVE80_FILE_START",name)
    print(base64.b64encode(path.read_bytes()).decode("ascii"))
    print("NATIVE80_FILE_END",name)
