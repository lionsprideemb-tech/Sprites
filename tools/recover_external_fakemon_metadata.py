from pathlib import Path
# FINAL_CONSOLIDATED_RECOVERY_2026_10_02
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
        for href in re.findall(r"href=['\"](/mons/[^'\"?]+)(?:\?[^'\"]*)?['\"]",raw):
            parts=href.split("/")
            if len(parts)<4:continue
            mid,slug=parts[2],urllib.parse.unquote(parts[3])
            key=norm(slug)
            links.setdefault(key,[])
            url="https://pokengine.org"+href
            if url not in links[key]:links[key].append(url)
    return links

def search_links(query):
    if not query:return []
    raw=fetch("https://pokengine.org/search?query="+urllib.parse.quote(str(query)))
    if not raw:return []
    out=[]
    for href in re.findall(r"href=['\"](/mons/[^'\"?#]+)",raw):
        url="https://pokengine.org"+href
        if url not in out:out.append(url)
    return out

def target_aliases(identity,name,source):
    vals={norm(identity),norm(name)}
    for x in list(vals):
        y=x
        for suf in ("-female","-male","-f","-m","-front","-back"):
            if y.endswith(suf): vals.add(y[:-len(suf)])
        if y.endswith("front") and len(y)>5: vals.add(y[:-5].rstrip("-"))
        if y.endswith("back") and len(y)>4: vals.add(y[:-4].rstrip("-"))
        if source=="Festival_PrincessPhoenix":
            if y.endswith("fs") and len(y)>2: vals.add(y[:-2])
            elif y.endswith("f") and len(y)>1: vals.add(y[:-1])
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
    # Evolution links on the page are stronger than collection membership and
    # let us recover families even when a contributor is not in Mongratis.
    block_norms={norm(x) for x in block if x}
    for href in re.findall(r"href=['\"](/mons/[^'\"?#]+)",raw):
        parts=href.split("/")
        if len(parts)<4:continue
        slug=norm(urllib.parse.unquote(parts[3]))
        if slug and any(b==slug or b.startswith(slug+"-") or slug.startswith(b+"-") for b in block_norms):
            known.add(slug)
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
    relation_cue=re.search(r"(?:Evolv|Lv\\.|Level up|Use an? |Happiness|Trade|holding|Stone)",joined,re.I)
    if len(family)<=1 and (re.search(r"Evo Line:\\s*Complete",joined,re.I) or not relation_cue):
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

