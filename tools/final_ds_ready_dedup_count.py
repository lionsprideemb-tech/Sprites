from pathlib import Path
from PIL import Image
import collections, csv, hashlib, json, re, urllib.request

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

# Official forms are protected from recolor collapse.
official=set()
api_ok=False
base_species=set()
official_megas=set()
forced_custom=set()

base_file=ROOT/"cleanup-audit"/"required_vanilla_species.txt"
if base_file.exists():
    base_species={norm(x) for x in base_file.read_text().splitlines() if x.strip()}

mega_file=ROOT/"cleanup-audit"/"required_mega_forms.txt"
if mega_file.exists():
    official_megas={norm(x) for x in mega_file.read_text().splitlines() if x.strip()}

replacement_summary=ROOT/"replacement-map"/"replacement_manifest_summary.json"
if replacement_summary.exists():
    try:
        d=json.loads(replacement_summary.read_text())
        forced_custom={norm(x.get("key","")) for x in d.get("mercury_custom_mega_priority",[]) if x.get("key")}
    except Exception:
        pass

try:
    with urllib.request.urlopen("https://pokeapi.co/api/v2/pokemon?limit=10000",timeout=60) as r:
        data=json.load(r)
    official={norm(x["name"]) for x in data.get("results",[])}
    api_ok=True
except Exception:
    core=ROOT/"packs"/"DrPrettyman_DS_64x64"/"sprites-processed"/"front"
    if core.exists():
        official={norm(p.stem) for p in core.iterdir() if p.is_file()}

official |= base_species
official |= (official_megas - forced_custom)

CUSTOM_TOKENS={"redux","delta","apex","nightmare","fakemon"}

def official_lookup_name(ident):
    x=ident
    for suffix in ("-male","-female"):
        if x.endswith(suffix):
            x=x[:-len(suffix)]
    return x

def is_official_identity(ident):
    lookup=official_lookup_name(ident)
    if lookup in forced_custom:
        return False
    if any(("-"+t) in lookup or lookup.startswith(t+"-") for t in CUSTOM_TOKENS):
        return False
    return lookup in official

def role(p):
    stem=norm(p.stem); parts=[norm(x) for x in p.parts]; joined="/".join(parts)
    if "icon" in stem or "/icon/" in joined or "/icons/" in joined: return "icon"
    shiny=("shiny" in stem or any("shiny" in x for x in parts))
    # PrincessPhoenix uses a trailing S for shiny companions (e.g. FiromenisFS
    # beside FiromenisF, PythonovaS beside Pythonova, *B4S beside *B4).
    # Recognize it only when the non-S companion physically exists.
    if "festival-princessphoenix" in parts and p.stem.lower().endswith("s"):
        mate=p.with_name(p.stem[:-1]+p.suffix)
        if mate.exists(): shiny=True
    # Festival Misc uses several old-school shiny filename conventions:
    # MawileS/Mawile, KangaSF/KangaF, and 479s_6/479_6 (same for backs).
    if "festival-misc" in parts:
        raw=p.stem
        candidates=[]
        if re.search(r"(?i)sf$",raw): candidates.append(re.sub(r"(?i)sf$","F",raw))
        if re.search(r"(?i)sb$",raw): candidates.append(re.sub(r"(?i)sb$","B",raw))
        if re.search(r"(?i)s(?=_\d+$)",raw): candidates.append(re.sub(r"(?i)s(?=_\d+$)","",raw))
        if raw.lower().endswith("s"): candidates.append(raw[:-1])
        if any(p.with_name(x+p.suffix).exists() for x in candidates): shiny=True
    back=("back" in stem or any(
        x in {"back","backs","backsprite","backsprites","back-shiny"}
        or "backsprite" in x or x.endswith("-backs")
        for x in parts
    ))
    front=("front" in stem or any(
        x in {"front","fronts","frontsprite","frontsprites","front-shiny"}
        or "frontsprite" in x or x.endswith("-fronts")
        for x in parts
    ))
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
    parent_norm=norm(p.parent.name)
    if (
        parent_norm in {"front","back","front-shiny","back-shiny","icon","icons","fronts","backs","frontsprites","backsprites"}
        or "frontsprite" in parent_norm or "backsprite" in parent_norm
        or parent_norm.endswith("-fronts") or parent_norm.endswith("-backs")
    ):
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
    # Native DS artwork is preferred over mechanical GBA conversion when the identity matches.
    if a["source"]=="DrPrettyman_DS_64x64": tier=0
    elif a["source"]=="HG_Engine_DS_Sprites": tier=1
    elif a["bucket"] in {"NATIVE_PACK","NATIVE_HACK"}: tier=2
    else: tier=3
    return (tier,len(a["path"]),a["path"])

