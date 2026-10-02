from pathlib import Path
import json, re, hashlib, io, subprocess
from collections import defaultdict
from PIL import Image
import openpyxl

ROOT=Path("DS_CUSTOM_LIBRARY")
OUT=ROOT/"DS_READY_MASTER"
AUTH=json.loads((OUT/"platinum_redux_authoritative.json").read_text())
auth_entries=AUTH.get("entries",[])
by_base=defaultdict(list)
for e in auth_entries:
    by_base[e["base_species"].strip().lower()].append(e)

xlsx=Path("/tmp/Platinum_Redux_v4.0_docs.xlsx")
subprocess.run(["gdown","1ZBX85oUoZKwwNcbpumM0bRH9uWSa7fiM","-O",str(xlsx)],check=True)

# hash existing extracted embedded images
repo_hash={}
base=ROOT/"hack-packs"/"Platinum_Redux_Embedded_Sprites"/"all-embedded"
for p in base.glob("*"):
    if p.is_file():
        repo_hash[hashlib.sha256(p.read_bytes()).hexdigest()]=p.as_posix()

wb=openpyxl.load_workbook(xlsx,data_only=True)
anchors=[]
matches=[]
unmapped=[]

def sval(v):
    if v is None:return ""
    return str(v).strip()

def nearest_text(ws,row,col,radius=3):
    vals=[]
    for rr in range(max(1,row-radius),min(ws.max_row,row+radius)+1):
        for cc in range(max(1,col-radius),min(ws.max_column,col+radius)+1):
            v=sval(ws.cell(rr,cc).value)
            if v:
                vals.append({"row":rr,"col":cc,"value":v})
    return vals

for ws in wb.worksheets:
    for idx,img in enumerate(getattr(ws,"_images",[])):
        try:
            row=img.anchor._from.row+1
            col=img.anchor._from.col+1
        except Exception:
            continue
        try:
            data=img._data()
            h=hashlib.sha256(data).hexdigest()
            im=Image.open(io.BytesIO(data)); wh=list(im.size)
        except Exception:
            h="";wh=[0,0]
        near=nearest_text(ws,row,col,4)
        # Species/name fields may be far left while the embedded sprite is far right.
        # Include the full anchor row plus one row above/below when matching identities.
        rowwide=[]
        for rr in range(max(1,row-1),min(ws.max_row,row+1)+1):
            for cc in range(1,ws.max_column+1):
                v=sval(ws.cell(rr,cc).value)
                if v: rowwide.append({"row":rr,"col":cc,"value":v})
        joined=" | ".join(x["value"] for x in (near+rowwide)).lower()
        bases=[]
        for base_name in by_base:
            # exact-ish word presence; punctuation-normalized fallback
            bn=base_name.lower()
            if bn in joined:
                bases.append(base_name)
        # Prefer longest base name when nested strings collide.
        bases=sorted(set(bases),key=len,reverse=True)
        if len(bases)>1:
            longest=bases[0]
            bases=[b for b in bases if not (b!=longest and b in longest)]
        headers=[]
        for rr in range(max(1,row-10),row+1):
            v=sval(ws.cell(rr,col).value)
            if v: headers.append(v)
        orientation=""
        signal=(" ".join(headers[-4:])+" "+joined).lower()
        if "back" in signal: orientation="back"
        elif "front" in signal: orientation="front"
        rec={
            "sheet":ws.title,"image_index":idx,"anchor_row":row,"anchor_col":col,
            "sha256":h,"repo_path":repo_hash.get(h,""),"size":wh,
            "nearby":near[:50],"rowwide":rowwide[:120],"base_candidates":bases[:10],"orientation_hint":orientation,
            "column_context":headers[-6:]
        }
        anchors.append(rec)
        if len(bases)==1 and repo_hash.get(h):
            base_name=bases[0]
            for ae in by_base[base_name]:
                matches.append({
                    "review_id":ae["review_id"],"base_species":ae["base_species"],
                    "effective_identity":ae["effective_identity"],"decision":ae["decision"],
                    "classification":ae["classification"],"sheet":ws.title,
                    "anchor_row":row,"anchor_col":col,"repo_path":repo_hash[h],
                    "orientation_hint":orientation,"size":wh
                })
        else:
            unmapped.append(rec)

# Build a direct review catalog from the Forms sheet. In this workbook:
# col 2 = species/form name, 3/4 = typing, 12 = Front, 13 = Back, 14 = Shiny.
forms=wb["Forms"]
forms_images=defaultdict(dict)
# Reuse the first-pass anchor records; calling openpyxl image._data() a second
# time can fail because the underlying image stream has already been consumed.
for a in anchors:
    if a.get("sheet")!="Forms": continue
    row=a.get("anchor_row"); col=a.get("anchor_col")
    p=a.get("repo_path",""); h=a.get("sha256","")
    if col in (12,13,14) and p:
        forms_images[row][col]={"path":p,"sha256":h}

