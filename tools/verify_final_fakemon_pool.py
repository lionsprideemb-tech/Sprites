from pathlib import Path
import json,csv

MASTER=Path("DS_CUSTOM_LIBRARY/DS_READY_MASTER")
ENRICHED=MASTER/"fakemon_enriched_metadata.json"
OUT=MASTER/"final_fakemon_verification.json"
BAD=MASTER/"final_fakemon_verification_failures.csv"

data=json.loads(ENRICHED.read_text()).get("entries",{})
ready=[]
bad=[]
for k,e in data.items():
    if not e.get("ready_for_approval"):
        continue
    ready.append(e)
    problems=[]
    if not e.get("name"): problems.append("missing name")
    if not e.get("type1") or e.get("type1")=="TBD": problems.append("missing type")
    if not e.get("family"): problems.append("missing family")
    fp=e.get("front_path","")
    bp=e.get("back_path","")
    if not fp or not Path(fp).is_file(): problems.append("front file missing")
    if not bp or not Path(bp).is_file(): problems.append("back file missing")
    if problems:
        bad.append({
            "identity":e.get("identity",""),
            "name":e.get("name",""),
            "source":e.get("source",""),
            "front_path":fp,
            "back_path":bp,
            "problems":"; ".join(problems)
        })

with BAD.open("w",newline="",encoding="utf-8") as f:
    fields=["identity","name","source","front_path","back_path","problems"]
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(bad)

summary={
    "ready_entries_checked":len(ready),
    "verification_failures":len(bad),
    "verified_ready_entries":len(ready)-len(bad),
    "all_ready_entries_valid":len(bad)==0
}
OUT.write_text(json.dumps(summary,indent=2)+"\n")
print(json.dumps(summary,indent=2))
