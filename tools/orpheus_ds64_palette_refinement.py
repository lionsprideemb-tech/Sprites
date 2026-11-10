#!/usr/bin/env python3
"""Experimental palette-only quality refinement on the verified original Orpheus sprites.

Neither source art nor silhouette/placement is modified. Candidate DS palettes are
chosen exclusively from original source colors after BGR555 rounding, with one
transparent slot. Outputs remain isolated and unapproved.
"""
from __future__ import annotations
import hashlib
import json
import math
import struct
from collections import Counter, defaultdict
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path("safepng")
BASE = Path("report/ds64_experiment")
OUT = Path("report/ds64_refinement")
OUT.mkdir(parents=True, exist_ok=True)
ARCHIVE = Path("orpheus-original-resources.rar")
ARCHIVE_SHA = "72539b83b55a427c4adcdf2f3e5397cc28371875a720f687ffcf4e2a6d803ef9"
STAGES = [(329, "vibrava"), (330, "flygon")]
font = ImageFont.load_default()

def hashfile(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda: f.read(1048576), b""):
            h.update(part)
    return h.hexdigest()

def to_word(rgb):
    return sum(max(0, min(31, round(rgb[i] * 31 / 255))) << (5*i) for i in range(3))

def from_word(word):
    return tuple(round(((word >> (5*i)) & 31) * 255 / 31) for i in range(3))

def ds_tiles(indices):
    assert len(indices) == 4096
    data = bytearray()
    for ty in range(0,64,8):
        for tx in range(0,64,8):
            for dy in range(8):
                for dx in range(0,8,2):
                    l=indices[(ty+dy)*64+tx+dx]
                    r=indices[(ty+dy)*64+tx+dx+1]
                    assert 0 <= l <=15 and 0 <=r<=15
                    data.append(l | (r<<4))
    assert len(data)==2048
    decoded=[0]*4096
    p=0
    for ty in range(0,64,8):
        for tx in range(0,64,8):
            for dy in range(8):
                for dx in range(0,8,2):
                    v=data[p];p+=1
                    decoded[(ty+dy)*64+tx+dx]=v&15
                    decoded[(ty+dy)*64+tx+dx+1]=v>>4
    assert decoded==indices
    return bytes(data)

def metric(reference, result):
    assert reference.size==result.size==(64,64)
    src=list(reference.getdata());dst=list(result.getdata())
    assert all((a[3]>0)==(b[3]>0) for a,b in zip(src,dst)), "changed alpha silhouette"
    n=0
    total_abs=0
    total_sq=0
    changed=0
    luma_src=[.2126*a[0]+.7152*a[1]+.0722*a[2] for a in src]
    luma_dst=[.2126*a[0]+.7152*a[1]+.0722*a[2] for a in dst]
    for a,b in zip(src,dst):
        if a[3] == 0: continue
        n+=1
        diffs=[abs(a[i]-b[i]) for i in range(3)]
        total_abs+=sum(diffs)
        total_sq+=sum(v*v for v in diffs)
        if a[:3]!=b[:3]:changed+=1
    edge_errors=[]
    for y in range(64):
        for x in range(64):
            i=y*64+x
            if not src[i][3]: continue
            for j in (i+1 if x<63 else -1, i+64 if y<63 else -1):
                if j<0 or not src[j][3]:continue
                e0=luma_src[i]-luma_src[j]
                e1=luma_dst[i]-luma_dst[j]
                edge_errors.append(abs(e0-e1))
    assert edge_errors
    return dict(
        meanAbsoluteRGBChannelError=round(total_abs/(3*n),4),
        rmsRGBChannelError=round(math.sqrt(total_sq/(3*n)),4),
        changedOpaquePixelPercent=round(changed*100/n,2),
        meanLumaEdgeDifference=round(sum(edge_errors)/len(edge_errors),4),
        opaquePixels=n
    )

def edge_hist(image):
    pixels=list(image.getdata())
    by_color=Counter()
    edge_count=defaultdict(float)
    for y in range(64):
        for x in range(64):
            i=y*64+x
            a=pixels[i]
            if not a[3]:continue
            rgb=a[:3]
            by_color[rgb]+=1
            if x+1<64:
                b=pixels[i+1]
                if b[3] and b[:3]!=rgb:
                    dx=sum(abs(a[k]-b[k]) for k in range(3))/3
                    edge_count[rgb] += dx/64
                    edge_count[b[:3]] += dx/64
            if y+1<64:
                b=pixels[i+64]
                if b[3] and b[:3]!=rgb:
                    dx=sum(abs(a[k]-b[k]) for k in range(3))/3
                    edge_count[rgb] += dx/64
                    edge_count[b[:3]] += dx/64
    return by_color,edge_count

