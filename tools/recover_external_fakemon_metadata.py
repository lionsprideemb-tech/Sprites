from pathlib import Path
import csv,json,re,urllib.request,urllib.parse,time,html as htmlmod
from html.parser import HTMLParser

ROOT=Path("DS_CUSTOM_LIBRARY")
MASTER=ROOT/"DS_READY_MASTER"
REPORT=MASTER/"fakemon_enrichment_report.csv"
OUT=MASTER/"external_fakemon_metadata.json"
CANON={"Normal","Fire","Water","Electric","Grass","Ice","Fighting","Poison","Ground","Flying","Psychic","Bug","Rock","Ghost","Dragon","Dark","Steel","Fairy"}

def norm(s):
    s=str(s or "").lower().replace("♀"," female ").replace("♂"," male ")
    s=s.replace("’","'").replace("'","")
    s=re.sub(r"[^a-z0-9]+","-",s)
    return re.sub(r"-+","-",s).strip("-")

class Textify(HTMLParser):
    def __init__(self): super().__init__(); self.parts=[]
    def handle_data(self,d):
        d=htmlmod.unescape(d)
        if d.strip(): self.parts.append(d.strip())

CACHE={}
def fetch(url):
    if url in CACHE:return CACHE[url]
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 MercurySpriteRecovery/1.0"})
    last=None
    for n in range(3):
        try:
            with urllib.request.urlopen(req,timeout=30) as r:
                raw=r.read().decode("utf-8","replace")
            CACHE[url]=raw
            time.sleep(0.03)
            return raw
        except Exception as e:
            last=e; time.sleep(0.5*(n+1))
    return ""

def text_lines(raw):
    p=Textify();p.feed(raw)
    return [x.strip() for x in p.parts if x.strip()]

def collection_links(base):
    links={}
    raws=[]
    for suffix in ("","?forms","?megas"):
        raw=fetch(base+suffix)
        raws.append(raw)
    for raw in raws:
        for href in re.findall(r"href=['\"](/mons/[^'\"?#]+)['\"]",raw):
            parts=href.split("/")
            if len(parts)<4:continue
            mid,slug=parts[2],urllib.parse.unquote(parts[3])
            key=norm(slug)
            links.setdefault(key,[])
            url="https://pokengine.org"+href
            if url not in links[key]:links[key].append(url)
    return links

def target_aliases(identity,name,source):
    vals={norm(identity),norm(name)}
    for x in list(vals):
        y=x
        for suf in ("-female","-male","-f","-m","-front","-back"):
            if y.endswith(suf): vals.add(y[:-len(suf)])
        m=re.match(r"^(.+)-(\d+)$",y)
        if m: vals.add(m.group(1))
        for pre in ("regional-","spaceworld-","luminian-","earthrethian-"):
            if y.startswith(pre): vals.add(y[len(pre):])
    aliases={
      "cabatfe":"cabat-female","cabatma":"cabat-male",
      "porygona":"porygon-a","octolect":"octolet","sproutsy":"sprousy",
      "lamby":"lambi","hauntray":"hauntray",
    }
    for x in list(vals):
        if x in aliases: vals.add(aliases[x])
    return {x for x in vals if x}

def parse_pokengine(url,known_slugs):
    raw=fetch(url)
    if not raw:return None
    lines=text_lines(raw)
    if not lines:return None
    try: oi=lines.index("Owner")
    except ValueError: oi=min(len(lines),80)
    pre=lines[:oi]
    # Canon types occur immediately before category "Mon" in the header.
    types=[]
    for i,x in enumerate(pre):
        if x in CANON and x not in types:
            # Ignore UI/move noise by staying close to Owner and after Imagery.
            if i>5:types.append(x)
    types=types[-2:] if len(types)>2 else types

    title=""
    if "Imagery" in lines:
        j=lines.index("Imagery")
        for x in lines[j+1:j+8]:
            if re.fullmatch(r"[0-9]+",x) or "rating" in x.lower() or x in {"★"}:continue
            if x.startswith("(") or " Form (" in x:continue
            title=x;break
    if not title:
        title=re.sub(r" - Pok.ngine.*$","",lines[0],flags=re.I)

    # Build evolution/family sequence from explicit related-mon names in the
    # descriptive/evolution block, before move lists.
    stop=len(lines)
    for token in ("Level-up moves","Teach moves","Egg moves","Check out"):
        if token in lines: stop=min(stop,lines.index(token))
    start=0
    for token in ("Flavor","Notes"):
        if token in lines:start=max(start,lines.index(token))
    block=lines[start:stop]
    family=[]
    known=set(known_slugs)
    # Also keep the current page name.
    current=norm(title)
    known.add(current)
    for x in block:
        nx=norm(re.sub(r"\s+(?:red-striped|blue-striped|violet-striped|normal|militant|rock|clay-helmet)\s+form$","",x,flags=re.I))
        if nx in known and nx not in family:
            family.append(nx)
    # If exact collection names did not survive form labels, find slug starts.
    for x in block:
        nx=norm(x)
        for k in known:
            if (nx==k or nx.startswith(k+"-")) and k not in family:
                family.append(k)
    # Ensure current is represented when relations exist.
    if current and current not in family:
        family.append(current)

    standalone=False
    joined=" ".join(block)
    if len(family)<=1 and re.search(r"Evo Line:\s*Complete",joined,re.I):
        standalone=True

    designer=""
    if "Designer" in lines:
        i=lines.index("Designer")
        if i+1<len(lines):designer=lines[i+1]

    display={norm(x):x for x in lines if 1<=len(x)<=60}
    fam_display=[]
    for k in family:
        # Humanize if exact display unavailable.
        fam_display.append(display.get(k,k.replace("-"," ").title()))
    return {
      "name":title,
      "type1":types[0] if types else "",
      "type2":types[1] if len(types)>1 else "",
      "family":" → ".join(fam_display) if len(fam_display)>1 else (("Standalone — "+title) if standalone else ""),
      "standalone":standalone,
      "designer":designer,
      "evidence_url":url,
    }