VANILLA_TYPE={"Sound":"Normal"}
def clean_type(v):
    t=sval(v).title()
    return VANILLA_TYPE.get(t,t)

def species_slug(name):
    s=str(name or "").strip().lower().replace("♀","-f").replace("♂","-m")
    s=s.replace("’","").replace("'","").replace(".","")
    s=re.sub(r"[^a-z0-9]+","-",s).strip("-")
    return s

family_cache={}
def poke_family(name):
    slug=species_slug(name)
    if slug in family_cache:return family_cache[slug]
    # PokeAPI special names.
    special={"mr-mime":"mr-mime","mime-jr":"mime-jr","farfetchd":"farfetchd","porygon-z":"porygon-z"}
    slug=special.get(slug,slug)
    try:
        import urllib.request
        with urllib.request.urlopen("https://pokeapi.co/api/v2/pokemon-species/"+slug,timeout=15) as r:
            sp=json.load(r)
        with urllib.request.urlopen(sp["evolution_chain"]["url"],timeout=15) as r:
            ch=json.load(r)
        members=[]
        def walk(n):
            members.append(n["species"]["name"].replace("-"," ").title())
            for e in n.get("evolves_to",[]):walk(e)
        walk(ch["chain"])
        fam=" → ".join(members)
    except Exception:
        fam=str(name).strip()+" family"
    family_cache[slug]=fam
    return fam

platinum_review=[]
for row,imgs in sorted(forms_images.items()):
    name=sval(forms.cell(row,2).value)
    if not name or 12 not in imgs or 13 not in imgs:continue
    t1=clean_type(forms.cell(row,3).value)
    t2=clean_type(forms.cell(row,4).value)
    dex=sval(forms.cell(row,1).value)
    base=name.title() if name.isupper() else name
    auth_candidates=by_base.get(base.lower(),[])
    hist=auth_candidates[0]["decision"] if auth_candidates else ""
    review_id=auth_candidates[0]["review_id"] if auth_candidates else ""
    identity="platinum-redux-"+species_slug(base)
    platinum_review.append({
      "identity":identity,
      "name":"Platinum Redux "+base,
      "base_species":base,
      "type1":t1,"type2":t2,
      "family":poke_family(base),
      "source":"Platinum Redux v4.0 workbook",
      "bucket":"NATIVE_HACK",
      "front_path":imgs[12]["path"],
      "back_path":imgs[13]["path"],
      "structural_hash":imgs[12]["sha256"],
      "historical_review_id":review_id,
      "historical_decision":hist,
      "ready_for_approval":True
    })
(OUT/"platinum_redux_review_entries.json").write_text(json.dumps({
  "generated":"2026-10-01","count":len(platinum_review),"entries":platinum_review
},indent=2)+"\n")

# Aggregate image candidates by review id.
agg=defaultdict(list)
for m in matches:agg[m["review_id"]].append(m)
summary={
  "workbook_sheets":wb.sheetnames,
  "images_anchored":len(anchors),
  "images_with_unique_species_match":len(matches),
  "authoritative_entries":len(auth_entries),
  "authoritative_entries_with_image_match":len(agg),
  "keep_entries_with_image_match":sum(1 for e in auth_entries if e["decision"]=="KEEP" and e["review_id"] in agg),
  "keep_entries_total":sum(1 for e in auth_entries if e["decision"]=="KEEP"),
  "reject_entries_with_image_match":sum(1 for e in auth_entries if e["decision"]=="REJECT" and e["review_id"] in agg),
  "unmapped_images":len(unmapped),
  "platinum_review_entries":len(platinum_review)
}
(OUT/"platinum_redux_workbook_anchor_map.json").write_text(json.dumps({
    "summary":summary,"matches_by_review_id":agg,"anchors":anchors
},indent=2,default=list)+"\n")
(OUT/"platinum_redux_workbook_map_summary.json").write_text(json.dumps(summary,indent=2)+"\n")

diag={"sheet_image_counts":{},"sheet_anchor_columns":{},"samples":[]}
for a in anchors:
    diag["sheet_image_counts"][a["sheet"]]=diag["sheet_image_counts"].get(a["sheet"],0)+1
    key=a["sheet"]
    diag["sheet_anchor_columns"].setdefault(key,{})
    col=str(a["anchor_col"])
    diag["sheet_anchor_columns"][key][col]=diag["sheet_anchor_columns"][key].get(col,0)+1
for sheet in wb.sheetnames:
    subset=[a for a in anchors if a["sheet"]==sheet]
    for a in subset[:12]:
        diag["samples"].append({
          "sheet":a["sheet"],"anchor_row":a["anchor_row"],"anchor_col":a["anchor_col"],
          "repo_path":a["repo_path"],"size":a["size"],
          "rowwide":[x["value"] for x in a.get("rowwide",[])][:40],
          "column_context":a.get("column_context",[])
        })
(OUT/"platinum_redux_anchor_diagnostics.json").write_text(json.dumps(diag,indent=2)+"\n")
print(json.dumps(summary,indent=2))
