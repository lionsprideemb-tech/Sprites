from pathlib import Path
import csv,json,re,sys,collections

M=Path("DS_CUSTOM_LIBRARY/DS_READY_MASTER")
POOL=M/"leftover_review_pool.csv"
ENRICHED=M/"fakemon_enriched_metadata.json"
OLD=M/"user_sprite_decisions_2026-10-01.json"
LEGACY=M/"legacy_sprite_decisions_rev4.json"
OUT=M/"leftover_recovery_verification.json"
CANON={"Normal","Fire","Water","Electric","Grass","Ice","Fighting","Poison","Ground","Flying","Psychic","Bug","Rock","Ghost","Dragon","Dark","Steel","Fairy"}

def readcsv(p):
    with p.open(newline="",encoding="utf-8-sig") as f:return list(csv.DictReader(f))

def norm(s):
    x=re.sub(r"-+","-",re.sub(r"[^a-z0-9]+","-",str(s or "").lower().replace("'","").replace("’",""))).strip("-")
    return {"gyarevalry":"gyarevelry"}.get(x,x)

rows=readcsv(POOL) if POOL.exists() else []
enriched=json.loads(ENRICHED.read_text()).get("entries",{}) if ENRICHED.exists() else {}
old=json.loads(OLD.read_text()).get("decisions",{}) if OLD.exists() else {}
legacy=json.loads(LEGACY.read_text()).get("decisions",[]) if LEGACY.exists() else []

legacy_names=collections.defaultdict(set)
for d in legacy:
    dec=d.get("decision","")
    if dec not in {"approve","reject"}:continue
    for x in (d.get("norm_reviewed",""),d.get("norm_effective","")):
        if x:legacy_names[norm(x)].add(dec)

problems=[]
for r in rows:
    key=r.get("key","")
    if not r.get("front_path"):problems.append({"key":key,"problem":"missing_front"})
    if not r.get("back_path"):problems.append({"key":key,"problem":"missing_back"})
    t1,t2=r.get("type1",""),r.get("type2","")
    if t1 not in CANON:problems.append({"key":key,"problem":"invalid_type1","value":t1})
    if t2 and t2 not in CANON:problems.append({"key":key,"problem":"invalid_type2","value":t2})
    if old.get(key) in {"approve","reject"}:problems.append({"key":key,"problem":"recent_settled_decision_leaked","value":old.get(key)})
    names={norm(r.get("identity","")),norm(r.get("name",""))}
    # Legacy name collision is informational because a different source/design
    # can legitimately share a semantic name. The pool builder performs the
    # source-aware exclusion; verification records remaining collisions.
    vals=set()
    for n in names:vals |= legacy_names.get(n,set())
    if vals:
        r["_legacy_name_collision"]=";".join(sorted(vals))

keys=[r.get("key","") for r in rows]
dups=[k for k,n in collections.Counter(keys).items() if k and n>1]
for k in dups:problems.append({"key":k,"problem":"duplicate_key"})

source_counts=collections.Counter(r.get("source","") for r in rows)
family_unresolved=sum(1 for r in rows if not r.get("family") or "Unresolved family" in r.get("family",""))
legacy_collisions=sum(1 for r in rows if r.get("_legacy_name_collision"))
summary={
 "pool_entries":len(rows),
 "all_front_back_complete":all(r.get("front_path") and r.get("back_path") for r in rows),
 "all_types_canon":all(r.get("type1") in CANON and (not r.get("type2") or r.get("type2") in CANON) for r in rows),
 "recent_settled_decisions_leaked":sum(1 for p in problems if p["problem"]=="recent_settled_decision_leaked"),
 "duplicate_keys":len(dups),
 "unresolved_family_entries":family_unresolved,
 "legacy_semantic_name_collisions_remaining":legacy_collisions,
 "source_counts":dict(source_counts.most_common()),
 "hard_failures":problems,
 "pass":not problems,
}
OUT.write_text(json.dumps(summary,indent=2)+"\n")
print(json.dumps(summary,indent=2))
if problems:sys.exit(1)