def weighted_dist(rgb, ds_rgb, weights):
    return sum(weights[i]*(rgb[i]-ds_rgb[i])**2 for i in range(3))

def select_source_palette(source, edge_strength, color_mode):
    counts, edges = edge_hist(source)
    unique_colors=sorted(counts)
    all_words=sorted({to_word(c) for c in unique_colors})
    assert len(all_words)>15, "only use optimizer for source requiring reduction"
    expanded_colors={w:from_word(w) for w in all_words}
    rgb_weights={"perceptual":(.27,.66,.07), "balanced":(.34,.46,.20), "equal":(1/3,1/3,1/3)}[color_mode]
    edge_total=max(edges.values(),default=0)
    importance=[]
    for col in unique_colors:
        n=counts[col]
        # Short, contrast-rich features receive more weight, but populous colors remain important.
        factor=1+edge_strength*min(2.0, edges.get(col,0)/max(1,n)*4.5)
        importance.append(n*factor)
    losses={}
    for src_col in unique_colors:
        losses[src_col]={w:weighted_dist(src_col,expanded_colors[w],rgb_weights) for w in all_words}
    def objective(pal):
        return sum(importance[i]*min(losses[col][w] for w in pal) for i,col in enumerate(unique_colors))
    retained=set(all_words)
    # Deterministic backward selection: remove the least costly extra source color.
    while len(retained)>15:
        candidates=[(objective(retained-{w}), w) for w in sorted(retained)]
        _,drop=min(candidates)
        retained.remove(drop)
    best=objective(retained)
    # Local 1-for-1 exchanges reduce sensitivity to the elimination order.
    for _ in range(8):
        choice=None
        for leaving in sorted(retained):
            for arriving in all_words:
                if arriving in retained:continue
                loss=objective((retained-{leaving})|{arriving})
                if loss+1e-7<best and (choice is None or (loss,leaving,arriving)<choice):
                    choice=(loss,leaving,arriving)
        if choice is None:break
        best,leaving,arriving=choice
        retained.remove(leaving)
        retained.add(arriving)
    selected=sorted(retained)
    indices=[]
    palette_words=[0]+selected
    look={w:i+1 for i,w in enumerate(selected)}
    out=Image.new("RGBA",(64,64),(0,0,0,0))
    result=[]
    exact_source=0
    for pixel in source.getdata():
        if not pixel[3]:
            indices.append(0)
            result.append((0,0,0,0))
        else:
            rgb=pixel[:3]
            chosen=min(selected,key=lambda w:(losses[rgb][w], w))
            i=look[chosen]
            indices.append(i)
            final=expanded_colors[chosen]
            result.append((*final,255))
            if chosen==to_word(rgb): exact_source+=1
    out.putdata(result)
    assert len(set(indices))<=16
    assert out.getchannel("A").tobytes()==source.getchannel("A").tobytes()
    tiles=ds_tiles(indices)
    pal=bytes().join(struct.pack("<H",w) for w in palette_words+[0]*(16-len(palette_words)))
    assert len(pal)==32
    return out,tiles,pal,dict(
        uniqueDSColors=len(set(indices)),
        sourcePaletteEntries=len(all_words),
        chosenOpaqueColors=len(selected),
        originalDSColorDirectMatchCount=exact_source,
        mode=color_mode,edgeStrength=edge_strength)

def board(canvas, im, x, y, dim=192):
    bg=Image.new("RGBA",(dim,dim),(236,241,245,255))
    view=im.resize((dim,dim),Image.Resampling.NEAREST)
    bg.alpha_composite(view)
    canvas.paste(bg.convert("RGB"),(x,y))

if hashfile(ARCHIVE)!=ARCHIVE_SHA:
    raise RuntimeError("Original resource SHA mismatch")
W=1120;ROW=268
H=115+4*ROW+34
sheet=Image.new("RGB",(W,H),"#f7f6f3")
draw=ImageDraw.Draw(sheet)
draw.text((20,13),"ORPHEUS / THRACEAN DS64 — EXPERIMENTAL QUALITY REFINEMENT",font=font,fill="#27303c")
draw.text((20,34),"Exactly the same 64px silhouette/pixel placement. Baseline median-cut vs best source-color palette.",font=font,fill="#465364")
draw.text((20,54),"No redraws, no new anatomy, no recolors. Unapproved. Candidate palettes drawn only from original art.",font=font,fill="#8b3e38")
for xpos,label in [(24,"Original 160x160"),(235,"Prior DS64 baseline (3x)"),(451,"Optimized palette (3x)"),(672,"RGB/luminance differences vs 64px source")]:
    draw.text((xpos,92),label,font=font,fill="#27303c")
