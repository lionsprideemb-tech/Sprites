from pathlib import Path
import csv,json,re,collections,urllib.request

ROOT=Path("DS_CUSTOM_LIBRARY")
MASTER=ROOT/"DS_READY_MASTER"
MANIFEST=MASTER/"ds_ready_front_design_manifest.csv"
TYPEMAP=MASTER/"mercury_name_type_map.json"
OUT=MASTER/"fakemon_enriched_metadata.json"
REPORT=MASTER/"fakemon_enrichment_report.csv"
EXCLUDED=MASTER/"fakemon_excluded_incomplete.csv"
EXTERNAL=MASTER/"external_fakemon_metadata.json"

# Local official-name index so recovery does not depend on PokeAPI availability.
# DrPrettyman is our broad native DS baseline and already contains the official
# species/forms we want to suppress from the custom-review pool.
LOCAL_OFFICIAL_NAMES=set()
for _p in [
    ROOT/"cleanup-audit"/"required_vanilla_species.txt",
    ROOT/"cleanup-audit"/"required_mega_forms.txt",
]:
    if _p.exists():
        for _x in _p.read_text(encoding="utf-8",errors="ignore").splitlines():
            if _x.strip(): LOCAL_OFFICIAL_NAMES.add(_x.strip())

def norm(s):
    return re.sub(r"-+","-",re.sub(r"[^a-z0-9]+","-",str(s or "").lower())).strip("-")

LOCAL_OFFICIAL_NAMES={norm(x) for x in LOCAL_OFFICIAL_NAMES}
_native_front=ROOT/"packs"/"DrPrettyman_DS_64x64"/"sprites-processed"/"front"
if _native_front.exists():
    LOCAL_OFFICIAL_NAMES |= {norm(p.stem) for p in _native_front.iterdir() if p.is_file()}

def official_aliases(ident):
    x=norm(ident)
    out={x}
    for suffix in ("-male","-female","-m","-f"):
        if x.endswith(suffix):
            out.add(x[:-len(suffix)])
    more=set(out)
    for y in list(out):
        if y.startswith("mega-"):
            bits=y.split("-")
            if len(bits)>=2:
                more.add("-".join(bits[1:])+"-mega")
        if y.endswith("-mega"):
            more.add("mega-"+y[:-5])
        m=re.match(r"^mega-(.+)-([xyz])$",y)
        if m:
            more.add(f"{m.group(1)}-mega-{m.group(2)}")
        m=re.match(r"^(.+)-mega-([xyz])$",y)
        if m:
            more.add(f"mega-{m.group(1)}-{m.group(2)}")
    return more

NONVANILLA_TYPE_REPLACEMENTS={"Sound":"Normal"}
def vanilla_type(t):
    t=str(t or "").strip().title()
    return NONVANILLA_TYPE_REPLACEMENTS.get(t,t)

CANON_TYPES={"Normal","Fire","Water","Electric","Grass","Ice","Fighting","Poison","Ground","Flying","Psychic","Bug","Rock","Ghost","Dragon","Dark","Steel","Fairy"}

def proposed_types(identity,name="",family=""):
    """Deterministic Mercury fallback using only canon types.
    Source/Mercury metadata always wins; this only fills otherwise-blank custom entries."""
    s=" ".join([str(identity or ""),str(name or ""),str(family or "")]).lower()
    rules=[
        ("Fire",["fire","flame","ember","lava","volcan","burn","blaze","sizzle","furn","char"]),
        ("Water",["water","aqua","sea","ocean","rain","river","fish","trout","carp","drip","damp","surf"]),
        ("Electric",["electric","volt","spark","thunder","shock","charge","battery","storm"]),
        ("Grass",["grass","leaf","plant","flora","flower","wood","tree","moss","sprout","vine"]),
        ("Ice",["ice","frost","snow","chill","cryo","glacier"]),
        ("Fighting",["fight","punch","kick","brawl","martial","warrior","club"]),
        ("Poison",["poison","toxic","venom","acid","sludge","contam"]),
        ("Ground",["ground","sand","dune","earth","mud","burrow"]),
        ("Flying",["flying","bird","wing","avian","raptor","hawk"]),
        ("Psychic",["psychic","mind","dream","psy","mystic"]),
        ("Bug",["bug","bee","moth","spider","web","ant","larva"]),
        ("Rock",["rock","stone","crag","ore","geo","fossil"]),
        ("Ghost",["ghost","spirit","haunt","phantom","spect","wraith"]),
        ("Dragon",["dragon","drake","wyrm","serpent"]),
        ("Dark",["dark","night","shadow","evil","imp","demon"]),
        ("Steel",["steel","metal","iron","gear","mech","blade"]),
        ("Fairy",["fairy","fae","fey","pixie","magic","charm","sprite"]),
    ]
    hits=[]
    for typ,words in rules:
        if any(w in s for w in words):
            hits.append(typ)
    if not hits:
        return ("Normal","")
    return (hits[0], hits[1] if len(hits)>1 and hits[1]!=hits[0] else "")

