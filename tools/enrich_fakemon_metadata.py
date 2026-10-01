from pathlib import Path
import csv,json,re,collections,urllib.request

ROOT=Path("DS_CUSTOM_LIBRARY")
MASTER=ROOT/"DS_READY_MASTER"
MANIFEST=MASTER/"ds_ready_front_design_manifest.csv"
TYPEMAP=MASTER/"mercury_name_type_map.json"
OUT=MASTER/"fakemon_enriched_metadata.json"
REPORT=MASTER/"fakemon_enrichment_report.csv"
EXCLUDED=MASTER/"fakemon_excluded_incomplete.csv"

def norm(s):
    return re.sub(r"-+","-",re.sub(r"[^a-z0-9]+","-",str(s or "").lower())).strip("-")

def read_csv(p):
    with p.open(newline="",encoding="utf-8-sig",errors="replace") as f:
        return list(csv.DictReader(f))

rows=read_csv(MANIFEST)
type_map={}
if TYPEMAP.exists():
    try:type_map=json.loads(TYPEMAP.read_text()).get("entries",{})
    except:pass

# Build a source-file index for robust back matching.
image_ext={".png",".gif",".bmp",".jpg",".jpeg",".webp"}
all_images=[]
for base in [ROOT/"packs",ROOT/"hack-packs",ROOT/"converted"]:
    if not base.exists():continue
    for p in base.rglob("*"):
        if p.is_file() and p.suffix.lower() in image_ext:
            ps=p.as_posix()
            low=ps.lower()
            role="back" if any(x in low for x in ["/back/","/backs/","back.","_back","/backsprite","/backsprites/"]) else ("front" if any(x in low for x in ["/front/","/fronts/","front.","_front","/frontsprite","/frontsprites/"]) else "unknown")
            all_images.append((p,role))

def source_of(path):
    parts=Path(path).parts
    for anchor in ("packs","hack-packs","converted"):
        if anchor in parts:
            i=parts.index(anchor)
            return parts[i+1] if i+1<len(parts) else ""
    return ""

# Parse text metadata embedded in packs (Essentials/PBS-style plus loose CSV/JSON hints).
meta={}
edges=collections.defaultdict(set)
text_ext={".txt",".pbs",".ini",".cfg",".csv",".json",".md"}
for base in [ROOT/"packs",ROOT/"hack-packs",ROOT/"converted"]:
    if not base.exists():continue
    for p in base.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in text_ext or p.stat().st_size>4_000_000:continue
        try:txt=p.read_text(encoding="utf-8",errors="ignore")
        except:continue
        src=source_of(p.as_posix())
        # Essentials sections: [SPECIES]
        secpat=list(re.finditer(r"(?m)^\s*\[([^\]\r\n]+)\]\s*$",txt))
        for i,m in enumerate(secpat):
            name=m.group(1).strip(); key=norm(name)
            if not key:continue
            chunk=txt[m.end():secpat[i+1].start() if i+1<len(secpat) else min(len(txt),m.end()+6000)]
            rec=meta.setdefault((src,key),{"name":name,"source":src})
            mt=re.search(r"(?mi)^\s*(?:Types?|Type1)\s*=\s*([^\r\n#;]+)",chunk)
            if mt:
                vals=[x.strip().title() for x in re.split(r"[,/]",mt.group(1)) if x.strip()]
                if vals:rec["type1"]=vals[0]
                if len(vals)>1:rec["type2"]=vals[1]
            mt2=re.search(r"(?mi)^\s*Type2\s*=\s*([^\r\n#;]+)",chunk)
            if mt2 and mt2.group(1).strip():rec["type2"]=mt2.group(1).strip().title()
            ev=re.search(r"(?mi)^\s*Evolutions?\s*=\s*([^\r\n#]+)",chunk)
            if ev:
                toks=[x.strip() for x in ev.group(1).split(",")]
                for j in range(0,len(toks),3):
                    if j<len(toks) and toks[j]:
                        child=norm(toks[j]); edges[key].add(child);edges[child].add(key)
        # Generic "Name, Type1, Type2" CSV-like rows are intentionally not trusted unless headers exist.
        if p.suffix.lower()==".csv":
            try:
                with p.open(newline="",encoding="utf-8-sig",errors="ignore") as f:
                    cr=csv.DictReader(f)
                    if cr.fieldnames:
                        fns={norm(x):x for x in cr.fieldnames}
                        ncol=next((fns[k] for k in ("species","name","pokemon","pokemon-name") if k in fns),None)
                        t1col=next((fns[k] for k in ("type1","type-1","primary-type","type") if k in fns),None)
                        t2col=next((fns[k] for k in ("type2","type-2","secondary-type") if k in fns),None)
                        fcol=next((fns[k] for k in ("family","evolution-family","breeding-base-family") if k in fns),None)
                        if ncol and t1col:
                            for rr in cr:
                                nm=(rr.get(ncol) or "").strip(); k=norm(nm)
                                if not k:continue
                                rec=meta.setdefault((src,k),{"name":nm,"source":src})
                                if rr.get(t1col):rec["type1"]=rr[t1col].strip().title()
                                if t2col and rr.get(t2col):rec["type2"]=rr[t2col].strip().title()
                                if fcol and rr.get(fcol):rec["family"]=rr[fcol].strip()
            except:pass

