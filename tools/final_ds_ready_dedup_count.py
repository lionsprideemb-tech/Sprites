from pathlib import Path
from PIL import Image
import collections, csv, hashlib, json, re

ROOT=Path("DS_CUSTOM_LIBRARY")
OUT=ROOT/"DS_READY_MASTER"
OUT.mkdir(parents=True, exist_ok=True)
EXTS={".png",".gif",".bmp",".jpg",".jpeg",".webp"}
EXCLUDE=[
    "/packs/Elite_Redux_ER_nextdex/",
    "/hack-reference-previews/",
    "/sprite-candidates/",
    "/gba-source-staging/",
]
ROOTS=[
    (ROOT/"packs","NATIVE_PACK"),
    (ROOT/"hack-packs","NATIVE_HACK"),
    (ROOT/"converted","CONVERTED_GBA"),
]

def norm(s):
    s=str(s).lower().replace("'","").replace("_","-").replace(" ","-")
    s=re.sub(r"[^a-z0-9-]+","-",s)
    return re.sub(r"-+","-",s).strip("-")

def role(p):
    stem=norm(p.stem); parts=[norm(x) for x in p.parts]; joined="/".join(parts)
    if "icon" in stem or "/icon/" in joined or "/icons/" in joined: return "icon"
    shiny=("shiny" in stem or any(x in {"front-shiny","back-shiny","shiny"} for x in parts))
    back=("back" in stem or any(x in {"back","backs","backsprite","backsprites","back-shiny"} for x in parts))
    front=("front" in stem or any(x in {"front","fronts","frontsprite","frontsprites","front-shiny"} for x in parts))
    if back: return "back_shiny" if shiny else "back"
    if front: return "front_shiny" if shiny else "front"
    return "unknown"

def identity(p, component):
    stem=norm(p.stem)
    generic={"front","back","front-shiny","back-shiny","icon","icon-generated","anim-front","anim-front-gba","back-gba","front-gba"}
    if stem in generic or stem.startswith("front-") or stem.startswith("back-"):
        parent=norm(p.parent.name)
        if parent in {"male","female","m","f"}:
            parent=norm(p.parent.parent.name)+"-"+parent
        return parent
    if norm(p.parent.name) in {"front","back","front-shiny","back-shiny","icon","icons","fronts","backs","frontsprites","backsprites"}:
        return stem
    x=stem
    for suffix in ["-front-shiny","-back-shiny","-front","-back","-icon","-shiny"]:
        if x.endswith(suffix):
            x=x[:-len(suffix)]; break
    return x or stem

def image_signatures(p):
    try:
        with Image.open(p) as im:
            im.seek(0); im=im.convert("RGBA")
            exact=hashlib.sha256(im.width.to_bytes(4,"big")+im.height.to_bytes(4,"big")+im.tobytes()).hexdigest()
            cmap={}; nxt=1; out=bytearray()
            out.extend(im.width.to_bytes(2,"big")); out.extend(im.height.to_bytes(2,"big"))
            for r,g,b,a in im.getdata():
                if a==0: out.extend((0,0)); continue
                key=(r,g,b,a)
                if key not in cmap: cmap[key]=nxt; nxt+=1
                out.extend(cmap[key].to_bytes(2,"big"))
            structural=hashlib.sha256(out).hexdigest()
            return exact,structural,im.width,im.height,len(cmap)
    except Exception:
        return None

def source(p, root):
    rel=p.relative_to(root)
    return rel.parts[0] if rel.parts else root.name

def quality(a):
    if a["bucket"]=="CONVERTED_GBA": tier=0
    elif a["source"]=="DrPrettyman_DS_64x64": tier=1
    elif a["source"]=="HG_Engine_DS_Sprites": tier=2
    else: tier=3
    return (tier,len(a["path"]),a["path"])

assets=[]; decode_fail=[]
for root,bucket in ROOTS:
    if not root.exists(): continue
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in EXTS: continue
        ps="/"+p.as_posix().replace("\\","/")+"/"
        if any(x in ps for x in EXCLUDE): continue
        sig=image_signatures(p)
        if not sig:
            decode_fail.append(p.as_posix()); continue
        exact,struct,w,h,colors=sig
        comp=role(p)
        assets.append({
            "path":p.as_posix(),"bucket":bucket,"source":source(p,root),
            "role":comp,"identity":identity(p,comp),
            "exact_hash":exact,"structural_hash":struct,
            "width":w,"height":h,"colors":colors
        })

# Same-role exact duplicate check.
by_exact=collections.defaultdict(list)
for a in assets: by_exact[(a["role"],a["exact_hash"])].append(a)
exact_rows=[]; exact_drop=set()
for (comp,h),items in by_exact.items():
    if len(items)<2: continue
    keep=min(items,key=quality)
    for a in items:
        if a["path"]==keep["path"]: continue
        exact_drop.add(a["path"])
        exact_rows.append({
            "reason":"EXACT_DUPLICATE","role":comp,"identity":a["identity"],
            "delete_path":a["path"],"keep_path":keep["path"],
            "delete_source":a["source"],"keep_source":keep["source"],"exact_hash":h
        })