def parse_romhackguide(identity,display_name=""):
    slug=identity
    url=f"https://romhackguides.com/hacks/elite-redux/pokemon/{slug}/"
    raw=fetch(url)
    if not raw:return None
    lines=text_lines(raw); joined=" ".join(lines)
    if "404" in joined[:300]:return None
    # The recovery report already has the correct display name; the guide page
    # contains decorative breadcrumb glyphs that should never become species names.
    name=(display_name or identity.replace("-"," ").title()).strip()

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
targets=[r for r in rows if (r.get("ready_for_approval","").lower()!="true") and (r.get("back_path") or r.get("source")=="Elite_Redux_Bulk")]
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

        # Pokengine's exact-name search is a fallback for donor mons that are
        # indexed on the site but not currently exposed by the collection page.
        if not candidates:
            # Site-wide search must stay exact. Broad aliases such as
            # "regional-diglett" -> "diglett" are safe inside a known donor
            # collection, but site-wide they could silently select Game Freak's
            # ordinary Diglett instead of the contributor's regional design.
            search_aliases={norm(ident),norm(name)}
            if src=="Festival_PrincessPhoenix":
                for a in list(search_aliases):
                    if a.endswith("fs"): search_aliases.add(a[:-2])
                    elif a.endswith("f"): search_aliases.add(a[:-1])
            for a in list(search_aliases):
                if a.endswith("front"): search_aliases.add(a[:-5].rstrip("-"))
                if a.endswith("back"): search_aliases.add(a[:-4].rstrip("-"))
            search_aliases={a for a in search_aliases if a}
            for a in sorted(search_aliases,key=len,reverse=True):
                raw=fetch("https://pokengine.org/search?query="+urllib.parse.quote(a.replace("-"," ")))
                for href in re.findall(r"href=['\"](/mons/[^'\"?]+)",raw):
                    slug=urllib.parse.unquote(href.split("/")[-1])
                    if norm(slug) in search_aliases:
                        candidates.append("https://pokengine.org"+href)
                if candidates:break

        # Prefer exact identity/name matches. For source sprite IDs ending in
        # -1/-2/etc., donor packs conventionally number alternate forms after
        # the base form; collection links are gathered base first, then forms.
        seen=[]
        for u in candidates:
            if u not in seen:seen.append(u)
        mform=re.match(r"^.+-(\d+)$",norm(ident))
        if mform and seen:
            n=int(mform.group(1))
            if 0 <= n < len(seen):
                seen=[seen[n]]+[u for i,u in enumerate(seen) if i!=n]
        for u in seen[:8]:
            p=parse_pokengine(u,known)
            if p and p.get("type1"):
                rec=p
                # Numeric/form targets intentionally allow form-specific pages
                # even when the visible base species name is identical.
                if mform or norm(p.get("name")) in aliases:break

    # Fallback to Pokengine's own search when the sprite pack's contributor
    # is not represented by our two bulk collections. Only accept an exact
    # species/display-name hit so similarly named mons (e.g. Anuf/Anufelis)
    # can never be silently substituted.
    if rec is None and (src in (festival_sources | {"Mikitari","Earthretha"})):
        primary={norm(ident),norm(name)}
        primary={x for x in primary if x}
        queries=[]
        for q in (name,ident.replace("-"," ")):
            if q and q not in queries:queries.append(q)
        for q in queries[:2]:
            for u in search_links(q)[:6]:
                p=parse_pokengine(u,set())
                if not p or not p.get("type1"):continue
                href_slug=norm(urllib.parse.unquote(u.rstrip("/").split("/")[-1]))
                if norm(p.get("name")) in primary or href_slug in primary:
                    rec=p
                    break
            if rec:break

    if rec is None and src=="Elite_Redux_Bulk":
        rec=parse_romhackguide(ident,name)

    if rec and rec.get("type1") in CANON and (not rec.get("type2") or rec.get("type2") in CANON):
        rec["source"]=src;rec["identity"]=ident
        out[f"{src}|{norm(ident)}"]=rec
        stats["resolved"]+=1
        stats["by_source"][src]=stats["by_source"].get(src,0)+1

# Merge all partial family statements into complete connected evolution lines.
# This turns pairwise donor records such as A→B and B→C into one A→B→C family.
parents_graph={}
children_graph={}
labels={}
for rec in out.values():
    fam=rec.get("family","")
    if not fam or fam.startswith("Standalone"):continue
    parts=[x.strip() for x in fam.split("→") if x.strip()]
    for x in parts: labels[norm(x)]=x
    for a,b in zip(parts,parts[1:]):
        na,nb=norm(a),norm(b)
        children_graph.setdefault(na,set()).add(nb)
        parents_graph.setdefault(nb,set()).add(na)

def component(start):
    seen=set();stack=[start]
    while stack:
        x=stack.pop()
        if x in seen:continue
        seen.add(x)
        stack.extend(children_graph.get(x,set()))
        stack.extend(parents_graph.get(x,set()))
    return seen

def ordered_component(nodes):
    roots=sorted(x for x in nodes if not (parents_graph.get(x,set()) & nodes))
    ordered=[];seen=set()
    def walk(x):
        if x in seen or x not in nodes:return
        seen.add(x);ordered.append(x)
        for y in sorted(children_graph.get(x,set()) & nodes):walk(y)
    for r in roots:walk(r)
    for x in sorted(nodes):
        if x not in seen:walk(x)
    return ordered

for rec in out.values():
    if rec.get("standalone"):continue
    k=norm(rec.get("name",""))
    if not k:k=norm(rec.get("identity",""))
    nodes=component(k)
    if len(nodes)>1:
        order=ordered_component(nodes)
        rec["family"]=" → ".join(labels.get(x,x.replace("-"," ").title()) for x in order)
        rec["standalone"]=False

stats["with_family"]=sum(1 for r in out.values() if r.get("family"))
stats["standalone"]=sum(1 for r in out.values() if r.get("standalone"))
OUT.write_text(json.dumps({"generated":"2026-10-02","records":out,"stats":stats},indent=2)+"\\n",encoding="utf-8")
print(json.dumps(stats,indent=2))
