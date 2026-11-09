#!/usr/bin/env python3
"""Read-only original Orpheus sprite QA. No source imports or art approvals."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import hashlib, json, re, subprocess, base64

ROOT=Path("safepng")
OUT=Path("report")
OUT.mkdir(exist_ok=True)
species=[(328,"Trapinch"),(329,"Vibrava"),(330,"Flygon")]
standard={}
regional={}
records=[]
for num,name in species:
    for form in ["vanilla","regional"]:
        paths={
            "front":ROOT/f"{num}{'_1' if form=='regional' else ''}.png",
            "back":ROOT/f"{num}{'b_1' if form=='regional' else 'b'}.png",
            "icon":ROOT/f"icon{num}{'_1' if form=='regional' else ''}.png",
        }
        current={}
        for role,path in paths.items():
            if not path.exists():
                records.append(dict(species=name,form=form,role=role,error="MISSING"))
                continue
            im=Image.open(path).convert("RGBA")
            colors=im.getcolors(10_000_000)
            uniq=len(colors) if colors else -1
            used_alpha=sorted({p[3] for p in im.getdata()})
            bounds=im.getchannel("A").getbbox()
            record=dict(species=name,form=form,role=role,path=str(path),dimensions=list(im.size),colorsIncludingTransparent=uniq,alpha=used_alpha,bounds=bounds,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            records.append(record)
            current[role]=im
        (regional if form=="regional" else standard)[num]=current

# Utility for silhouette shape comparison, without claiming artistic uniqueness.
def silhouette(im,size=(64,64)):
    a=im.getchannel("A")
    rect=a.getbbox()
    if not rect:return None
    crop=a.crop(rect)
    w,h=crop.size
    s=min((size[0]-4)/w,(size[1]-4)/h)
    dest=Image.new("L",size,0)
    cropped=crop.resize((max(1,round(w*s)),max(1,round(h*s))),Image.Resampling.NEAREST)
    dest.paste(cropped,((size[0]-cropped.width)//2,(size[1]-cropped.height)//2))
    return dest
metrics=[]
for num,name in species:
    a=regional.get(num,{}).get("front")
    b=standard.get(num,{}).get("front")
    if a and b:
        aa=silhouette(a);bb=silhouette(b)
        ab=list(aa.getdata());cb=list(bb.getdata())
        sa={i for i,v in enumerate(ab) if v>0}
        sb={i for i,v in enumerate(cb) if v>0}
        iou=len(sa&sb)/max(1,len(sa|sb))
        metrics.append(dict(species=name,normalizedSilhouetteIoU=round(iou,3),exactSameRGBA=a.size==b.size and a.tobytes()==b.tobytes()))

# Research-only sprite contact sheet: original image PNGs, no mutations.
font=ImageFont.load_default()
W,H=1180,785
canvas=Image.new("RGB",(W,H),"#f7f5f1")
draw=ImageDraw.Draw(canvas)
draw.text((30,24),"POKEMON ORPHEUS  /  REGIONAL FLYGON FAMILY",fill="#27303c",font=font)
draw.text((30,46),"Unapproved source PNGs from original 2021 resource pack | Native source pixels, no recolors or art edits",fill="#515c6a",font=font)
draw.text((30,65),"Battlers 160x160  |  Icons 128x64 sheets  |  NOT DS 64x64 graphics",fill="#515c6a",font=font)
col_centers=[204,588,972]
for (num,name),cx in zip(species,col_centers):
    draw.rounded_rectangle((cx-170,100,cx+170,755),radius=14,fill="#ffffff",outline="#ced4dc",width=2)
    draw.text((cx-75,115),f"#{num} {name}",fill="#202a35",font=font)
    for role,y,label in [("front",143,"REGIONAL FRONT"),("back",358,"REGIONAL BACK"),("icon",565,"REGIONAL ICON SHEET")]:
        draw.text((cx-65,y),label,fill="#536070",font=font)
        im=regional.get(num,{}).get(role)
        if im is None:
            draw.text((cx-50,y+80),"MISSING",fill="#bd4750",font=font)
            continue
        # Center transparent images unchanged at 1x; never smooth or invent pixels.
        back=Image.new("RGBA",im.size,(239,243,246,255))
        back.alpha_composite(im)
        xp=cx-im.width//2
        yp=y+24
        canvas.paste(back.convert("RGB"),(xp,yp))
        draw.rectangle((xp,yp,xp+im.width,yp+im.height),outline="#cbd3db",width=1)
canvas.save(OUT/"orpheus_regional_family_actual_pngs.png",optimize=True)

# Side-by-side vanilla vs regional front sprites for independent visual judgement.
W2,H2=1180,455
comparison=Image.new("RGB",(W2,H2),"#f7f5f1")
d=ImageDraw.Draw(comparison)
d.text((30,20),"ORPHEUS RESOURCE PACK  /  VANILLA VS REGIONAL FRONT SPRITES",fill="#202b35",font=font)
d.text((30,40),"Original pixel art source. Vanilla 256x256 scaled to 160 with nearest-neighbor for VIEWING ONLY",fill="#5a6470",font=font)
for (num,name),cx in zip(species,col_centers):
    d.rounded_rectangle((cx-170,85,cx+170,425),radius=12,fill="white",outline="#c8d0d8",width=2)
    d.text((cx-55,98),f"#{num} {name}",fill="#202a35",font=font)
    for i,(im,label) in enumerate([(standard.get(num,{}).get("front"),"VANILLA"),(regional.get(num,{}).get("front"),"REGIONAL")]):
        xpos=cx-160+i*160; ypos=160
        d.text((xpos+42,140),label,fill="#596472",font=font)
        if im:
            if im.size!=(160,160):im=im.resize((160,160),Image.Resampling.NEAREST)
            bg=Image.new("RGBA",(160,160),(235,240,245,255))
            bg.alpha_composite(im)
            comparison.paste(bg.convert("RGB"),(xpos,ypos))
comparison.save(OUT/"orpheus_vanilla_regional_comparison.png",optimize=True)

# Find PBS/metadata-type records in original archive by paths, and record relevant lines.
archives=Path("all-rar-paths.txt")
pbs_hits=[]
if archives.exists() and Path("orpheus-original-resources.rar").exists():
    ap=[line[7:] for line in archives.read_text(errors="replace").splitlines() if line.startswith("Path = ")]
    choices=[p for p in ap if p.lower().endswith((".txt",".pbs",".dat")) and ("/pbs/" in ("/"+p.lower()) or "pokemonforms" in p.lower() or p.lower().endswith("/pokemon.txt"))]
    print("PBS CANDIDATES",json.dumps(choices[:80]))
    Path("report/pbs_candidate_paths.txt").write_text("\n".join(choices[:200])+"\n")
    for p in choices[:80]:
        if any(x in p.lower() for x in ["pokemon", "form", "regional", "species"]):
            try:
                o=subprocess.run(["7z","x","-so","orpheus-original-resources.rar",p],capture_output=True,timeout=40)
                if len(o.stdout)>5_000_000:continue
                content=o.stdout.decode("utf-8",errors="replace")
                if not re.search(r"TRAPINCH|VIBRAVA|FLYGON|\[328[,:\]]|\[329[,:\]]|\[330[,:\]]",content,re.I):continue
                lines=content.splitlines()
                match_idxs=[i for i,l in enumerate(lines) if re.search(r"TRAPINCH|VIBRAVA|FLYGON|\[(?:328|329|330)(?:,1)?\]",l,re.I)]
                found=[]
                for i in match_idxs[:90]:
                    context="\n".join(f" L{j+1}: {lines[j][:230]}" for j in range(max(0,i-4),min(len(lines),i+25)))
                    found.append(context)
                pbs_hits.append(dict(file=p,totalLines=len(lines),matchCount=len(match_idxs),contexts=found))
            except Exception as e:
                print("PBS PROBE ERROR",p,str(e)[:300])
Path("report/pbs_family_matches.json").write_text(json.dumps(pbs_hits,indent=2))
Path("report/qa_summary.json").write_text(json.dumps(dict(records=records,shapeComparison=metrics,pbsMatches=pbs_hits),indent=2))
for row in metrics:print("SILHOUETTE",json.dumps(row))
print("PBS MATCHED FILES",len(pbs_hits))
for row in pbs_hits:
    print("PBS FILE",row["file"],"hits",row["matchCount"])
    for context in row["contexts"][:4]:print("PBS CONTEXT",context[:2400].replace("\n"," | "))
for name in ["orpheus_regional_family_actual_pngs.png","orpheus_vanilla_regional_comparison.png"]:
    path=OUT/name
    print("OUTPUT",name,"bytes",path.stat().st_size,"sha256",hashlib.sha256(path.read_bytes()).hexdigest())
    print("BASE64_START",name)
    print(base64.b64encode(path.read_bytes()).decode("ascii"))
    print("BASE64_END",name)
