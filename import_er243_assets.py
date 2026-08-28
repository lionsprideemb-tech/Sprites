#!/usr/bin/env python3
from pathlib import Path
from PIL import Image
import pandas as pd, shutil, sys, json

if len(sys.argv) != 4:
    print("usage: import_er243_assets.py <asset_root> <queue.csv> <mercury_fork_root>")
    raise SystemExit(2)

asset_root=Path(sys.argv[1])
queue=pd.read_csv(sys.argv[2])
fork=Path(sys.argv[3])
stage=fork/"graphics"/"pokemon_mercury_staging"/"elite_redux_approved"
stage.mkdir(parents=True,exist_ok=True)

rows=[]
fails=[]
for _,r in queue.iterrows():
    iid=str(r["internal_id"])
    dest=stage/iid.lower().replace("species_","")
    dest.mkdir(parents=True,exist_ok=True)
    files={
        "front.png":r["sprite_source_path"],
        "back.png":r["back_source_path"],
        "icon.png":r["icon_source_path"],
        "normal.pal":r["palette_source_path"],
        "shiny.pal":r["shiny_palette_source_path"],
    }
    ok=True
    notes=[]
    for outname,rel in files.items():
        src=asset_root/rel
        if not src.exists():
            ok=False; notes.append("missing "+rel); continue
        shutil.copy2(src,dest/outname)
    # Validate images/palettes when all present.
    try:
        if (dest/"front.png").exists():
            im=Image.open(dest/"front.png"); im.load()
            if im.width not in (64,128) or im.height not in (64,128):
                notes.append(f"front geometry {im.size}")
        if (dest/"back.png").exists():
            im=Image.open(dest/"back.png"); im.load()
            if im.width != 64 or im.height != 64:
                notes.append(f"back geometry {im.size}")
        if (dest/"icon.png").exists():
            im=Image.open(dest/"icon.png"); im.load()
        for pal in ("normal.pal","shiny.pal"):
            if (dest/pal).exists():
                txt=(dest/pal).read_text(errors="ignore")
                if "JASC-PAL" not in txt:
                    notes.append(pal+" not JASC-PAL")
    except Exception as e:
        ok=False; notes.append("decode "+repr(e))
    rows.append({
        "internal_id":iid,
        "source_name":r["source_name"],
        "mercury_story_name":r["mercury_story_name"],
        "delta_story_form":r["delta_story_form"],
        "staged_dir":str(dest),
        "status":"PASS" if ok and not notes else ("PASS_WITH_NOTES" if ok else "FAIL"),
        "notes":"; ".join(notes)
    })
    if not ok:
        fails.append(rows[-1])

pd.DataFrame(rows).to_csv(stage/"ER243_VALIDATION.csv",index=False)
pd.DataFrame(fails).to_csv(stage/"ER243_FAILURES.csv",index=False)
print(json.dumps({
    "entries":len(rows),
    "pass":sum(x["status"]=="PASS" for x in rows),
    "pass_with_notes":sum(x["status"]=="PASS_WITH_NOTES" for x in rows),
    "fail":sum(x["status"]=="FAIL" for x in rows),
    "stage":str(stage)
},indent=2))
