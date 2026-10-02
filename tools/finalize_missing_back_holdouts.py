from pathlib import Path
import csv,json,collections

M=Path("DS_CUSTOM_LIBRARY/DS_READY_MASTER")
SRC=M/"fakemon_excluded_incomplete.csv"
OUT=M/"missing_back_holdout_summary.json"
CSV=M/"missing_back_holdout.csv"

rows=[]
if SRC.exists():
    with SRC.open(newline="",encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if not r.get("back_path"):
                rows.append(r)

by_source=collections.Counter(r.get("source","") for r in rows)
outrows=[]
for r in rows:
    outrows.append({
        "identity":r.get("identity",""),
        "name":r.get("name",""),
        "source":r.get("source",""),
        "front_path":r.get("front_path",""),
        "type1":r.get("type1",""),
        "type2":r.get("type2",""),
        "family":r.get("family",""),
        "status":"WITHHELD_NO_VERIFIED_BACK",
    })

with CSV.open("w",newline="",encoding="utf-8") as f:
    fields=["identity","name","source","front_path","type1","type2","family","status"]
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(outrows)

summary={
    "true_holdout_count":len(outrows),
    "policy":"Entries without a verified back sprite are withheld from the Mercury leftover approval pool. No guessed or unrelated back sprite is substituted.",
    "by_source":dict(by_source.most_common()),
    "review_eligible":0,
}
OUT.write_text(json.dumps(summary,indent=2)+"\n")
print(json.dumps(summary,indent=2))
