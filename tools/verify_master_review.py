#!/usr/bin/env python3
"""Non-destructive validation of Mercury Redux sprite-review provenance and user decisions."""
from __future__ import annotations

import json
import re
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "review/master-review-data-2026-10-23.json"
USER = ROOT / "review/recovered-user-export-decisions-2026-10-23.json"
HTML = ROOT / "mercury-master-review.html"


def norm(value):
    value = str(value or "").lower().strip()
    return {"approve":"keep", "keep":"keep", "reject":"cut", "cut":"cut", "delete":"cut","maybe":"maybe"}.get(value, "")


def check(condition, description):
    if not condition:
        raise AssertionError(description)
    print("PASS:", description)


def main():
    d = json.loads(DATA.read_text(encoding="utf-8"))
    u = json.loads(USER.read_text(encoding="utf-8"))
    page = HTML.read_text(encoding="utf-8")
    r = d["records"]
    c = d["choices"]
    check(d["schema"] == "mercury.sprite.master-review.v1", "master schema pinned")
    check(d["policy"]["no_deletion"] is True and d["policy"]["no_integration"] is True, "non-destructive no-integration rules")
    check(len(r) == 1837, "all 1,837 prior source-linked review records preserved")
    ids = [x["id"] for x in r]
    check(len(ids) == len(set(ids)), "every record has a unique stable ID")
    check(len(c) == 9 and len({x["identity"] for x in c}) == 9, "all competing design source records preserved")
    check(len(u["exports"]) == 3, "original user-export decision snapshots retained")
    ds = u["exports"][0]["rows"]
    check(len(ds) == 372, "372 original DS artwork decisions preserved")
    byid = {x["id"]: x for x in r}
    for row in ds:
        rid = "ds:" + row["identity"] + "|" + row["structural_hash"]
        check(rid in byid, "source vote has preserved identity: " + rid) if rid not in byid else None
        check(norm(row["decision"]) == norm(byid[rid]["decision"]), "user vote was not changed: " + rid) if norm(row["decision"]) != norm(byid[rid]["decision"]) else None
    check(sum(x["id"].startswith("ds:") for x in r) == 372, "exact artwork votes remain intact")
    check(sum(x["id"].startswith("polished:") for x in r) >= 262, "polished sprite vote records remain intact")
    check(all(x.get("originalName") for x in r), "original labels retained in every record")
    check(all(x.get("creator") is not None for x in r), "creator/source attribution stored in separate field")
    check(not [x for x in r if x["kind"] == "new-fakemon" and x["bucket"] == "needs_review" and x["name"].strip().lower() in {"mikitarian","luminian"}], "creator/region labels not served as species names")
    check(all(x.get("identityStatus") for x in r), "identity provenance class available")
    check(all(not any(s in p for s in ["../","\\"]) for x in r for p in (x.get("front",""),x.get("back",""))), "sprite paths do not traverse directories")
    check(all(not any(s in p for s in ["../","\\"]) for q in c for x in q["options"] for p in (x.get("front",""),x.get("back",""))), "artwork option paths do not traverse directories")
    check(all(all(x.get("front") and x.get("back") for x in q["options"]) for q in c if q["bucket"] == "needs_review"), "creative art comparisons have front/back pairs")
    check(sum(x["bucket"] == "identity_hold" for x in r) >= 19, "identity conflicts separated into hold queue")
    check(sum(x["bucket"] == "technical_hold" for x in r) >= 100, "technical repair queue retained")
    check(any(x["id"] == "gba:R0471" and x["decision"] == "keep" for x in r), "approved Elite Redux Roserade preserved")
    check(any(x["id"] == "gba:R0470" and x["decision"] == "cut" for x in r), "rejected original Mega Roserade preserved")
    for species_id in ("gba:R0477", "gba:R0479"):
        check(byid[species_id]["decision"] == "" and byid[species_id]["bucket"] == "technical_hold", species_id + " unreviewed, awaiting art source recovery")
    check("data-tab=\"identity\"" in page, "identity-provenance tab available on phone")
    check("data-confirmidentity" in page, "explicit identity confirmation required before creative choice")
    check('["linked_source_record","prior_source_verification"].includes(x.identityStatus)' in page, "bulk approve guarded by source evidence")
    check("function exportCSV" in page and "function importRows" in page and "function exportJSON" in page, "round-trip user export/import controls available")
    check("artist_credit" in page and "resolved_name" in page and "resolved_family" in page, "GitHub CSV includes credited creator and corrected identities")
    inline = re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>", page, re.DOTALL | re.IGNORECASE)
    check(len(inline) == 1, "one standalone reviewer script")
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "review.js"
        path.write_text(inline[0], encoding="utf-8")
        result = subprocess.run(["node", "--check", str(path)], capture_output=True, text=True)
        check(result.returncode == 0, "JavaScript syntax valid: " + result.stderr.strip())
    summary = Counter(x["bucket"] for x in r)
    summary["choice_needs_review"] = sum(x["bucket"] == "needs_review" for x in c)
    summary["choice_identity_hold"] = sum(x["bucket"] == "identity_hold" for x in c)
    summary["choice_technical_hold"] = sum(x["bucket"] == "technical_hold" for x in c)
    print("AUDIT:", json.dumps(dict(summary), sort_keys=True))
    print("All read-only identity / source-provenance tests passed.")


if __name__ == "__main__":
    main()
