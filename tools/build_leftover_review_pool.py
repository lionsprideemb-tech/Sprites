from pathlib import Path
import csv, json

MASTER=Path("DS_CUSTOM_LIBRARY/DS_READY_MASTER")
ENRICHED=MASTER/"fakemon_enriched_metadata.json"
DECISIONS=MASTER/"user_sprite_decisions_2026-10-01.json"
OUT=MASTER/"leftover_review_pool.csv"
SUMMARY=MASTER/"leftover_review_summary.json"

data=json.loads(ENRICHED.read_text()).get("entries",{})
old=json.loads(DECISIONS.read_text()).get("decisions",{}) if DECISIONS.exists() else {}

rows=[]
excluded_approved=excluded_rejected=excluded_incomplete=0
for key,e in data.items():
    prior=old.get(key,"")
    if prior=="approve":
        excluded_approved+=1; continue
    if prior=="reject":
        excluded_rejected+=1; continue
    if not e.get("ready_for_approval"):
        excluded_incomplete+=1; continue
    if not e.get("front_path") or not e.get("back_path"):
        excluded_incomplete+=1; continue
    if not e.get("type1") or e.get("type1")=="TBD":
        excluded_incomplete+=1; continue
    rows.append({
        "key":key,
        "identity":e.get("identity",""),
        "name":e.get("name",""),
        "type1":e.get("type1",""),
        "type2":e.get("type2",""),
        "family":e.get("family",""),
        "source":e.get("source",""),
        "front_path":e.get("front_path",""),
        "back_path":e.get("back_path",""),
        "confidence":e.get("confidence",""),
        "prior_decision":prior,
    })

def priority(r):
    s=(" ".join([r["identity"],r["name"],r["family"]])).lower()
    return 0 if any(x in s for x in ["merrykarp","gyarevelry","gible","gabite","garchomp"]) else 1

rows.sort(key=lambda r:(priority(r),r["family"].lower(),r["name"].lower(),r["source"].lower()))

fields=["key","identity","name","type1","type2","family","source","front_path","back_path","confidence","prior_decision"]
with OUT.open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

summary={
    "leftover_review_entries":len(rows),
    "excluded_prior_approved":excluded_approved,
    "excluded_prior_rejected":excluded_rejected,
    "excluded_incomplete":excluded_incomplete,
    "requires_front_and_back":True,
    "requires_canon_type":True,
    "priority_recoveries":{
        "merrykarp":sum(1 for r in rows if "merrykarp" in (r["identity"]+" "+r["name"]).lower()),
        "gyarevelry":sum(1 for r in rows if "gyarevelry" in (r["identity"]+" "+r["name"]).lower()),
        "gible_family":sum(1 for r in rows if any(x in (r["identity"]+" "+r["name"]).lower() for x in ["gible","gabite","garchomp"]))
    }
}
SUMMARY.write_text(json.dumps(summary,indent=2)+"\n")
print(json.dumps(summary,indent=2))