rows=[]
chosen_count=0
for stage_idx,(num,name) in enumerate(STAGES):
    for view_idx,(role,suffix) in enumerate([("front","_1"),("back","b_1")]):
        basename=f"{name}_{role}"
        source_path=ROOT/f"{num}{suffix}.png"
        before_path=BASE/f"{basename}_experimental_ds64.png"
        reference_path=BASE/f"{basename}_unlimited64.png"
        raw=Image.open(source_path).convert("RGBA")
        before=Image.open(before_path).convert("RGBA")
        reference=Image.open(reference_path).convert("RGBA")
        assert raw.size==(160,160)
        assert before.size==reference.size==(64,64)
        assert before.getchannel("A").tobytes()==reference.getchannel("A").tobytes(), "baseline mask already differs"
        baseline=metric(reference,before)
        trials=[]
        for edge_strength in [0.0,0.65,1.5,3.0]:
            for mode in ["balanced","perceptual","equal"]:
                im,tiles,pal,meta=select_source_palette(reference,edge_strength,mode)
                m=metric(reference,im)
                trials.append(dict(image=im,tiles=tiles,palette=pal,metric=m,config=meta))
        # Objective allows no meaningful edge-clarity regression even if RGB score improves.
        candidates=sorted(trials,key=lambda x:(
            .77*x["metric"]["meanAbsoluteRGBChannelError"]+.23*x["metric"]["meanLumaEdgeDifference"],
            x["metric"]["meanAbsoluteRGBChannelError"],
            x["config"]["edgeStrength"],x["config"]["mode"]))
        safe=[t for t in candidates if (
            t["metric"]["meanLumaEdgeDifference"]<=baseline["meanLumaEdgeDifference"]+0.20
            and t["metric"]["meanAbsoluteRGBChannelError"]<=baseline["meanAbsoluteRGBChannelError"]-.035
        )]
        improvement=safe[0] if safe else None
        if improvement:
            selected=improvement["image"]
            native_tiles=improvement["tiles"]
            native_pal=improvement["palette"]
            selected_metrics=improvement["metric"]
            picked=improvement["config"]
            chosen_count+=1
            status="SELECTED (loss metric improved)"
        else:
            selected=before
            selected_metrics=baseline
            picked={"mode":"baseline-retained","edgeStrength":None}
            # Existing binaries from prior validated experiment retained, NOT rewritten.
            native_tiles=(BASE/f"{basename}_4bpp_tiles.bin").read_bytes()
            native_pal=(BASE/f"{basename}_bgr555_palette.bin").read_bytes()
            status="RETAINED BASELINE (no safe win)"
        assert len(native_tiles)==2048 and len(native_pal)==32
        assert selected.getchannel("A").tobytes()==reference.getchannel("A").tobytes()
        # Verify resulting tiles/palettes reproduce exact RGBA pixels, including the alpha mask.
        packed_indices=[]
        for ty in range(0,64,8):
            for tx in range(0,64,8):
                for dy in range(8):
                    for dx in range(0,8,2):
                        pass
        # Decode native DS tile order to an index canvas.
        indices=[0]*4096
        off=0
        for ty in range(0,64,8):
            for tx in range(0,64,8):
                for dy in range(8):
                    for dx in range(0,8,2):
                        c=native_tiles[off];off+=1
                        indices[(ty+dy)*64+tx+dx]=c&15
                        indices[(ty+dy)*64+tx+dx+1]=c>>4
        words=struct.unpack("<16H",native_pal)
        pixels=[(*from_word(words[i]),255) if i else (0,0,0,0) for i in indices]
        assert pixels==list(selected.getdata()), "native tile/palette decode mismatch"
        selected_path=OUT/f"{basename}_experimental_refinement64.png"
        selected.save(selected_path)
        (OUT/f"{basename}_4bpp_tiles.bin").write_bytes(native_tiles)
        (OUT/f"{basename}_bgr555_palette.bin").write_bytes(native_pal)
        yi=115+(stage_idx*2+view_idx)*ROW
        draw.rounded_rectangle((15,yi-5,W-15,yi+ROW-16),radius=12,fill="white",outline="#d5dce2")
        draw.text((25,yi+3),f"{name.upper()} {role.upper()}: {status}",fill="#243347",font=font)
        board(sheet,raw,24,yi+30,160)
        board(sheet,before,232,yi+30,192)
        board(sheet,selected,448,yi+30,192)
        draw.text((675,yi+33),f"RGB error: {baseline['meanAbsoluteRGBChannelError']:.3f} -> {selected_metrics['meanAbsoluteRGBChannelError']:.3f} /255",fill="#27303c",font=font)
        draw.text((675,yi+55),f"Edge contrast error: {baseline['meanLumaEdgeDifference']:.3f} -> {selected_metrics['meanLumaEdgeDifference']:.3f}",fill="#27303c",font=font)
        draw.text((675,yi+77),f"RMS error: {baseline['rmsRGBChannelError']:.3f} -> {selected_metrics['rmsRGBChannelError']:.3f}",fill="#27303c",font=font)
        draw.text((675,yi+99),f"Source colors: {len({p[:3] for p in reference.getdata() if p[3]>0})} -> <=15 opaque in DS",fill="#485766",font=font)
        draw.text((675,yi+121),f"Optimizer: {picked['mode']} / edge weight {picked['edgeStrength']}",fill="#485766",font=font)
        draw.text((675,yi+143),"Source art and 64px alpha silhouette: unchanged",fill="#485766",font=font)
        draw.text((675,yi+165),"Encoded DS OBJ 4bpp tiles: 2048 bytes / palette: 32 bytes",fill="#485766",font=font)
        draw.text((675,yi+187),"No shiny, icon or in-ROM sprite substitution",fill="#8b3e38",font=font)
        row=dict(
            species=name,view=role,sourceFile=str(source_path),
            sourceSHA256=hashfile(source_path),sourceSize=[160,160],
            chosenStatus=status, selectedConfig=picked,
            baseline=baseline,refinement=selected_metrics,
            candidateTrialCount=len(trials),
            improved=bool(improvement),
            improvedMeanAbsoluteRGBError=round(baseline["meanAbsoluteRGBChannelError"]-selected_metrics["meanAbsoluteRGBChannelError"],4),
            improvedMeanLumaEdgeError=round(baseline["meanLumaEdgeDifference"]-selected_metrics["meanLumaEdgeDifference"],4),
            targetSize=[64,64],alphaMaskUnchanged=True,nativeTilesBytes=2048,paletteBytes=32,
            nativeTilesSHA256=hashfile(OUT/f"{basename}_4bpp_tiles.bin"),
            nativePaletteSHA256=hashfile(OUT/f"{basename}_bgr555_palette.bin"),
            approved=False,romIntegrated=False,
            experiment=True)
        rows.append(row)
        print("REFINEMENT_RESULT",json.dumps(row,sort_keys=True))