OFFICIAL_POKEMON_NAMES=set()
try:
    with urllib.request.urlopen("https://pokeapi.co/api/v2/pokemon?limit=100000",timeout=30) as _r:
        _d=json.load(_r)
    OFFICIAL_POKEMON_NAMES={norm(x.get("name","")) for x in _d.get("results",[]) if x.get("name")}
except Exception:
    OFFICIAL_POKEMON_NAMES=set()

def _official_name_candidate(ident):
    ident=norm(ident)
    if ident in OFFICIAL_POKEMON_NAMES:
        return True
    # Gendered sprite folders and harmless display-role suffixes are still the
    # same official design, not Mercury review candidates.
    for suffix in ("-male","-female","-normal","-default","-front","-back"):
        if ident.endswith(suffix) and ident[:-len(suffix)] in OFFICIAL_POKEMON_NAMES:
            return True
    return False

def looks_like_official_variant(ident):
    x=norm(ident)
    # Official regional / alternate-form naming used by donor packs.
    official_tokens=[
        "-alolan","-galarian","-hisuian","-paldean",
        "-east-sea","-west-sea",
        "-ice-rider","-shadow-rider",
        "-dusk-mane","-dawn-wings",
        "-original-color","-eternal-flower",
        "-whitestriped",
    ]
    if any(t in x for t in official_tokens):
        # Custom Mega/evolved derivatives of an official form remain candidates.
        if x.endswith("-mega") or "-mega-" in x:
            return False
        return True
    if x in {
        "wormadam-sandy-cloak","wormadam-trash-cloak",
        "burmy-sandy-cloak","burmy-trash-cloak",
        "maushold-four","maushold-three",
        "unown-emark","unown-qmark",
    }:
        return True
    if x.startswith("alcremie-") and "mega" not in x:
        return True
    return False

def plain_official_row(r,type_map):
    """Exclude ordinary official/native art while preserving true custom-source
    redesigns that happen to reuse a vanilla Pokémon name."""
    flag=str(r.get("is_official","")).strip().lower()
    if flag in {"true","1","yes"}:
        return True

    ident=norm(r.get("identity",""))
    src=r.get("source","")
    baseline_sources={
        "DrPrettyman_DS_64x64","HG_Engine_DS_Sprites","DS_Styled_Gen5_8",
        "Gen7_DS_Backsprites","Shiny_Icons_Gen1_9"
    }
    if src in baseline_sources or src.startswith("HGSS_Project_Unique_"):
        return True

    # Elite Redux includes a large vanilla/form sprite layer alongside its
    # actual custom content. Remove ordinary official forms but keep Redux,
    # custom Mega, EX, trainer, paradox, and fakemon identities.
    aliases=official_aliases(ident)
    if src=="Elite_Redux_Bulk":
        if looks_like_official_variant(ident):
            return True
        if any(a in LOCAL_OFFICIAL_NAMES for a in aliases):
            return True

    # A few miscellaneous packs carry plain vanilla reference sprites alongside
    # the custom art; these are not review candidates.
    if src=="Festival_Misc" and ident in {"mawile","sableye"}:
        return True

    if flag in {"false","0","no"}:
        return False

    mr=type_map.get(ident) or {}
    cat=str(mr.get("category","")).upper()
    return cat in {"CANON","OFFICIAL/CANON","OFFICIAL REGIONAL","OFFICIAL FORM"}

def read_csv(p):
    with p.open(newline="",encoding="utf-8-sig",errors="replace") as f:
        return list(csv.DictReader(f))

rows=read_csv(MANIFEST)
type_map={}
if TYPEMAP.exists():
    try:type_map=json.loads(TYPEMAP.read_text()).get("entries",{})
    except:pass

external_records={}
if EXTERNAL.exists():
    try: external_records=json.loads(EXTERNAL.read_text()).get("records",{})
    except: external_records={}