# PokeAPI cache used for numbered filenames and official-family fallback.
poke_cache={}
chain_cache={}
def poke_species(token):
    if token in poke_cache:return poke_cache[token]
    try:
        with urllib.request.urlopen("https://pokeapi.co/api/v2/pokemon-species/"+str(token),timeout=20) as r:d=json.load(r)
        poke_cache[token]=d;return d
    except:
        poke_cache[token]=None;return None

def poke_pokemon(token):
    try:
        with urllib.request.urlopen("https://pokeapi.co/api/v2/pokemon/"+str(token),timeout=20) as r:return json.load(r)
    except:return None

def chain_members(url):
    if url in chain_cache:return chain_cache[url]
    try:
        with urllib.request.urlopen(url,timeout=20) as r:d=json.load(r)
        out=[]
        def walk(n):
            out.append(n["species"]["name"])
            for e in n.get("evolves_to",[]):walk(e)
        walk(d["chain"]);chain_cache[url]=out;return out
    except:return []

def numeric_dex(identity):
    m=re.match(r"^0*([0-9]{1,4})(?:[-_].*)?$",identity)
    if not m:return None
    n=int(m.group(1))
    return n if 1<=n<=1025 else None

def likely_back(front_path,identity,source):
    # First: manifest's paired back.
    rr=next((x for x in rows if x.get("front_path")==front_path),None)
    if rr and rr.get("back_path"):return rr["back_path"]
    fid=norm(identity)
    num=numeric_dex(identity)
    cand=[]
    for p,role in all_images:
        if role!="back":continue
        ps=p.as_posix()
        if source and source_of(ps)!=source:continue
        stem=norm(p.stem)
        parent=norm(p.parent.name)
        score=0
        if stem==fid:score+=100
        if fid and fid in norm(ps):score+=40
        if num is not None:
            nums=re.findall(r"(?<!\d)(\d{1,4})(?!\d)",p.name)
            if any(int(x)==num for x in nums):score+=70
        # Match same basename with front/back token removed.
        fbase=norm(Path(front_path).stem.replace("front",""))
        bbase=norm(p.stem.replace("back",""))
        if fbase and fbase==bbase:score+=90
        if score:cand.append((score,len(ps),ps))
    if cand:
        cand.sort(key=lambda x:(-x[0],x[1],x[2]))
        if cand[0][0]>=70:return cand[0][2]
    return ""

# Connected-component family for custom source metadata.
def custom_family(key):
    seen=set();stack=[key]
    while stack:
        x=stack.pop()
        if x in seen:continue
        seen.add(x);stack.extend(edges.get(x,()))
    return seen