BASELINE_OFFICIAL_SOURCES={
    "DrPrettyman_DS_64x64",
    "HG_Engine_DS_Sprites",
    "DS_Styled_Gen5_8",
    "Gen7_DS_Backsprites",
    "Shiny_Icons_Gen1_9",
    "Elite_Redux_Bulk",
}

def asset_is_official(ident,src):
    # A canon-named design from a known baseline source is ordinary vanilla art.
    # The same canon name coming from a custom-form/fakemon source is preserved
    # as a review candidate unless it collapses as an exact/recolor duplicate.
    return src in BASELINE_OFFICIAL_SOURCES and is_official_identity(ident)

assets=[]; decode_fail=[]
for root,bucket in ROOTS:
    if not root.exists(): continue
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in EXTS: continue
        ps="/"+p.as_posix().replace("\\","/")+"/"
        if any(x in ps for x in EXCLUDE): continue
        # This contributor ships both Gen-3 and native DS-style Gen-4/5 views.
        # For the DS approval master, never pair a Gen-3 front with a Gen-4 back.
        lowps=ps.lower()
        if "/festival_princessphoenix/" in lowps and (
            "/gen 3 frontsprites/" in lowps or "/gen 3 backsprites/" in lowps
        ):
            continue
        sig=image_signatures(p)
        if not sig:
            decode_fail.append(p.as_posix()); continue
        exact,struct,w,h,colors=sig
        comp=role(p)
        ident=identity(p,comp)
        src=source(p,root)
        assets.append({
            "path":p.as_posix(),"bucket":bucket,"source":src,
            "role":comp,"identity":ident,"official_identity":asset_is_official(ident,src),
            "semantic_official_name":is_official_identity(ident),
            "exact_hash":exact,"structural_hash":struct,
            "width":w,"height":h,"colors":colors
        })

# Exact duplicates: same component and same pixels. Keep best source.
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

# Palette-only recolors are only cleanup candidates when at least one side is custom.
# Official-vs-official palette forms are protected. Normal and shiny never mix.
recolor_rows=[]; recolor_drop=set()
by_struct=collections.defaultdict(list)
for a in assets:
    if a["path"] in exact_drop or a["role"] not in {"front","back","icon"}: continue
    by_struct[(a["role"],a["structural_hash"])].append(a)

for (comp,h),items in by_struct.items():
    if len(items)<2 or len({x["exact_hash"] for x in items})<2: continue
    official_items=[x for x in items if x["official_identity"]]
    custom_items=[x for x in items if not x["official_identity"]]
    if not custom_items:
        continue
    # If an official design exists, all custom palette-only variants are cleanup candidates.
    # Otherwise keep the best custom source and collapse the other pure recolors.
    keep=min(official_items,key=quality) if official_items else min(custom_items,key=quality)
    candidates=custom_items if official_items else [x for x in custom_items if x["path"]!=keep["path"]]
    for a in candidates:
        if a["path"]==keep["path"]: continue
        recolor_drop.add(a["path"])
        recolor_rows.append({
            "reason":"CUSTOM_PALETTE_ONLY_RECOLOR","role":comp,"identity":a["identity"],
            "delete_path":a["path"],"keep_path":keep["path"],
            "delete_source":a["source"],"keep_source":keep["source"],"structural_hash":h
        })

fronts=[a for a in assets if a["role"]=="front" and a["path"] not in exact_drop and a["path"] not in recolor_drop]

# Build final front candidates:
# - one preferred front per official semantic identity;
# - all genuinely different structural designs per custom identity.
official_fronts=collections.defaultdict(list)
custom_fronts=collections.defaultdict(list)
for a in fronts:
    (official_fronts if a["official_identity"] else custom_fronts)[a["identity"]].append(a)

canonical=[]
for ident,items in official_fronts.items():
    canonical.append(min(items,key=quality))

multi=[]; multi_ids=set()
for ident,items in custom_fronts.items():
    by_visual=collections.defaultdict(list)
    for a in items: by_visual[a["structural_hash"]].append(a)
    kept=[min(group,key=quality) for group in by_visual.values()]
    kept=sorted(kept,key=quality)
    if len(kept)>1:
        multi_ids.add(ident)
        for n,a in enumerate(kept,1):
            multi.append({
                "identity":ident,"design_option":n,"source":a["source"],"bucket":a["bucket"],
                "front_path":a["path"],"structural_hash":a["structural_hash"],
                "exact_hash":a["exact_hash"],"action":"KEEP_FOR_APPROVAL_SHEET"
            })
    canonical.extend(kept)