# Build a source-file index for robust back matching.
image_ext={".png",".gif",".bmp",".jpg",".jpeg",".webp"}
all_images=[]
for base in [ROOT/"packs",ROOT/"hack-packs",ROOT/"converted"]:
    if not base.exists():continue
    for p in base.rglob("*"):
        if p.is_file() and p.suffix.lower() in image_ext:
            ps=p.as_posix()
            low=ps.lower()
            pparts=[norm(x) for x in p.parts]
            back_folder=any(
                x in {"back","backs","backsprite","backsprites"}
                or "backsprite" in x or x.endswith("-backs")
                for x in pparts
            )
            front_folder=any(
                x in {"front","fronts","frontsprite","frontsprites"}
                or "frontsprite" in x or x.endswith("-fronts")
                for x in pparts
            )
            role="back" if (
                back_folder or any(x in low for x in ["/back/","/backs/","back.","_back"])
            ) else ("front" if (
                front_folder or any(x in low for x in ["/front/","/fronts/","front.","_front"])
            ) else "unknown")
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
children=collections.defaultdict(set)
parents=collections.defaultdict(set)
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
            section_name=m.group(1).strip()
            chunk=txt[m.end():secpat[i+1].start() if i+1<len(secpat) else min(len(txt),m.end()+6000)]

            # Many Essentials fakemon packs use repeated [X] sections and put
            # the real identity in InternalName/Name. Treat that identity as
            # authoritative instead of collapsing every custom species to "x".
            im=re.search(r"(?mi)^\s*InternalName\s*=\s*([^\r\n#;]+)",chunk)
            nm=re.search(r"(?mi)^\s*Name\s*=\s*([^\r\n#;]+)",chunk)
            fm=re.search(r"(?mi)^\s*FormName\s*=\s*([^\r\n#;]+)",chunk)
            identity=(im.group(1).strip() if im else section_name)
            key=norm(identity)
            if not key:continue
            display=(nm.group(1).strip() if nm else section_name)
            if fm and "," in section_name and not nm:
                display=(fm.group(1).strip()+" "+section_name.split(",")[0].strip()).strip()
            rec=meta.setdefault((src,key),{"name":display,"source":src})

            # Alias the literal section key too (e.g. NOCTOWL,1).
            section_key=norm(section_name)
            if section_key and section_key!="x":
                meta.setdefault((src,section_key),rec)

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
                        child=norm(toks[j]); edges[key].add(child);edges[child].add(key);children[key].add(child);parents[child].add(key)
                        if section_key and section_key!=key:
                            edges[section_key].add(child);edges[child].add(section_key);children[section_key].add(child);parents[child].add(section_key)
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

def locality_parts(path):
    parts=list(Path(path).parts)
    role_tokens={"front","fronts","frontsprite","frontsprites","back","backs","backsprite","backsprites","front-shiny","back-shiny"}
    out=[]
    for part in parts:
        n=norm(part)
        if n in role_tokens or "frontsprite" in n or "backsprite" in n or n.endswith("-fronts") or n.endswith("-backs"):
            break
        out.append(n)
    return out

def common_prefix_len(a,b):
    n=0
    for x,y in zip(a,b):
        if x!=y: break
        n+=1
    return n

def sprite_stem_key(s,source=""):
    x=norm(Path(str(s)).stem)
    # Remove view/shiny markers only. Do not collapse species/form tokens.
    x=re.sub(r"-(?:front|back|backsprite|frontsprite|shiny)$","",x)
    x=re.sub(r"-(?:gen-?4|gen-?5|gen4|gen5)$","",x)
    x=re.sub(r"-(?:front|back)$","",x)
    # Festival Misc compact convention: 059_1f -> 059_1b.
    if source=="Festival_Misc":
        x=re.sub(r"(?<=\d)[fb]$","",x)
    # PrincessPhoenix convention: FiromenisF -> FiromenisB4/FiromenisB5.
    if source=="Festival_PrincessPhoenix":
        x=re.sub(r"(?:fs|f|b4s|b4|b5s|b5)$","",x)
    # Atsui sometimes appends _gen_4 to the matching back.
    if source=="Festival_Atsui":
        x=re.sub(r"-gen-?4$","",x)
    return x