sheet_path=OUT/"orpheus_ds64_palette_refinement_before_after.png"
sheet.save(sheet_path,optimize=True)
report={
    "schema":"mercury-orpheus-thracean-ds64-refinement-v1",
    "archiveSHA256":ARCHIVE_SHA,
    "method":"original DS64 60px fit and alpha mask unchanged, source-only BGR555 palette medoid search with 15 opaque colors, deterministic loss/edge guard, exact DS4bpp decode verification",
    "selectionRule":"best score = .77 * channel absolute error + .23 * edge luminance error; reject if mean luminance edge error rises over 0.20 or channel error improves under 0.035/255",
    "stageCount":2,"views":len(rows),"selectedImprovements":chosen_count,
    "sourceArtModified":False,"approvalsChanged":False,"romIntegrated":False,
    "originalTyping":{"Trapinch":"Bug","Vibrava":"Bug/Dragon","Flygon":"Bug/Dragon"},
    "mercuryFlygonTypeRequirement":"Bug/Ground, not yet implemented",
    "originalArtistPermissionVerified":False,"gameArchiveNCGRNCLRImplemented":False,
    "notes":["Quantitative loss does not guarantee subjective visual quality.","The rendering uses the same 64px silhouettes as the prior experiment.","Trapinch left unchanged in this pass.","Original Orpheus archive contains no verified matching regional shiny sets."],
    "rows":rows
}
(OUT/"refinement_metrics.json").write_text(json.dumps(report,indent=2)+"\n")
print("REFINEMENT_SUMMARY",json.dumps(dict(views=len(rows),selectedImprovements=chosen_count,unapproved=True,gameChanges=False),sort_keys=True))
print("REFINEMENT_SHEET",sheet_path,"bytes",sheet_path.stat().st_size,"sha256",hashfile(sheet_path))

# Export only the finished comparison PNG to logs so it can be published to the
# quarantined research branch without committing any original archive resources.
import base64
print("REFINEMENT_BASE64_START orpheus_ds64_palette_refinement_before_after.png")
print(base64.b64encode(sheet_path.read_bytes()).decode("ascii"))
print("REFINEMENT_BASE64_END orpheus_ds64_palette_refinement_before_after.png")