canonical=sorted(canonical,key=lambda a:(a["identity"],quality(a)))

# Pair each chosen front with a normal back sprite from the same source/identity.
back_index=collections.defaultdict(list)
for a in assets:
    if a["role"]=="back" and a["path"] not in exact_drop and a["path"] not in recolor_drop:
        back_index[(a["source"],a["bucket"],a["identity"])].append(a)

def paired_back(a):
    items=back_index.get((a["source"],a["bucket"],a["identity"]),[])
    if items:
        return min(items,key=quality)["path"]
    # Cross-source fallback is allowed only when another source carries the
    # exact same FRONT design (same structural hash). This prevents pairing a
    # custom front with an unrelated vanilla/custom back merely because names match.
    same_design_fronts=[
        x for x in assets
        if x["role"]=="front" and x["identity"]==a["identity"]
        and x["structural_hash"]==a["structural_hash"] and x["path"]!=a["path"]
    ]
    fallback=[]
    for other in same_design_fronts:
        fallback.extend(back_index.get((other["source"],other["bucket"],other["identity"]),[]))
    fallback=[x for x in fallback if x["path"] not in exact_drop and x["path"] not in recolor_drop]
    return min(fallback,key=quality)["path"] if fallback else ""

master=[{
    "identity":a["identity"],"is_official":a["official_identity"],
    "semantic_official_name":a.get("semantic_official_name",False),
    "source":a["source"],"bucket":a["bucket"],
    "front_path":a["path"],"back_path":paired_back(a),
    "structural_hash":a["structural_hash"],
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
          ["identity","is_official","semantic_official_name","source","bucket","front_path","back_path","structural_hash","exact_hash","multi_design_for_approval"])
(OUT/"decode_failures.txt").write_text(("\n".join(decode_fail)+"\n") if decode_fail else "")

official_kept=sum(1 for x in master if x["is_official"])
custom_kept=sum(1 for x in master if not x["is_official"])
custom_identity_count=len(custom_fronts)
summary={
    "pokeapi_official_form_index_ok":api_ok,
    "official_form_names_indexed":len(official),
    "ds_ready_image_files_scanned":len(assets),
    "decoded_failures":len(decode_fail),
    "normal_front_source_files_scanned":sum(1 for a in assets if a["role"]=="front"),
    "normal_front_sprite_files_after_component_cleanup":len(fronts),
    "exact_duplicate_component_files":len(exact_rows),
    "front_exact_duplicate_files":sum(1 for x in exact_rows if x["role"]=="front"),
    "custom_palette_only_recolor_component_files":len(recolor_rows),
    "front_custom_palette_only_recolor_files":sum(1 for x in recolor_rows if x["role"]=="front"),
    "official_semantic_front_entries_kept":official_kept,
    "custom_semantic_identities":custom_identity_count,
    "custom_identities_with_multiple_genuinely_different_designs":len(multi_ids),
    "custom_design_options_preserved_for_approval":len(multi),
    "custom_designs_with_back_sprite":sum(1 for x in master if (not x["is_official"]) and x["back_path"]),
    "custom_designs_missing_back_sprite":sum(1 for x in master if (not x["is_official"]) and not x["back_path"]),
    "total_pokemon_form_sprite_designs_before_approval":len(master),
    "official_plus_custom_breakdown":{"official":official_kept,"custom_design_candidates":custom_kept},
    "count_definition":"Count is one preferred normal-front sprite per official form identity plus every genuinely different custom design candidate. Exact duplicates and custom palette-only recolors are excluded. Multiple genuinely different designs for the same custom mon are retained for approval.",
    "policy":[
        "Normal and shiny roles are never compared against each other.",
        "Official form identities are protected from palette-recolor collapse.",
        "Native DS artwork is preferred over mechanically converted GBA art when the semantic identity is the same.",
        "No files are deleted by this audit; duplicate/recolor files are isolated in reports.",
        "Different custom-mon designs are preserved for the approval sheet."
    ]
}
(OUT/"ds_ready_dedup_summary.json").write_text(json.dumps(summary,indent=2)+"\n")
print(json.dumps(summary,indent=2))