def likely_back(front_path,identity,source):
    # A manifest pair is accepted only when the source-specific normalized
    # species/form key agrees. Same-source alone is NOT enough: the old audit
    # accidentally reused unrelated backs inside umbrella Fakemon packs.
    rr=next((x for x in rows if x.get("front_path")==front_path),None)
    if rr and rr.get("back_path") and source_of(rr["back_path"])==source:
        if sprite_stem_key(front_path,source)==sprite_stem_key(rr["back_path"],source):
            return rr["back_path"]

    fkey=sprite_stem_key(front_path,source)
    candidates=[]
    for p,role in all_images:
        if role!="back":continue
        ps=p.as_posix()
        if source_of(ps)!=source:continue
        bkey=sprite_stem_key(ps,source)
        if not fkey or bkey!=fkey:
            continue

        score=0
        # Prefer same contributor/subpack and Gen 4 back art for Platinum.
        score+=common_prefix_len(locality_parts(front_path),locality_parts(ps))*20
        if source=="Festival_PrincessPhoenix":
            n=norm(p.stem)
            if "b4" in n: score+=50
            if n.endswith("s"): score-=10
        if "shiny" in norm(p.stem): score-=100
        candidates.append((score,len(ps),ps))

    if candidates:
        candidates.sort(key=lambda x:(-x[0],x[1],x[2]))
        return candidates[0][2]
    return ""

# Connected-component family for custom source metadata.
def custom_family(key):
    seen=set();stack=[key]
    while stack:
        x=stack.pop()
        if x in seen:continue
        seen.add(x);stack.extend(edges.get(x,()))
    return seen

def custom_family_order(key):
    # Build only the lineage that actually leads into/out of this identity.
    # Do NOT use a whole undirected connected component: donor packs often have
    # several unrelated custom species that evolve into the same canon Pokémon,
    # which would incorrectly merge them into one giant "family".
    ancestors=set()
    stack=list(parents.get(key,set()))
    while stack:
        x=stack.pop()
        if x in ancestors:continue
        ancestors.add(x)
        stack.extend(parents.get(x,set()))
    descendants=set()
    stack=list(children.get(key,set()))
    while stack:
        x=stack.pop()
        if x in descendants:continue
        descendants.add(x)
        stack.extend(children.get(x,set()))
    fam=ancestors|{key}|descendants
    roots=sorted(x for x in fam if not (parents.get(x,set()) & fam))
    ordered=[];seen=set()
    def walk(x):
        if x in seen or x not in fam:return
        seen.add(x);ordered.append(x)
        for y in sorted(children.get(x,set()) & fam):
            walk(y)
    for r in roots:walk(r)
    if key not in seen:walk(key)
    for x in sorted(fam):
        if x not in seen:walk(x)
    return ordered

# Recover numbered alternate-form families (e.g. ODDISH_1 → GLOOM_1 → VILEPLUME_1)
# from the canonical evolution chain instead of alphabetically grouping source IDs.
numbered_form_family={}
numbered_type_fallback={}
numbered=[]
for rr in rows:
    if rr.get("is_official")!="False":continue
    ident=rr.get("identity","")
    m=re.match(r"^(.+)-(\d+)$",ident)
    if m:
        numbered.append((rr.get("source",""),m.group(2),m.group(1),ident))
groups=collections.defaultdict(list)
for src,suffix,base,ident in numbered:
    sp=poke_species(base)
    if not sp:continue
    members=chain_members(sp["evolution_chain"]["url"])
    if not members:continue
    root=members[0]
    groups[(src,suffix,root)].append((base,ident,members))
for (src,suffix,root),items in groups.items():
    member_order=items[0][2]
    present={base:ident for base,ident,_ in items}
    ordered=[present[x] for x in member_order if x in present]
    if len(ordered)<2:continue
    label=" → ".join(x.replace("-"," ").title() for x in ordered)
    known_types=[]
    for ident in ordered:
        sm=meta.get((src,norm(ident)))
        if sm and sm.get("type1"):
            known_types.append((sm.get("type1",""),sm.get("type2","")))
    unique_types=list(dict.fromkeys(known_types))
    for ident in ordered:
        numbered_form_family[(src,ident)]=label
        if len(unique_types)==1:
            numbered_type_fallback[(src,ident)]=unique_types[0]