def parse_romhackguide(identity):
    slug=identity
    url=f"https://romhackguides.com/hacks/elite-redux/pokemon/{slug}/"
    raw=fetch(url)
    if not raw:return None
    lines=text_lines(raw); joined=" ".join(lines)
    if "404" in joined[:300]:return None
    name=""
    for i,x in enumerate(lines):
        if x.lower()=="elite redux" and i+1<len(lines):
            name=lines[i+1]
    # Better: find line exactly matching slug words title-cased.
    if not name:
        target=norm(identity)
        for x in lines[:80]:
            if norm(x)==target:
                name=x;break
    if not name:name=identity.replace("-"," ").title()

    t1=t2=""
    m=re.search(r"\b("+"|".join(CANON)+r")(?:\s*/\s*("+"|".join(CANON)+r"))?\s+type\b",joined)
    if m:
        t1=m.group(1); t2=m.group(2) or ""
    if not t1:
        # Header usually has adjacent type tokens shortly after the species name.
        try:i=next(i for i,x in enumerate(lines[:100]) if norm(x)==norm(name))
        except StopIteration:i=0
        ts=[]
        for x in lines[i+1:i+20]:
            if x in CANON and x not in ts:ts.append(x)
        if ts:t1=ts[0];t2=ts[1] if len(ts)>1 else ""

    family=""
    # "evolve Fluffbee at level 30" / "evolve Bewear ..."
    m=re.search(r"evolve\s+([A-Z][A-Za-z0-9 .’'\-]+?)(?:\s+at\s+|\s+using\s+|\s+while\s+|\s+with\s+|\.|,)",joined)
    if m:
        parent=m.group(1).strip()
        family=f"{parent} → {name}"
    elif "mega" in identity:
        base=re.sub(r"-mega(?:-[xyz])?$","",identity)
        if base!=identity:
            family=base.replace("-"," ").title()+" → "+name

    # Known Redux/custom form fallback: tie it to its obvious base species/form
    # instead of leaving it ungrouped.
    if not family:
        base=identity
        for tok in ("-redux","-ex","-clemont","-serena","-partner","-galaxy","-ph-d"):
            base=base.replace(tok,"")
        base=re.sub(r"-mega(?:-[xyz])?$","",base)
        if base!=identity:
            family=base.replace("-"," ").title()+" → "+name
    return {"name":name,"type1":t1,"type2":t2,"family":family,"standalone":False,"designer":"Elite Redux","evidence_url":url}

rows=[]
with REPORT.open(newline="",encoding="utf-8-sig") as f:
    rows=list(csv.DictReader(f))
targets=[r for r in rows if (r.get("ready_for_approval","").lower()!="true")]
by_source={}
for r in targets:by_source.setdefault(r["source"],[]).append(r)

collections={
 "Mikitari":"https://pokengine.org/collections/10o0ctrn/Mikitari",
 "Mongratis":"https://pokengine.org/collections/107s7x9x/Mongratis",
}
miki=collection_links(collections["Mikitari"])
mong=collection_links(collections["Mongratis"])
known_miki=set(miki)
known_mong=set(mong)

out={}
stats={"targets":len(targets),"resolved":0,"by_source":{}}

festival_sources={
 "Festival_Magiscarf","Festival_PrincessPhoenix","Festival_Scotsman",
 "Festival_Atsui","Festival_Lumio","Festival_Misc","Fakemon_Festival_Full"
}

for r in targets:
    src=r["source"];ident=r["identity"];name=r.get("name","")
    rec=None
    aliases=target_aliases(ident,name,src)
    linkmap=None;known=None
    if src=="Mikitari":linkmap,known=miki,known_miki
    elif src in festival_sources:linkmap,known=mong,known_mong

    if linkmap is not None:
        candidates=[]
        for a in aliases:
            candidates.extend(linkmap.get(a,[]))
        # Prefer exact identity/name matches; otherwise base alias inherited metadata.
        seen=[]
        for u in candidates:
            if u not in seen:seen.append(u)
        for u in seen[:4]:
            p=parse_pokengine(u,known)
            if p and p.get("type1"):
                rec=p
                if norm(p.get("name")) in aliases:break

    if rec is None and src=="Elite_Redux_Bulk":
        rec=parse_romhackguide(ident)

    if rec and rec.get("type1") in CANON and (not rec.get("type2") or rec.get("type2") in CANON):
        rec["source"]=src;rec["identity"]=ident
        out[f"{src}|{norm(ident)}"]=rec
        stats["resolved"]+=1
        stats["by_source"][src]=stats["by_source"].get(src,0)+1

OUT.write_text(json.dumps({"generated":"2026-10-02","records":out,"stats":stats},indent=2)+"\n",encoding="utf-8")
# trigger after workflow install\nprint(json.dumps(stats,indent=2))