enriched={}
report=[]
for r in rows:
    if r.get("is_official")!="False":continue
    ident=r["identity"];src=r["source"];key=norm(ident)
    out={"identity":ident,"source":src,"front_path":r.get("front_path",""),"back_path":r.get("back_path","")}
    confidence=[]
    # Mercury master first.
    mr=type_map.get(key)
    if not mr:
        # common identity fallbacks
        for k in [key.replace("-mega-z","-mega-z"),key.replace("-delta","-redux"),key.replace("-redux","")]:
            if k in type_map:mr=type_map[k];break
    if mr:
        out["name"]=mr.get("name") or ident
        out["type1"]=mr.get("type1") or ""
        out["type2"]=mr.get("type2") or ""
        out["family"]=re.sub(r"\s+family$","",mr.get("family") or "",flags=re.I)
        confidence.append("MERCURY_MASTER")
    # Source metadata next.
    sm=meta.get((src,key))
    if not sm:
        # strip familiar form suffixes
        base=re.sub(r"-(mega(?:-[xyz])?|redux|delta|male|female)$","",key)
        sm=meta.get((src,base))
    if sm:
        out.setdefault("name",sm.get("name") or ident)
        if not out.get("type1"):out["type1"]=sm.get("type1","")
        if not out.get("type2"):out["type2"]=sm.get("type2","")
        if not out.get("family"):out["family"]=sm.get("family","")
        confidence.append("SOURCE_METADATA")
    # Numbered source IDs often encode National Dex species.
    dex=numeric_dex(ident)
    if dex:
        sp=poke_species(dex)
        pk=poke_pokemon(dex)
        if sp:
            pname=sp["name"]
            out.setdefault("name",pname.replace("-"," ").title()+" Variant")
            if not out.get("family"):
                members=chain_members(sp["evolution_chain"]["url"])
                out["family"]=" → ".join(x.replace("-"," ").title() for x in members)
            confidence.append("DEX_ID")
        if pk and not out.get("type1"):
            types=sorted(pk["types"],key=lambda x:x["slot"])
            if types:
                out["type1"]=types[0]["type"]["name"].title()
                out["type2"]=types[1]["type"]["name"].title() if len(types)>1 else ""
                confidence.append("BASE_TYPE_PROPOSAL")
    # Named official-base/custom-form fallback.
    if not out.get("type1"):
        base=re.sub(r"-(mega(?:-[xyz])?|redux|delta|male|female|hisuian|galarian|alolan|paldean)$","",key)
        pk=poke_pokemon(base)
        sp=poke_species(base)
        if pk:
            types=sorted(pk["types"],key=lambda x:x["slot"])
            out["type1"]=types[0]["type"]["name"].title() if types else ""
            out["type2"]=types[1]["type"]["name"].title() if len(types)>1 else ""
            confidence.append("BASE_TYPE_PROPOSAL")
        if sp and not out.get("family"):
            members=chain_members(sp["evolution_chain"]["url"])
            if members:out["family"]=" → ".join(x.replace("-"," ").title() for x in members)
    # Custom source evolution graph.
    if not out.get("family") and key in edges:
        fam=sorted(custom_family(key))
        out["family"]=" → ".join(x.replace("-"," ").title() for x in fam)
        confidence.append("SOURCE_EVOLUTION_GRAPH")
    # No known family = standalone; explicit is better than blank.
    if not out.get("family"):
        out["family"]="Standalone / no evolution data found"
        confidence.append("STANDALONE_PROPOSAL")
    if not out.get("name"):
        out["name"]=ident.replace("-"," ").title()
        confidence.append("SOURCE_NAME")
    if not out.get("type1"):
        out["type1"]="TBD"
        out["type2"]=""
        confidence.append("TYPE_NEEDS_VISUAL_PITCH")
    if not out.get("back_path"):
        out["back_path"]=likely_back(out["front_path"],ident,src)
        if out["back_path"]:confidence.append("BACK_MATCH_RECOVERED")
    out["confidence"]=";".join(confidence)
    out["ready_for_approval"]=bool(out.get("name") and out.get("type1")!="TBD" and out.get("family") and out.get("back_path"))
    enriched[ident+"|"+r.get("structural_hash","")]=out
    report.append(out)

OUT.write_text(json.dumps({"generated":"2026-10-01","entries":enriched},indent=2)+"\n")
with REPORT.open("w",newline="",encoding="utf-8") as f:
    fields=["identity","name","type1","type2","family","source","front_path","back_path","confidence","ready_for_approval"]
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
    for x in report:w.writerow({k:x.get(k,"") for k in fields})

with EXCLUDED.open("w",newline="",encoding="utf-8") as f:
    fields=["identity","name","type1","type2","family","source","front_path","back_path","missing"]
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
    for x in report:
        if x["ready_for_approval"]: continue
        missing=[]
        if not x.get("name"): missing.append("name")
        if not x.get("type1") or x.get("type1")=="TBD": missing.append("type")
        if not x.get("family"): missing.append("family")
        if not x.get("back_path"): missing.append("back sprite")
        row={k:x.get(k,"") for k in fields}
        row["missing"]="; ".join(missing)
        w.writerow(row)

summary={
 "custom_entries":len(report),
 "ready":sum(1 for x in report if x["ready_for_approval"]),
 "missing_type":sum(1 for x in report if x["type1"]=="TBD"),
 "missing_back":sum(1 for x in report if not x.get("back_path")),
 "standalone_proposals":sum(1 for x in report if x.get("family")=="Standalone / no evolution data found"),
 "source_metadata_records":len(meta),
 "excluded_from_approval":sum(1 for x in report if not x["ready_for_approval"]),
 "approval_policy":"Only fully identified entries with name, type, family placement, front sprite and back sprite are admitted to approval.",
}
(MASTER/"fakemon_enrichment_summary.json").write_text(json.dumps(summary,indent=2)+"\n")
print(json.dumps(summary,indent=2))