# Same-role palette-only recolor check. Shiny roles are intentionally excluded.
by_struct=collections.defaultdict(list)
for a in assets:
    if a["path"] in exact_drop or a["role"] not in {"front","back","icon"}: continue
    by_struct[(a["role"],a["structural_hash"])].append(a)
recolor_rows=[]; recolor_drop=set()
for (comp,h),items in by_struct.items():
    if len(items)<2 or len({x["exact_hash"] for x in items})<2: continue
    keep=min(items,key=quality)
    for a in items:
        if a["path"]==keep["path"]: continue
        recolor_drop.add(a["path"])
        recolor_rows.append({
            "reason":"PALETTE_ONLY_RECOLOR","role":comp,"identity":a["identity"],
            "delete_path":a["path"],"keep_path":keep["path"],
            "delete_source":a["source"],"keep_source":keep["source"],"structural_hash":h
        })

# One Pokemon/form design = one unique normal-front structural design.
fronts=[a for a in assets if a["role"]=="front"]
canonical=[]; seen=set()
for a in sorted(fronts,key=quality):
    if a["structural_hash"] in seen: continue
    seen.add(a["structural_hash"]); canonical.append(a)

by_identity=collections.defaultdict(list)
for a in canonical: by_identity[a["identity"]].append(a)

# Preserve genuinely different custom designs for approval.
multi=[]; multi_ids=set()
core_sources={"DrPrettyman_DS_64x64","HG_Engine_DS_Sprites","DS_Styled_Gen5_8","Gen7_DS_Backsprites","Shiny_Icons_Gen1_9"}
for ident,items in sorted(by_identity.items()):
    if len({x["structural_hash"] for x in items})<2: continue
    custom_signal=(
        any(t in ident for t in ["mega","redux","delta","primal","apex","battle-bond","nightmare"])
        or any(x["bucket"]!="NATIVE_PACK" or x["source"] not in core_sources for x in items)
    )
    if not custom_signal: continue
    multi_ids.add(ident)
    for n,a in enumerate(sorted(items,key=quality),1):
        multi.append({
            "identity":ident,"design_option":n,"source":a["source"],"bucket":a["bucket"],
            "front_path":a["path"],"structural_hash":a["structural_hash"],
            "exact_hash":a["exact_hash"],"action":"KEEP_FOR_APPROVAL_SHEET"
        })

master=[{
    "identity":a["identity"],"source":a["source"],"bucket":a["bucket"],
    "front_path":a["path"],"structural_hash":a["structural_hash"],
    "exact_hash":a["exact_hash"],"multi_design_for_approval":a["identity"] in multi_ids
} for a in canonical]

def write_csv(path, rows, fields):
    with path.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)

write_csv(OUT/"exact_duplicates.csv",exact_rows,
          ["reason","role","identity","delete_path","keep_path","delete_source","keep_source","exact_hash"])
write_csv(OUT/"palette_only_recolors.csv",recolor_rows,
          ["reason","role","identity","delete_path","keep_path","delete_source","keep_source","structural_hash"])
write_csv(OUT/"custom_multi_design_approval_candidates.csv",multi,
          ["identity","design_option","source","bucket","front_path","structural_hash","exact_hash","action"])
write_csv(OUT/"ds_ready_front_design_manifest.csv",master,
          ["identity","source","bucket","front_path","structural_hash","exact_hash","multi_design_for_approval"])
(OUT/"decode_failures.txt").write_text(("\n".join(decode_fail)+"\n") if decode_fail else "")

summary={
    "ds_ready_image_files_scanned":len(assets),
    "decoded_failures":len(decode_fail),
    "front_sprite_files_found":len(fronts),
    "exact_duplicate_component_files":len(exact_rows),
    "palette_only_recolor_component_files":len(recolor_rows),
    "unique_front_visual_designs_after_exact_and_recolor_dedup":len(canonical),
    "semantic_identity_count_among_unique_front_designs":len(by_identity),
    "custom_identities_with_multiple_genuinely_different_designs":len(multi_ids),
    "custom_design_options_preserved_for_approval":len(multi),
    "count_definition":"One Pokemon sprite design is one unique non-shiny FRONT visual after exact duplicates and palette-only recolors are collapsed. Genuinely different designs for the same custom identity are all retained and counted.",
    "policy":[
        "Normal and shiny roles are never compared against each other.",
        "No files are deleted by this audit.",
        "Exact duplicates and palette-only recolors are isolated as cleanup candidates.",
        "Different custom-mon designs are preserved for the approval sheet."
    ]
}
(OUT/"ds_ready_dedup_summary.json").write_text(json.dumps(summary,indent=2)+"\n")
print(json.dumps(summary,indent=2))