enriched={}
report=[]
VERIFIED_SOURCE_OVERRIDES={
    ("Mega_Flygon","flygon-1"):{"name":"Mega Flygon","type1":"Bug","type2":"Dragon","family":"Trapinch → Vibrava → Flygon → Mega Flygon"},
    ("Mega_Flygon_Animated_Gen5","flygon-1"):{"name":"Mega Flygon","type1":"Bug","type2":"Dragon","family":"Trapinch → Vibrava → Flygon → Mega Flygon"},
    ("PokeAPI_Mega_Meowstic_Female","pokeapi-mega-meowstic-female"):{"name":"Mega Meowstic Female","type1":"Psychic","type2":"","family":"Espurr → Meowstic → Mega Meowstic Female"},
    ("Festival_PrincessPhoenix","merlicunf"):{"name":"Merlicun","type1":"Dragon","type2":"Bug","family":"Merlicun → Firomenis"},
    ("Festival_PrincessPhoenix","firomenisf"):{"name":"Firomenis","type1":"Dragon","type2":"Bug","family":"Merlicun → Firomenis"},
    ("Festival_PrincessPhoenix","drashimif"):{"name":"Drashimi","type1":"Dragon","type2":"","family":"Drashimi → Tsushimi → Tobishimi"},
    ("Festival_PrincessPhoenix","tsushimif"):{"name":"Tsushimi","type1":"Dragon","type2":"","family":"Drashimi → Tsushimi → Tobishimi"},
    ("Festival_PrincessPhoenix","tobishimif"):{"name":"Tobishimi","type1":"Dragon","type2":"","family":"Drashimi → Tsushimi → Tobishimi"},
    ("Festival_PrincessPhoenix","hissiorite"):{"name":"Hissiorite","type1":"Fire","type2":"","family":"Hissiorite → Cobarett → Pythonova"},
    ("Festival_PrincessPhoenix","cobarett"):{"name":"Cobarett","type1":"Fire","type2":"","family":"Hissiorite → Cobarett → Pythonova"},
    ("Festival_PrincessPhoenix","pythonova"):{"name":"Pythonova","type1":"Fire","type2":"","family":"Hissiorite → Cobarett → Pythonova"},
    ("Festival_PrincessPhoenix","baoby"):{"name":"Baoby","type1":"Grass","type2":"","family":"Baoby → Baobaraffe"},
    ("Festival_PrincessPhoenix","baobaraffe"):{"name":"Baobaraffe","type1":"Grass","type2":"","family":"Baoby → Baobaraffe"},
}

for r in rows:
    # The rebuilt DS-ready manifest no longer carries an is_official column.
    # Classify plain official/native rows from source + Mercury metadata instead.
    if plain_official_row(r,type_map):
        continue
    ident=r["identity"];src=r["source"];key=norm(ident)
    out={"identity":ident,"source":src,"front_path":r.get("front_path",""),"back_path":r.get("back_path","")}
    confidence=[]
    vo=VERIFIED_SOURCE_OVERRIDES.get((src,key))
    if vo:
        out.update(vo)
        confidence.append("VERIFIED_SOURCE_METADATA")
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
        # Strip familiar presentation suffixes while preserving the donor form
        # number used by PBS sections such as [BELSTATUE,1].
        base=re.sub(r"-(mega(?:-[xyz])?|redux|delta|male|female|beta)$","",key)
        sm=meta.get((src,base))
    if not sm:
        # Sprite filenames often expand a numbered PBS form with a readable
        # label: BELSTATUE_1 (Sun Shard) -> belstatue-1-sun-shard.
        mform=re.match(r"^(.+?)-(\d+)(?:-.+)?$",key)
        if mform:
            sm=meta.get((src,mform.group(1)+"-"+mform.group(2)))
    if sm:
        out.setdefault("name",sm.get("name") or ident)
        if not out.get("type1"):out["type1"]=sm.get("type1","")
        if not out.get("type2"):out["type2"]=sm.get("type2","")
        if not out.get("family"):out["family"]=sm.get("family","")
        confidence.append("SOURCE_METADATA")

    # External source databases (Pokengine/Mongratis and Elite Redux guide)
    # recover donor-intended types and evolution relationships that were not
    # shipped inside the sprite folders.
    er=external_records.get(src+"|"+key)
    if er:
        if not out.get("name"):out["name"]=er.get("name") or ident
        if not out.get("type1"):out["type1"]=er.get("type1","")
        if not out.get("type2"):out["type2"]=er.get("type2","")
        if not out.get("family"):
            out["family"]=er.get("family","")
            if not out["family"] and er.get("standalone"):
                out["family"]="Standalone — "+(er.get("name") or ident)
        confidence.append("EXTERNAL_SOURCE_METADATA")

    # A PBS-backed species with explicit typing and no incoming/outgoing
    # evolution edges is a confirmed standalone donor species, not unresolved.
    if not out.get("family") and sm and sm.get("type1") and key not in parents and key not in children:
        out["family"]="Standalone — "+(out.get("name") or ident)
        confidence.append("SOURCE_STANDALONE")

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
    if not out.get("type1") and (src,ident) in numbered_type_fallback:
        out["type1"],out["type2"]=numbered_type_fallback[(src,ident)]
        confidence.append("NUMBERED_FAMILY_TYPE_PROPAGATION")
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
    if (src,ident) in numbered_form_family:
        out["family"]=numbered_form_family[(src,ident)]
        confidence.append("CANONICAL_FORM_FAMILY_ORDER")
    elif not out.get("family") and key in edges:
        fam=custom_family_order(key)
        out["family"]=" → ".join(x.replace("-"," ").title() for x in fam)
        confidence.append("SOURCE_EVOLUTION_GRAPH")
    # User rule: if we cannot establish the family/standalone identity from
    # source data, Mercury data, or an explicit approved override, do not show
    # it for approval. "No known evolution" is unresolved, not proof standalone.
    if not out.get("family"):
        out["family"]="Unresolved family / relationship"
        confidence.append("UNRESOLVED_FAMILY")
    if not out.get("name"):
        out["name"]=ident.replace("-"," ").title()
        confidence.append("SOURCE_NAME")
    if not out.get("type1"):
        p1,p2=proposed_types(key,out.get("name",""),out.get("family",""))
        out["type1"],out["type2"]=p1,p2
        confidence.append("MERCURY_PROVISIONAL_CANON_TYPE")
    if not out.get("back_path"):
        out["back_path"]=likely_back(out["front_path"],ident,src)
        if out["back_path"]:confidence.append("BACK_MATCH_RECOVERED")

    # Mercury supports only the canonical 18 Pokémon types. Donor-only SOUND is
    # normalized to Normal while retaining any second vanilla type.
    t1=(out.get("type1") or "").strip().title()
    t2=(out.get("type2") or "").strip().title()
    if t1=="Sound":
        t1="Normal"
        confidence.append("SOUND_TO_NORMAL")
    if t2=="Sound":
        t2="Normal"
        confidence.append("SOUND_TO_NORMAL")
    if t1==t2:
        t2=""
    out["type1"],out["type2"]=t1,t2

    # User-approved manual recovery for the previously opaque 059_1f sprite.
    if ident=="059-1f":
        out["name"]="Proposed Mega Hisuian Arcanine"
        out["type1"],out["type2"]="Fire","Rock"
        out["family"]="Growlithe → Hisuian Arcanine"
        confidence.append("USER_APPROVED_IDENTITY_RECOVERY")

    out["type1"]=vanilla_type(out.get("type1"))
    out["type2"]=vanilla_type(out.get("type2"))
    out["confidence"]=";".join(confidence)
    unresolved_family=(out.get("family")=="Unresolved family / relationship")
    provisional_type=("MERCURY_PROVISIONAL_CANON_TYPE" in confidence)
    out["ready_for_approval"]=bool(
        out.get("name") and out.get("type1") in CANON_TYPES
        and (not out.get("type2") or out.get("type2") in CANON_TYPES)
        and out.get("front_path") and out.get("back_path")
        and not unresolved_family
        and not provisional_type
    )
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
        if not x.get("family") or x.get("family")=="Unresolved family / relationship": missing.append("family/relationship")
        if "MERCURY_PROVISIONAL_CANON_TYPE" in str(x.get("confidence","")): missing.append("source type")
        if not x.get("back_path"): missing.append("back sprite")
        row={k:x.get(k,"") for k in fields}
        row["missing"]="; ".join(missing)
        w.writerow(row)

summary={
 "custom_entries":len(report),
 "ready":sum(1 for x in report if x["ready_for_approval"]),
 "missing_type":sum(1 for x in report if str(x.get("type1","")).upper()=="TBD"),
 "missing_back":sum(1 for x in report if not x.get("back_path")),
 "unresolved_family":sum(1 for x in report if x.get("family")=="Unresolved family / relationship"),
 "provisional_type":sum(1 for x in report if "MERCURY_PROVISIONAL_CANON_TYPE" in str(x.get("confidence",""))),
 "source_metadata_records":len(meta),
 "excluded_from_approval":sum(1 for x in report if not x["ready_for_approval"]),
 "approval_policy":"Only custom/nonstandard designs with a verified front/back pair, source/authoritative canon-compatible typing, and resolved family/standalone relationship are shown for user decisions. Provisional-type or unresolved-family entries stay in recovery, not review.",
}
(MASTER/"fakemon_enrichment_summary.json").write_text(json.dumps(summary,indent=2)+"\n")
print(json.dumps(summary,indent=2))
